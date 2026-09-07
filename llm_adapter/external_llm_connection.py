"""Provider-neutral governed external-LLM connection primitive.

No governance, runtime, credential, worker, heartbeat, route, sandbox, identity,
or custody authority is created here. This module selects existing provider
adapters behind one common Interlock/InTr -> TV/TVC -> provider -> Master
Records -> InTr sequence.

Provider differences are declared through one adapter registry. Registry entries
describe compatibility only; discovery never grants admission or capability.
The registry also records non-external execution owners and blocked providers so
unsupported paths fail closed instead of growing parallel orchestration.
"""
from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Any, Callable, Mapping

from .provider_request import ProviderRequest
from .zai_intr_executor import execute_governed_zai, admit_zai_egress
from .deepseek_intr_executor import execute_governed_deepseek, admit_deepseek_egress
from .kimi_intr_executor import execute_governed_kimi, admit_kimi_egress
from .zai_tvc_runtime_executor import execute_governed_zai_via_tvc_runtime, admit_zai_tvc_runtime_egress
from .deepseek_tvc_runtime_executor import execute_governed_deepseek_via_tvc_runtime, admit_deepseek_tvc_runtime_egress
from .kimi_tvc_runtime_executor import execute_governed_kimi_via_tvc_runtime, admit_kimi_tvc_runtime_egress
from .anthropic_tvc_runtime_executor import execute_governed_anthropic_via_tvc_runtime, admit_anthropic_tvc_runtime_egress


class ExternalLLMConnectionError(RuntimeError):
    pass


SEMANTIC_CAPABILITIES = (
    "conversational_inference",
    "structured_inference",
    "retrieval",
    "tool_invocation",
    "sandboxed_code_execution",
    "multimodal_input",
    "multimodal_output",
    "artifact_generation",
    "local_model_inference",
    "agent_delegation",
    "governed_persistence",
    "repository_read",
    "repository_mutation",
    "workflow_dispatch",
    "evaluation",
    "simulation",
    "transport",
)

FAILURE_CLASSES = (
    "PROVIDER_UNAVAILABLE",
    "INVALID_CREDENTIAL",
    "MISSING_CREDENTIAL",
    "ROUTE_UNAVAILABLE",
    "SANDBOX_UNAVAILABLE",
    "MODEL_UNAVAILABLE",
    "RUNTIME_INACTIVE",
    "RUNTIME_UNOBSERVED",
    "DISPATCH_MISSING",
    "RATE_LIMITED",
    "TIMEOUT",
    "MALFORMED_RESPONSE",
    "UNSUPPORTED_CAPABILITY",
    "INTR_DENY",
    "CONFINEMENT_VIOLATION",
    "IDENTITY_UNRESOLVED",
    "EVIDENCE_INCOMPLETE",
    "TRANSPORT_FAILURE",
)


@dataclass(frozen=True)
class ProviderAdapterDescriptor:
    """Declarative provider-edge compatibility descriptor.

    The descriptor is not an authority object. It cannot admit a transition,
    mint credentials, establish identity, grant sandbox permission, or claim
    runtime availability.
    """

    provider: str
    aliases: tuple[str, ...]
    adapter: str
    adapter_version: str
    transport_type: str
    credential_requirement: str
    semantic_capabilities: tuple[str, ...]
    tvc_executor: str | None
    tvc_egress: str | None
    direct_executor: str | None = None
    direct_egress: str | None = None
    direct_compatibility_allowed: bool = False
    confinement_compatible: bool = True
    authority_effect: str = "NONE"
    status: str = "IMPLEMENTED_UNVALIDATED"
    execution_owner: str = "EXTERNAL_TVC_CONNECTION"
    blocker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "aliases": list(self.aliases),
            "adapter": self.adapter,
            "adapter_version": self.adapter_version,
            "transport_type": self.transport_type,
            "credential_requirement": self.credential_requirement,
            "semantic_capabilities": list(self.semantic_capabilities),
            "tvc_executor": self.tvc_executor,
            "tvc_egress": self.tvc_egress,
            "direct_executor": self.direct_executor,
            "direct_egress": self.direct_egress,
            "direct_compatibility_allowed": self.direct_compatibility_allowed,
            "confinement_compatible": self.confinement_compatible,
            "authority_effect": self.authority_effect,
            "status": self.status,
            "execution_owner": self.execution_owner,
            "blocker": self.blocker,
        }


