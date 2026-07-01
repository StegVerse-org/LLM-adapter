"""One-call governed session runner.

A governed session joins provider request normalization, continuity search,
candidate response handling, and adapter receipt generation into one deterministic
runtime surface. It still does not call live model providers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, Sequence

from .continuity_search import FixtureContinuitySearch
from .governed_adapter import GovernedLLMAdapter
from .provider_request import ProviderRequest, build_provider_request


SESSION_SCHEMA_VERSION = "stegverse.llm_adapter.governed_session.v0.1"


@dataclass(frozen=True)
class GovernedSessionResult:
    """Complete output of one governed adapter session."""

    provider_request: dict[str, Any]
    provider_request_hash: str
    continuity: dict[str, Any]
    adapter_result: dict[str, Any]
    schema_version: str = SESSION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_governed_session(
    *,
    provider: str,
    model: str,
    messages: Sequence[Mapping[str, str]],
    candidate_output: str,
    evidence_fixtures: Sequence[Mapping[str, Any]] = (),
    purpose: str = "answer",
    allowed_sources: Sequence[str] = ("model_knowledge",),
    policy: Optional[Mapping[str, Any]] = None,
    delegation: Optional[Mapping[str, Any]] = None,
    temperature: float = 0.0,
    metadata: Optional[Mapping[str, Any]] = None,
) -> GovernedSessionResult:
    """Run a complete governed response session without a live provider call."""

    request = build_provider_request(
        provider=provider,
        model=model,
        messages=messages,
        purpose=purpose,
        allowed_sources=allowed_sources,
        temperature=temperature,
        metadata=metadata or {},
    )
    return run_governed_request_session(
        request=request,
        candidate_output=candidate_output,
        evidence_fixtures=evidence_fixtures,
        policy=policy,
        delegation=delegation,
    )


def run_governed_request_session(
    *,
    request: ProviderRequest,
    candidate_output: str,
    evidence_fixtures: Sequence[Mapping[str, Any]] = (),
    policy: Optional[Mapping[str, Any]] = None,
    delegation: Optional[Mapping[str, Any]] = None,
) -> GovernedSessionResult:
    """Run a complete governed response session from a normalized request."""

    continuity = FixtureContinuitySearch(evidence_fixtures).search(request.user_query)
    adapter = GovernedLLMAdapter(default_provider=request.provider, default_model=request.model)
    adapter_result = adapter.govern_response(
        query=request.user_query,
        candidate_output=candidate_output,
        allowed_sources=request.allowed_sources,
        evidence=continuity.evidence,
        purpose=request.purpose,
        policy=policy or {},
        delegation=delegation or {},
        model_provider=request.provider,
        model_name=request.model,
    )
    return GovernedSessionResult(
        provider_request=request.to_dict(),
        provider_request_hash=request.request_hash,
        continuity=continuity.to_dict(),
        adapter_result=adapter_result.to_dict(),
    )


__all__ = [
    "SESSION_SCHEMA_VERSION",
    "GovernedSessionResult",
    "run_governed_request_session",
    "run_governed_session",
]
