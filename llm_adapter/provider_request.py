"""Provider-facing request normalization for governed LLM adapter.

This module keeps provider calls outside the governance core. It turns provider
and model metadata plus prompt content into a deterministic request envelope that
can be governed before any external call is made.

The optional :class:`AIIngressContext` is provider-independent. It records the
identity, capability, confinement, evidence, and correlation facts presented at
the adapter boundary without granting any authority. Existing requests that do
not attach ingress context retain their historical serialized shape and hash.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence


REQUEST_SCHEMA_VERSION = "stegverse.llm_adapter.provider_request.v0.1"
AI_INGRESS_CONTEXT_SCHEMA_VERSION = "stegverse.ai_ingress.context.v1"
UNKNOWN_IDENTITY = "UNKNOWN"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ProviderMessage:
    """Normalized chat-style message prepared for a model provider."""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class AIIngressContext:
    """Provider-independent facts presented at the StegVerse AI ingress seam.

    Nothing in this structure is an authorization token. Provider/model/session
    identifiers remain distinct from a StegVerse entity identity. An unresolved
    principal stays ``UNKNOWN`` until a canonical identity owner resolves it.

    Confinement fields describe requested/required bounds for the existing
    sandbox/confinement owner; this class does not implement a sandbox or mint
    permission to use a resource.
    """

    entity_id: str = UNKNOWN_IDENTITY
    provider_identity: str = UNKNOWN_IDENTITY
    model_identity: str = UNKNOWN_IDENTITY
    transport_id: str = UNKNOWN_IDENTITY
    adapter_identity: str = "llm-adapter"
    adapter_version: str = "UNKNOWN"
    session_id: str = UNKNOWN_IDENTITY
    conversation_id: str = UNKNOWN_IDENTITY
    transition_id: str = UNKNOWN_IDENTITY
    execution_id: str = UNKNOWN_IDENTITY
    claimed_capabilities: tuple[str, ...] = ()
    requested_capabilities: tuple[str, ...] = ()
    authority_declaration: str = "NONE"
    confinement_profile: str = "bounded-entity-sandbox"
    execution_budget: Mapping[str, Any] = field(default_factory=dict)
    resource_budget: Mapping[str, Any] = field(default_factory=dict)
    network_permissions: tuple[str, ...] = ()
    filesystem_permissions: tuple[str, ...] = ()
    tool_permissions: tuple[str, ...] = ()
    persistence_permissions: tuple[str, ...] = ()
    outbound_destinations: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    context_lineage: tuple[str, ...] = ()
    response_constraints: Mapping[str, Any] = field(default_factory=dict)
    evidence_requirements: tuple[str, ...] = ()
    failure_mode: str = "FAIL_CLOSED"
    correlation_identifiers: Mapping[str, str] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = AI_INGRESS_CONTEXT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "entity_id": self.entity_id,
            "provider_identity": self.provider_identity,
            "model_identity": self.model_identity,
            "transport_id": self.transport_id,
            "adapter_identity": self.adapter_identity,
            "adapter_version": self.adapter_version,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "transition_id": self.transition_id,
            "execution_id": self.execution_id,
            "claimed_capabilities": list(self.claimed_capabilities),
            "requested_capabilities": list(self.requested_capabilities),
            "authority_declaration": self.authority_declaration,
            "confinement_profile": self.confinement_profile,
            "execution_budget": dict(self.execution_budget),
            "resource_budget": dict(self.resource_budget),
            "network_permissions": list(self.network_permissions),
            "filesystem_permissions": list(self.filesystem_permissions),
            "tool_permissions": list(self.tool_permissions),
            "persistence_permissions": list(self.persistence_permissions),
            "outbound_destinations": list(self.outbound_destinations),
            "provenance": dict(self.provenance),
            "context_lineage": list(self.context_lineage),
            "response_constraints": dict(self.response_constraints),
            "evidence_requirements": list(self.evidence_requirements),
            "failure_mode": self.failure_mode,
            "correlation_identifiers": dict(self.correlation_identifiers),
            "extensions": dict(self.extensions),
        }


@dataclass(frozen=True)
class ProviderRequest:
    """Transport-neutral model request envelope.

    The request envelope is hashable and can be attached to a query packet
    without exposing provider credentials or executing a provider call.

    ``ingress_context`` is optional for backward compatibility. When absent it
    is not serialized, preserving the pre-v1 request representation and hash.
    """

    provider: str
    model: str
    messages: tuple[ProviderMessage, ...]
    purpose: str = "answer"
    allowed_sources: tuple[str, ...] = ("model_knowledge",)
    temperature: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    ingress_context: AIIngressContext | None = None
    created_at: str = field(default_factory=utc_now_iso)
    schema_version: str = REQUEST_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "provider": self.provider,
            "model": self.model,
            "messages": [message.to_dict() for message in self.messages],
            "purpose": self.purpose,
            "allowed_sources": list(self.allowed_sources),
            "temperature": self.temperature,
            "metadata": dict(self.metadata),
        }
        if self.ingress_context is not None:
            payload["ingress_context"] = self.ingress_context.to_dict()
        return payload

    @property
    def request_hash(self) -> str:
        return stable_hash(self.to_dict())

    @property
    def user_query(self) -> str:
        for message in reversed(self.messages):
            if message.role == "user":
                return message.content
        return "\n".join(message.content for message in self.messages)


def normalize_messages(messages: Sequence[Mapping[str, str] | ProviderMessage]) -> tuple[ProviderMessage, ...]:
    normalized = []
    for message in messages:
        if isinstance(message, ProviderMessage):
            normalized.append(message)
            continue
        role = str(message.get("role", "user")).strip() or "user"
        content = str(message.get("content", ""))
        normalized.append(ProviderMessage(role=role, content=content))
    return tuple(normalized)


def build_provider_request(
    *,
    provider: str,
    model: str,
    messages: Sequence[Mapping[str, str] | ProviderMessage],
    purpose: str = "answer",
    allowed_sources: Sequence[str] = ("model_knowledge",),
    temperature: float = 0.0,
    metadata: Optional[Mapping[str, Any]] = None,
    ingress_context: AIIngressContext | None = None,
) -> ProviderRequest:
    """Create a normalized provider request envelope."""

    return ProviderRequest(
        provider=provider,
        model=model,
        messages=normalize_messages(messages),
        purpose=purpose,
        allowed_sources=tuple(allowed_sources),
        temperature=temperature,
        metadata=metadata or {},
        ingress_context=ingress_context,
    )


__all__ = [
    "REQUEST_SCHEMA_VERSION",
    "AI_INGRESS_CONTEXT_SCHEMA_VERSION",
    "UNKNOWN_IDENTITY",
    "ProviderMessage",
    "AIIngressContext",
    "ProviderRequest",
    "build_provider_request",
    "normalize_messages",
    "stable_hash",
    "stable_json",
]