_ADAPTER_REGISTRY: dict[str, ProviderAdapterDescriptor] = {
    "zai": ProviderAdapterDescriptor(
        provider="zai",
        aliases=("z.ai", "zai", "z_ai"),
        adapter="zai_intr_transport",
        adapter_version="stegverse.intr.zai.transport.v1",
        transport_type="openai_compatible_http",
        credential_requirement="TV_TVC_NON_EXPORTABLE",
        semantic_capabilities=("conversational_inference", "structured_inference", "transport"),
        tvc_executor="execute_governed_zai_via_tvc_runtime",
        tvc_egress="admit_zai_tvc_runtime_egress",
        direct_executor="execute_governed_zai",
        direct_egress="admit_zai_egress",
        direct_compatibility_allowed=True,
    ),
    "deepseek": ProviderAdapterDescriptor(
        provider="deepseek",
        aliases=("deepseek", "deepseek_http"),
        adapter="deepseek_intr_transport",
        adapter_version="stegverse.intr.deepseek.transport.v1",
        transport_type="openai_compatible_http",
        credential_requirement="TV_TVC_NON_EXPORTABLE",
        semantic_capabilities=("conversational_inference", "structured_inference", "transport"),
        tvc_executor="execute_governed_deepseek_via_tvc_runtime",
        tvc_egress="admit_deepseek_tvc_runtime_egress",
        direct_executor="execute_governed_deepseek",
        direct_egress="admit_deepseek_egress",
        direct_compatibility_allowed=True,
    ),
    "kimi": ProviderAdapterDescriptor(
        provider="kimi",
        aliases=("kimi", "moonshot", "kimi_http"),
        adapter="kimi_intr_transport",
        adapter_version="stegverse.intr.kimi.transport.v1",
        transport_type="openai_compatible_http",
        credential_requirement="TV_TVC_NON_EXPORTABLE",
        semantic_capabilities=("conversational_inference", "structured_inference", "transport"),
        tvc_executor="execute_governed_kimi_via_tvc_runtime",
        tvc_egress="admit_kimi_tvc_runtime_egress",
        direct_executor="execute_governed_kimi",
        direct_egress="admit_kimi_egress",
        direct_compatibility_allowed=True,
    ),
    "anthropic": ProviderAdapterDescriptor(
        provider="anthropic",
        aliases=("anthropic", "claude", "anthropic_http"),
        adapter="anthropic_intr_transport",
        adapter_version="stegverse.intr.anthropic.transport.v1",
        transport_type="anthropic_http",
        credential_requirement="TV_TVC_NON_EXPORTABLE",
        semantic_capabilities=("conversational_inference", "structured_inference", "transport"),
        tvc_executor="execute_governed_anthropic_via_tvc_runtime",
        tvc_egress="admit_anthropic_tvc_runtime_egress",
        direct_compatibility_allowed=False,
    ),
    "openai": ProviderAdapterDescriptor(
        provider="openai",
        aliases=("openai", "chatgpt", "openai_http"),
        adapter="OpenAIHTTPProviderClient",
        adapter_version="legacy-direct-key-test-shim",
        transport_type="openai_http",
        credential_requirement="TV_TVC_NON_EXPORTABLE",
        semantic_capabilities=("conversational_inference", "structured_inference", "transport"),
        tvc_executor=None,
        tvc_egress=None,
        direct_compatibility_allowed=False,
        status="BLOCKED",
        execution_owner="TVC_PROVIDER_OPERATION_REQUIRED",
        blocker="canonical OpenAI TVC non-exportable provider-operation route not yet reconciled",
    ),
    "stegverse-local": ProviderAdapterDescriptor(
        provider="stegverse-local",
        aliases=("stegverse", "stegverse-local", "stegverse_local", "local-sovereign"),
        adapter="StegVerseLocalHTTPProviderClient",
        adapter_version="existing-provider-client",
        transport_type="local_openai_compatible_http",
        credential_requirement="NONE",
        semantic_capabilities=("conversational_inference", "local_model_inference", "transport"),
        tvc_executor=None,
        tvc_egress=None,
        direct_compatibility_allowed=False,
        status="IMPLEMENTED_UNVALIDATED",
        execution_owner="CANONICAL_SOVEREIGN_PROVIDER_CLIENT",
    ),
}

_ALIAS_INDEX = {
    alias: provider
    for provider, descriptor in _ADAPTER_REGISTRY.items()
    for alias in descriptor.aliases
}


@dataclass(frozen=True)
class GovernedConnectionResult:
    provider: str
    execution: Any
    execution_path: str
    authority_effect: str = "NONE"
    egress_intr_required: bool = True

    @property
    def response_hash(self) -> str:
        return str(self.execution.response_hash)

    @property
    def egress_handoff(self) -> Any:
        return self.execution.egress_handoff

    @property
    def response(self) -> Any:
        transport = getattr(self.execution, "transport", None)
        if transport is not None and getattr(transport, "response", None) is not None:
            return transport.response
        broker = getattr(self.execution, "broker", None)
        if broker is not None and getattr(broker, "response", None) is not None:
            return broker.response
        raise ExternalLLMConnectionError("governed execution has no provider response")

    def evidence(self) -> dict[str, Any]:
        execution_evidence = self.execution.evidence() if hasattr(self.execution, "evidence") else {
            "transition_id": self.execution.envelope.transition_id,
            "response_hash": self.response_hash,
            "runtime_profile_id": getattr(self.execution, "runtime_profile_id", None),
            "authority_effect": getattr(self.execution, "authority_effect", "NONE"),
        }
        return {
            "schema": "stegverse.llm_adapter.external_llm_connection/v1",
            "provider": self.provider,
            "execution_path": self.execution_path,
            "response_hash": self.response_hash,
            "execution": execution_evidence,
            "egress_intr_required": True,
            "authority_effect": "NONE",
        }


