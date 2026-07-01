"""Runtime adapter for governed LLM response handling.

The adapter does not call any LLM provider. It accepts a candidate response,
classifies the transition, builds a reconstruction packet, and returns a
receipt-ready result. Provider integrations can wrap this module without
changing the governance contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

try:
    from stegverse.governed_llm import (
        EvidencePointer,
        build_query_packet,
        build_response_receipt,
        reconstruction_summary,
    )
except ImportError:  # pragma: no cover - fallback for isolated repo tests
    EvidencePointer = None  # type: ignore[assignment]
    build_query_packet = None  # type: ignore[assignment]
    build_response_receipt = None  # type: ignore[assignment]
    reconstruction_summary = None  # type: ignore[assignment]


class AdapterDecision(str, Enum):
    """Adapter-level decision before downstream execution authority."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"


@dataclass(frozen=True)
class GovernedAdapterResult:
    """Complete runtime result returned by the governed adapter."""

    decision: str
    admissibility_status: str
    query_packet: dict[str, Any]
    response_receipt: dict[str, Any]
    reconstruction: dict[str, Any]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GovernedLLMAdapter:
    """Govern LLM candidate responses without treating the LLM as authority."""

    def __init__(
        self,
        *,
        default_provider: str = "unresolved-provider",
        default_model: str = "unresolved-model",
    ) -> None:
        self.default_provider = default_provider
        self.default_model = default_model

    def govern_response(
        self,
        *,
        query: str,
        candidate_output: str,
        allowed_sources: Sequence[str] = ("model_knowledge",),
        evidence: Sequence[Any] = (),
        purpose: Optional[str] = None,
        transition_class: str = "candidate_response",
        policy: Optional[Mapping[str, Any]] = None,
        delegation: Optional[Mapping[str, Any]] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> GovernedAdapterResult:
        """Return a receipt-ready governance result for a candidate response."""

        self._ensure_sdk_contracts_available()
        packet = build_query_packet(  # type: ignore[misc]
            query,
            allowed_sources=allowed_sources,
            purpose=purpose,
            transition_class=transition_class,
            evidence=evidence,
            policy=policy,
            delegation=delegation,
        )
        decision, status, reason = self._decide(packet, candidate_output)
        receipt = build_response_receipt(  # type: ignore[misc]
            packet,
            candidate_output,
            model_provider=model_provider or self.default_provider,
            model_name=model_name or self.default_model,
            decision=decision.value,
            admissibility_status=status,
            reconstruction_status="reconstructable" if decision != AdapterDecision.DENY else "denied_reconstructable",
        )
        reconstruction = reconstruction_summary(packet, receipt)  # type: ignore[misc]
        return GovernedAdapterResult(
            decision=decision.value,
            admissibility_status=status,
            query_packet=packet.to_dict(),
            response_receipt=receipt.to_dict(),
            reconstruction=reconstruction,
            reason=reason,
        )

    def _ensure_sdk_contracts_available(self) -> None:
        if build_query_packet is None or build_response_receipt is None or reconstruction_summary is None:
            raise RuntimeError(
                "stegverse.governed_llm is required. Install stegverse-sdk or run within the SDK workspace."
            )

    def _decide(self, packet: Any, candidate_output: str) -> tuple[AdapterDecision, str, str]:
        if not candidate_output.strip():
            return AdapterDecision.DENY, "empty_output_denied", "No output can be admitted without content."

        if packet.risk_tier in {"HIGH", "CRITICAL"}:
            return (
                AdapterDecision.QUARANTINE,
                "requires_commit_time_authority",
                "High-consequence output requires downstream commit-time standing before consequence attaches.",
            )

        if any(item.freshness in {"stale", "revoked", "superseded"} for item in packet.evidence):
            return (
                AdapterDecision.QUARANTINE,
                "requires_fresh_retrieval",
                "At least one evidence pointer is not current; reconstructable history is not current authority.",
            )

        return (
            AdapterDecision.ALLOW,
            "allowed_read_only_candidate",
            "Candidate response is allowed as read-only output with reconstruction receipt.",
        )


def govern_response(**kwargs: Any) -> dict[str, Any]:
    """Convenience wrapper returning a plain dictionary."""

    adapter = GovernedLLMAdapter()
    return adapter.govern_response(**kwargs).to_dict()


__all__ = [
    "AdapterDecision",
    "GovernedAdapterResult",
    "GovernedLLMAdapter",
    "govern_response",
]
