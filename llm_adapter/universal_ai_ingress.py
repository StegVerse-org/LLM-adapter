"""Canonical provider-independent AI ingress contract.

This module extends ProviderRequest/ProviderResponse semantics without creating a
new governance, credential, worker, custody, heartbeat, or runtime authority.
Provider-specific transports remain thin edge implementations behind the shared
registry. Unsupported execution paths fail closed instead of manufacturing a
new provider owner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .external_llm_connection import (
    GovernedConnectionResult,
    admit_external_llm_egress,
    execute_governed_external_llm,
)
from .provider_request import ProviderRequest, stable_hash


AI_INGRESS_SCHEMA_VERSION = "stegverse.llm_adapter.ai_ingress.v1"
AI_ADAPTER_REGISTRY_SCHEMA_VERSION = "stegverse.llm_adapter.ai_adapter_registry.v1"


class AIIngressError(RuntimeError):
    """Base failure for canonical AI ingress validation or routing."""


class UnsupportedAIIngressRoute(AIIngressError):
    """The ingress identity is known, but no execution adapter is admitted here."""


@dataclass(frozen=True)
class AIIngressCapabilities:
    """Provider-independent capability vocabulary.

    These values describe capability only. They grant no route or execution
    authority and must not be interpreted as proof of live availability.
    """

    interaction_modes: tuple[str, ...] = ("chat",)
    execution_classes: tuple[str, ...] = ("hosted_api",)
    network_required: bool = True
    credential_requirement: str = "TV_TVC"
    supports_streaming: bool = False
    supports_tools: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "interaction_modes": list(self.interaction_modes),
            "execution_classes": list(self.execution_classes),
            "network_required": self.network_required,
            "credential_requirement": self.credential_requirement,
            "supports_streaming": self.supports_streaming,
            "supports_tools": self.supports_tools,
        }


@dataclass(frozen=True)
class AIIngressConfinement:
    """Non-authoritative ingress confinement declaration."""

    allowed_purposes: tuple[str, ...] = ("answer",)
    allowed_sources: tuple[str, ...] = ("model_knowledge",)
    max_temperature: float = 1.0
    authority_effect: str = "NONE"
    transition_authority: str = "Interlock/InTr"
    credential_authority: str = "TV/TVC"
    custody_authority: str = "master-records/orchestration"

    def validate(self, request: ProviderRequest) -> None:
        if request.purpose not in self.allowed_purposes:
            raise AIIngressError(f"purpose not admitted by ingress confinement: {request.purpose}")
        disallowed = sorted(set(request.allowed_sources) - set(self.allowed_sources))
        if disallowed:
            raise AIIngressError(
                "source not admitted by ingress confinement: " + ",".join(disallowed)
            )
        if request.temperature > self.max_temperature:
            raise AIIngressError(
                f"temperature exceeds ingress confinement: {request.temperature}>{self.max_temperature}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_purposes": list(self.allowed_purposes),
            "allowed_sources": list(self.allowed_sources),
            "max_temperature": self.max_temperature,
            "authority_effect": self.authority_effect,
            "transition_authority": self.transition_authority,
            "credential_authority": self.credential_authority,
            "custody_authority": self.custody_authority,
        }


@dataclass(frozen=True)
class AIAdapterContract:
    """Declarative registry entry for one AI ingress identity family."""

    adapter_id: str
    canonical_provider: str
    aliases: tuple[str, ...]
    transport_family: str
    execution_owner: str
    capabilities: AIIngressCapabilities
    external_connection_dispatch: bool
    evidence_class: str = "provider_response"
    authority_effect: str = "NONE"

    def matches(self, provider: str) -> bool:
        candidate = provider.lower().strip()
        return candidate == self.canonical_provider or candidate in self.aliases

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "canonical_provider": self.canonical_provider,
            "aliases": list(self.aliases),
            "transport_family": self.transport_family,
            "execution_owner": self.execution_owner,
            "capabilities": self.capabilities.to_dict(),
            "external_connection_dispatch": self.external_connection_dispatch,
            "evidence_class": self.evidence_class,
            "authority_effect": self.authority_effect,
        }


HOSTED_API = AIIngressCapabilities(
    interaction_modes=("chat",),
    execution_classes=("hosted_api",),
    network_required=True,
    credential_requirement="TV_TVC",
)

LOCAL_RESIDENT = AIIngressCapabilities(
    interaction_modes=("chat",),
    execution_classes=("local", "resident"),
    network_required=False,
    credential_requirement="NONE_OR_TV_TVC_ROUTE_DEPENDENT",
)

BROWSER_SESSION = AIIngressCapabilities(
    interaction_modes=("chat", "browser_session"),
    execution_classes=("browser_mediated",),
    network_required=True,
    credential_requirement="SESSION_BOUNDARY_DEPENDENT",
)

OPENAI_COMPATIBLE = AIIngressCapabilities(
    interaction_modes=("chat",),
    execution_classes=("hosted_api", "openai_compatible"),
    network_required=True,
    credential_requirement="TV_TVC",
)


AI_ADAPTER_REGISTRY: tuple[AIAdapterContract, ...] = (
    AIAdapterContract("ai-adapter:zai", "zai", ("z.ai", "z_ai"), "provider_http", "llm_adapter.external_llm_connection", HOSTED_API, True),
    AIAdapterContract("ai-adapter:deepseek", "deepseek", ("deepseek_http",), "provider_http", "llm_adapter.external_llm_connection", HOSTED_API, True),
    AIAdapterContract("ai-adapter:kimi", "kimi", ("moonshot", "kimi_http"), "provider_http", "llm_adapter.external_llm_connection", HOSTED_API, True),
    AIAdapterContract("ai-adapter:anthropic", "anthropic", ("claude", "anthropic_http"), "provider_http", "llm_adapter.external_llm_connection", HOSTED_API, True),
    AIAdapterContract("ai-adapter:openai", "openai", ("chatgpt_api",), "provider_http", "provider_edge:openai", HOSTED_API, False),
    AIAdapterContract("ai-adapter:openai-compatible", "openai_compatible", ("openai-compatible", "oai_compatible"), "provider_http_compatible", "provider_edge:openai_compatible", OPENAI_COMPATIBLE, False),
    AIAdapterContract("ai-adapter:sovereign-local", "sovereign_local", ("local", "resident", "sovereign"), "resident_local", "StegVerse-002/micro-node-runtime", LOCAL_RESIDENT, False, evidence_class="resident_execution_receipt"),
    AIAdapterContract("ai-adapter:browser-session", "browser_session", ("browser", "session_mediated"), "browser_session", "bounded_entity_session_path", BROWSER_SESSION, False, evidence_class="bounded_session_receipt"),
)


@dataclass(frozen=True)
class AIIngressEnvelope:
    """Canonical ingress envelope layered on the existing ProviderRequest."""

    request: ProviderRequest
    session_id: str
    transition_id: str
    measurement_id: str
    ingress_disposition: str
    ingress_receipt_hash: str
    carrier_ref: str
    entity_id: str | None = None
    confinement: AIIngressConfinement = field(default_factory=AIIngressConfinement)
    schema_version: str = AI_INGRESS_SCHEMA_VERSION

    def validate(self) -> AIAdapterContract:
        if self.ingress_disposition != "ALLOW":
            raise AIIngressError("canonical AI ingress requires an admitted Interlock/InTr ingress")
        if not self.session_id or not self.transition_id or not self.measurement_id:
            raise AIIngressError("session_id, transition_id, and measurement_id are required")
        if len(self.ingress_receipt_hash) != 64:
            raise AIIngressError("ingress_receipt_hash must be a 64-character hash")
        if not self.carrier_ref:
            raise AIIngressError("carrier_ref is required")
        self.confinement.validate(self.request)
        return resolve_ai_adapter(self.request.provider)

    @property
    def ingress_hash(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request": self.request.to_dict(),
            "session_id": self.session_id,
            "transition_id": self.transition_id,
            "measurement_id": self.measurement_id,
            "ingress_disposition": self.ingress_disposition,
            "ingress_receipt_hash": self.ingress_receipt_hash,
            "carrier_ref": self.carrier_ref,
            "entity_id": self.entity_id,
            "confinement": self.confinement.to_dict(),
            "authority_effect": "NONE",
        }


@dataclass(frozen=True)
class AIRouteDirective:
    """Fail-closed provider-independent routing result.

    A directive identifies the existing owner of an execution path. It is not an
    execution receipt and cannot be promoted to CONNECTED or ACTIVE evidence.
    """

    adapter: AIAdapterContract
    ingress_hash: str
    request_hash: str
    execution_supported_here: bool
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.llm_adapter.ai_route_directive.v1",
            "adapter": self.adapter.to_dict(),
            "ingress_hash": self.ingress_hash,
            "request_hash": self.request_hash,
            "execution_supported_here": self.execution_supported_here,
            "authority_effect": self.authority_effect,
            "connected": False,
            "runtime_proof": False,
        }


def resolve_ai_adapter(provider: str) -> AIAdapterContract:
    matches = [adapter for adapter in AI_ADAPTER_REGISTRY if adapter.matches(provider)]
    if len(matches) != 1:
        if not matches:
            raise UnsupportedAIIngressRoute(f"unregistered AI ingress provider: {provider}")
        raise AIIngressError(f"duplicate AI ingress adapter ownership for provider: {provider}")
    return matches[0]


def audit_ai_adapter_registry(registry: Sequence[AIAdapterContract] = AI_ADAPTER_REGISTRY) -> dict[str, Any]:
    """Detect alias/canonical collisions and authority duplication."""

    owners: dict[str, str] = {}
    duplicates: dict[str, list[str]] = {}
    forbidden_authority = []
    for adapter in registry:
        for name in (adapter.canonical_provider, *adapter.aliases):
            key = name.lower().strip()
            if key in owners and owners[key] != adapter.adapter_id:
                duplicates.setdefault(key, [owners[key]]).append(adapter.adapter_id)
            else:
                owners[key] = adapter.adapter_id
        if adapter.authority_effect != "NONE":
            forbidden_authority.append(adapter.adapter_id)
    return {
        "schema": AI_ADAPTER_REGISTRY_SCHEMA_VERSION,
        "adapter_count": len(registry),
        "duplicates": duplicates,
        "forbidden_authority_effect": forbidden_authority,
        "pass": not duplicates and not forbidden_authority,
    }


def route_ai_ingress(envelope: AIIngressEnvelope) -> AIRouteDirective:
    adapter = envelope.validate()
    return AIRouteDirective(
        adapter=adapter,
        ingress_hash=envelope.ingress_hash,
        request_hash=envelope.request.request_hash,
        execution_supported_here=adapter.external_connection_dispatch,
    )


def execute_ai_ingress(
    envelope: AIIngressEnvelope,
    *,
    credential_resolver=None,
    lease_receipt: Mapping[str, Any] | None = None,
    broker_submitter=None,
    **provider_options: Any,
) -> GovernedConnectionResult:
    """Execute only adapters already owned by external_llm_connection.

    Local/resident/browser/OpenAI-family registry entries intentionally return a
    routing failure until their existing owner exposes an admitted executable
    seam. This prevents architecture registration from becoming authority.
    """

    adapter = envelope.validate()
    if not adapter.external_connection_dispatch:
        raise UnsupportedAIIngressRoute(
            f"AI ingress adapter {adapter.adapter_id} is registered to {adapter.execution_owner} "
            "and is not executable through llm_adapter.external_llm_connection"
        )
    return execute_governed_external_llm(
        envelope.request,
        session_id=envelope.session_id,
        transition_id=envelope.transition_id,
        measurement_id=envelope.measurement_id,
        ingress_disposition=envelope.ingress_disposition,
        ingress_receipt_hash=envelope.ingress_receipt_hash,
        carrier_ref=envelope.carrier_ref,
        credential_resolver=credential_resolver,
        lease_receipt=lease_receipt,
        broker_submitter=broker_submitter,
        **provider_options,
    )


def admit_ai_egress(
    result: GovernedConnectionResult,
    *,
    egress_disposition: str,
    egress_receipt_hash: str,
    admitted_response_hash: str,
) -> Any:
    """Reuse the existing provider-independent governed egress seam."""

    return admit_external_llm_egress(
        result,
        egress_disposition=egress_disposition,
        egress_receipt_hash=egress_receipt_hash,
        admitted_response_hash=admitted_response_hash,
    )


__all__ = [
    "AI_INGRESS_SCHEMA_VERSION",
    "AI_ADAPTER_REGISTRY_SCHEMA_VERSION",
    "AIIngressError",
    "UnsupportedAIIngressRoute",
    "AIIngressCapabilities",
    "AIIngressConfinement",
    "AIAdapterContract",
    "AI_ADAPTER_REGISTRY",
    "AIIngressEnvelope",
    "AIRouteDirective",
    "resolve_ai_adapter",
    "audit_ai_adapter_registry",
    "route_ai_ingress",
    "execute_ai_ingress",
    "admit_ai_egress",
]
