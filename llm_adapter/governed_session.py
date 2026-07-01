"""One-call governed session runner.

A governed session joins provider request normalization, continuity search,
provider output handling, adapter receipt generation, and commit-time action
routing into one deterministic runtime surface. Live provider clients can be
injected later while preserving the same governance boundary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, Sequence

from .action_router import build_action_route_packet
from .continuity_search import FixtureContinuitySearch
from .governed_adapter import GovernedLLMAdapter
from .provider_client import FixtureProviderClient, ProviderClient, ProviderResponse
from .provider_request import ProviderRequest, build_provider_request


SESSION_SCHEMA_VERSION = "stegverse.llm_adapter.governed_session.v0.1"


@dataclass(frozen=True)
class GovernedSessionResult:
    """Complete output of one governed adapter session."""

    provider_request: dict[str, Any]
    provider_request_hash: str
    provider_response: dict[str, Any]
    continuity: dict[str, Any]
    adapter_result: dict[str, Any]
    action_route: dict[str, Any]
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
    action_target: str = "unresolved",
) -> GovernedSessionResult:
    """Run a complete governed response session with fixture provider output."""

    request = build_provider_request(
        provider=provider,
        model=model,
        messages=messages,
        purpose=purpose,
        allowed_sources=allowed_sources,
        temperature=temperature,
        metadata=metadata or {},
    )
    provider_client = FixtureProviderClient(output=candidate_output)
    return run_governed_request_session(
        request=request,
        provider_client=provider_client,
        evidence_fixtures=evidence_fixtures,
        policy=policy,
        delegation=delegation,
        action_target=action_target,
    )


def run_governed_request_session(
    *,
    request: ProviderRequest,
    provider_client: ProviderClient,
    evidence_fixtures: Sequence[Mapping[str, Any]] = (),
    policy: Optional[Mapping[str, Any]] = None,
    delegation: Optional[Mapping[str, Any]] = None,
    action_target: str = "unresolved",
) -> GovernedSessionResult:
    """Run a complete governed response session from a normalized request."""

    provider_response = provider_client.complete(request)
    return run_governed_response_session(
        request=request,
        provider_response=provider_response,
        evidence_fixtures=evidence_fixtures,
        policy=policy,
        delegation=delegation,
        action_target=action_target,
    )


def run_governed_response_session(
    *,
    request: ProviderRequest,
    provider_response: ProviderResponse,
    evidence_fixtures: Sequence[Mapping[str, Any]] = (),
    policy: Optional[Mapping[str, Any]] = None,
    delegation: Optional[Mapping[str, Any]] = None,
    action_target: str = "unresolved",
) -> GovernedSessionResult:
    """Govern an already-created provider response envelope."""

    if provider_response.request_hash != request.request_hash:
        raise ValueError("provider response request_hash does not match provider request")

    continuity = FixtureContinuitySearch(evidence_fixtures).search(request.user_query)
    adapter = GovernedLLMAdapter(default_provider=request.provider, default_model=request.model)
    adapter_result = adapter.govern_response(
        query=request.user_query,
        candidate_output=provider_response.output,
        allowed_sources=request.allowed_sources,
        evidence=continuity.evidence,
        purpose=request.purpose,
        policy=policy or {},
        delegation=delegation or {},
        model_provider=request.provider,
        model_name=request.model,
    )
    action_route = build_action_route_packet(
        query=request.user_query,
        output=provider_response.output,
        adapter_result=adapter_result.to_dict(),
        purpose=request.purpose,
        target=action_target,
    )
    return GovernedSessionResult(
        provider_request=request.to_dict(),
        provider_request_hash=request.request_hash,
        provider_response=provider_response.to_dict(),
        continuity=continuity.to_dict(),
        adapter_result=adapter_result.to_dict(),
        action_route=action_route.to_dict(),
    )


__all__ = [
    "SESSION_SCHEMA_VERSION",
    "GovernedSessionResult",
    "run_governed_request_session",
    "run_governed_response_session",
    "run_governed_session",
]