def adapter_registry() -> Mapping[str, ProviderAdapterDescriptor]:
    """Return the single provider adapter compatibility registry."""

    return dict(_ADAPTER_REGISTRY)


def normalize_provider(provider: str) -> str:
    normalized = _ALIAS_INDEX.get(provider.lower().strip())
    if not normalized:
        raise ExternalLLMConnectionError(f"unsupported external LLM provider: {provider}")
    return normalized


def adapter_descriptor(provider: str) -> ProviderAdapterDescriptor:
    return _ADAPTER_REGISTRY[normalize_provider(provider)]


def _resolve_callable(name: str | None) -> Callable[..., Any]:
    if not name:
        raise ExternalLLMConnectionError("provider adapter path is not implemented")
    value = getattr(sys.modules[__name__], name, None)
    if not callable(value):
        raise ExternalLLMConnectionError(f"provider adapter callable unavailable: {name}")
    return value


def execute_governed_external_llm(
    request: ProviderRequest,
    *,
    session_id: str,
    transition_id: str,
    measurement_id: str,
    ingress_disposition: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    credential_resolver: Callable[[], str] | None = None,
    lease_receipt: Mapping[str, Any] | None = None,
    broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    **provider_options: Any,
) -> GovernedConnectionResult:
    descriptor = adapter_descriptor(request.provider)
    provider = descriptor.provider

    if descriptor.execution_owner != "EXTERNAL_TVC_CONNECTION":
        blocker = f"; blocker={descriptor.blocker}" if descriptor.blocker else ""
        raise ExternalLLMConnectionError(
            f"{provider} is owned by {descriptor.execution_owner}, not the external TVC connection primitive{blocker}"
        )

    base = dict(
        request=request,
        session_id=session_id,
        transition_id=transition_id,
        measurement_id=measurement_id,
        ingress_disposition=ingress_disposition,
        ingress_receipt_hash=ingress_receipt_hash,
        carrier_ref=carrier_ref,
    )

    if lease_receipt is not None and broker_submitter is not None:
        tvc = dict(
            base,
            lease_receipt=lease_receipt,
            broker_submitter=broker_submitter,
            max_output_tokens=int(provider_options.get("max_output_tokens", 2048)),
            response_format=str(provider_options.get("response_format", "text")),
        )
        if provider == "zai":
            tvc["endpoint_profile"] = provider_options.get("endpoint_profile", "general")
        execution = _resolve_callable(descriptor.tvc_executor)(**tvc)
        return GovernedConnectionResult(provider, execution, "TVC_NON_EXPORTABLE_RUNTIME")

    if not descriptor.direct_compatibility_allowed:
        raise ExternalLLMConnectionError(
            f"{provider} requires the canonical TVC non-exportable runtime path"
        )
    if not callable(credential_resolver):
        raise ExternalLLMConnectionError(f"{provider} requires canonical TV/TVC execution material")

    direct = dict(base, credential_resolver=credential_resolver)
    if provider == "zai":
        direct["endpoint_profile"] = provider_options.get("endpoint_profile", "general")
    execution = _resolve_callable(descriptor.direct_executor)(**direct)
    return GovernedConnectionResult(provider, execution, "TV_TVC_RESOLVER_COMPATIBILITY")


def admit_external_llm_egress(
    result: GovernedConnectionResult,
    *,
    egress_disposition: str,
    egress_receipt_hash: str,
    admitted_response_hash: str,
) -> Any:
    descriptor = _ADAPTER_REGISTRY.get(result.provider)
    if descriptor is None or descriptor.execution_owner != "EXTERNAL_TVC_CONNECTION":
        raise ExternalLLMConnectionError("provider egress dispatch invariant violated")

    kwargs = dict(
        execution=result.execution,
        egress_disposition=egress_disposition,
        egress_receipt_hash=egress_receipt_hash,
        admitted_response_hash=admitted_response_hash,
    )
    if result.execution_path == "TVC_NON_EXPORTABLE_RUNTIME":
        return _resolve_callable(descriptor.tvc_egress)(**kwargs)
    if result.execution_path == "TV_TVC_RESOLVER_COMPATIBILITY" and descriptor.direct_compatibility_allowed:
        return _resolve_callable(descriptor.direct_egress)(**kwargs)
    raise ExternalLLMConnectionError("provider egress dispatch invariant violated")


__all__ = [
    "ExternalLLMConnectionError",
    "SEMANTIC_CAPABILITIES",
    "FAILURE_CLASSES",
    "ProviderAdapterDescriptor",
    "GovernedConnectionResult",
    "adapter_registry",
    "normalize_provider",
    "adapter_descriptor",
    "execute_governed_external_llm",
    "admit_external_llm_egress",
]
