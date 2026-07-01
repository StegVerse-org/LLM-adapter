"""Runtime adapter for governed LLM response handling.

The adapter does not call any LLM provider. It accepts a candidate response,
classifies the transition, builds a reconstruction packet, and returns a
receipt-ready result. Provider integrations can wrap this module without
changing the governance contract.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional, Sequence


try:
    from stegverse.governed_llm import (  # type: ignore[import]
        EvidencePointer,
        build_query_packet,
        build_response_receipt,
        reconstruction_summary,
    )
except ImportError:  # pragma: no cover - used before SDK contract release is installed
    SCHEMA_VERSION = "stegverse.governed_llm.v0.1"
    ACTION_PURPOSES = frozenset({"publish", "commit", "send", "execute", "mutate_memory"})

    def _stable_json(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def _stable_hash(value: Any) -> str:
        return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()

    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @dataclass(frozen=True)
    class EvidencePointer:  # type: ignore[no-redef]
        source_type: str
        pointer: str
        content_hash: str
        retrieved_at: str
        freshness: str = "current"
        authority_scope: str = "read"
        notes: str = ""

        def to_dict(self) -> dict[str, str]:
            return asdict(self)

    @dataclass(frozen=True)
    class _QueryPacket:
        query: str
        purpose: str
        transition_class: str
        risk_tier: str
        allowed_sources: tuple[str, ...]
        evidence: tuple[EvidencePointer, ...] = field(default_factory=tuple)
        policy_hash: str = "unresolved"
        delegation_hash: str = "unresolved"
        created_at: str = field(default_factory=_utc_now_iso)
        schema_version: str = SCHEMA_VERSION

        def to_dict(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "created_at": self.created_at,
                "query": self.query,
                "purpose": self.purpose,
                "transition_class": self.transition_class,
                "risk_tier": self.risk_tier,
                "allowed_sources": list(self.allowed_sources),
                "evidence": [item.to_dict() for item in self.evidence],
                "policy_hash": self.policy_hash,
                "delegation_hash": self.delegation_hash,
            }

        @property
        def packet_hash(self) -> str:
            return _stable_hash(self.to_dict())

    @dataclass(frozen=True)
    class _ResponseReceipt:
        query_packet_hash: str
        output_hash: str
        model_provider: str
        model_name: str
        decision: str
        admissibility_status: str
        reconstruction_status: str
        emitted_at: str = field(default_factory=_utc_now_iso)
        schema_version: str = SCHEMA_VERSION

        def to_dict(self) -> dict[str, str]:
            return asdict(self)

        @property
        def receipt_hash(self) -> str:
            return _stable_hash(self.to_dict())

    def _classify_purpose(query: str, requested_purpose: Optional[str]) -> str:
        if requested_purpose:
            return requested_purpose.lower().strip()
        lowered = query.lower()
        if any(word in lowered for word in ("commit", "publish", "send", "execute")):
            return "execute"
        if any(word in lowered for word in ("remember", "store", "memory")):
            return "mutate_memory"
        if any(word in lowered for word in ("summarize", "explain", "what", "how", "why")):
            return "answer"
        return "classify"

    def _classify_risk(purpose: str, allowed_sources: Sequence[str]) -> str:
        normalized_sources = {source.lower() for source in allowed_sources}
        if purpose in ACTION_PURPOSES:
            return "HIGH"
        if {"private_connector", "memory", "repo_write"} & normalized_sources:
            return "MEDIUM"
        if "external_publication" in normalized_sources:
            return "HIGH"
        return "LOW"

    def build_query_packet(  # type: ignore[no-redef]
        query: str,
        *,
        allowed_sources: Sequence[str] = ("model_knowledge",),
        purpose: Optional[str] = None,
        transition_class: str = "candidate_response",
        evidence: Sequence[EvidencePointer] = (),
        policy: Optional[Mapping[str, Any]] = None,
        delegation: Optional[Mapping[str, Any]] = None,
    ) -> _QueryPacket:
        resolved_purpose = _classify_purpose(query, purpose)
        source_tuple = tuple(allowed_sources)
        return _QueryPacket(
            query=query,
            purpose=resolved_purpose,
            transition_class=transition_class,
            risk_tier=_classify_risk(resolved_purpose, source_tuple),
            allowed_sources=source_tuple,
            evidence=tuple(evidence),
            policy_hash=_stable_hash(policy or {"policy": "unresolved"}),
            delegation_hash=_stable_hash(delegation or {"delegation": "unresolved"}),
        )

    def build_response_receipt(  # type: ignore[no-redef]
        query_packet: _QueryPacket,
        output: str,
        *,
        model_provider: str,
        model_name: str,
        decision: str,
        admissibility_status: str,
        reconstruction_status: str = "reconstructable",
    ) -> _ResponseReceipt:
        return _ResponseReceipt(
            query_packet_hash=query_packet.packet_hash,
            output_hash=_stable_hash({"output": output}),
            model_provider=model_provider,
            model_name=model_name,
            decision=decision.upper(),
            admissibility_status=admissibility_status,
            reconstruction_status=reconstruction_status,
        )

    def reconstruction_summary(  # type: ignore[no-redef]
        query_packet: _QueryPacket,
        receipt: _ResponseReceipt,
    ) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "query_packet_hash": query_packet.packet_hash,
            "response_receipt_hash": receipt.receipt_hash,
            "policy_hash": query_packet.policy_hash,
            "delegation_hash": query_packet.delegation_hash,
            "evidence_hashes": [item.content_hash for item in query_packet.evidence],
            "risk_tier": query_packet.risk_tier,
            "decision": receipt.decision,
            "admissibility_status": receipt.admissibility_status,
            "reconstruction_status": receipt.reconstruction_status,
        }


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

        packet = build_query_packet(
            query,
            allowed_sources=allowed_sources,
            purpose=purpose,
            transition_class=transition_class,
            evidence=evidence,
            policy=policy,
            delegation=delegation,
        )
        decision, status, reason = self._decide(packet, candidate_output)
        receipt = build_response_receipt(
            packet,
            candidate_output,
            model_provider=model_provider or self.default_provider,
            model_name=model_name or self.default_model,
            decision=decision.value,
            admissibility_status=status,
            reconstruction_status="reconstructable" if decision != AdapterDecision.DENY else "denied_reconstructable",
        )
        reconstruction = reconstruction_summary(packet, receipt)
        return GovernedAdapterResult(
            decision=decision.value,
            admissibility_status=status,
            query_packet=packet.to_dict(),
            response_receipt=receipt.to_dict(),
            reconstruction=reconstruction,
            reason=reason,
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
    "EvidencePointer",
    "GovernedAdapterResult",
    "GovernedLLMAdapter",
    "govern_response",
]
