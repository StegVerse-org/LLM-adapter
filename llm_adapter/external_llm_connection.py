"""Provider-neutral governed external-LLM connection primitive.

No governance, runtime, credential, worker, heartbeat, route, or custody authority
is created here. This module selects existing provider adapters behind one common
Interlock/InTr -> TV/TVC -> provider -> Master Records -> InTr sequence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .provider_request import ProviderRequest
from .zai_intr_executor import execute_governed_zai, admit_zai_egress
from .deepseek_intr_executor import execute_governed_deepseek, admit_deepseek_egress
from .kimi_intr_executor import execute_governed_kimi, admit_kimi_egress
from .anthropic_intr_executor import execute_governed_anthropic, admit_anthropic_egress
from .zai_tvc_runtime_executor import execute_governed_zai_via_tvc_runtime, admit_zai_tvc_runtime_egress
from .deepseek_tvc_runtime_executor import execute_governed_deepseek_via_tvc_runtime, admit_deepseek_tvc_runtime_egress
from .kimi_tvc_runtime_executor import execute_governed_kimi_via_tvc_runtime, admit_kimi_tvc_runtime_egress
from .anthropic_tvc_runtime_executor import execute_governed_anthropic_via_tvc_runtime, admit_anthropic_tvc_runtime_egress

class ExternalLLMConnectionError(RuntimeError): pass

_PROVIDER_ALIASES = {
    "z.ai": "zai", "zai": "zai", "z_ai": "zai",
    "deepseek": "deepseek", "deepseek_http": "deepseek",
    "kimi": "kimi", "moonshot": "kimi", "kimi_http": "kimi",
    "anthropic": "anthropic", "claude": "anthropic", "anthropic_http": "anthropic",
}

@dataclass(frozen=True)
class GovernedConnectionResult:
    provider: str
    execution: Any
    execution_path: str
    authority_effect: str = "NONE"
    egress_intr_required: bool = True

    @property
    def response_hash(self) -> str: return str(self.execution.response_hash)
    @property
    def egress_handoff(self) -> Any: return self.execution.egress_handoff
    @property
    def response(self) -> Any:
        transport = getattr(self.execution, "transport", None)
        if transport is not None and getattr(transport, "response", None) is not None: return transport.response
        broker = getattr(self.execution, "broker", None)
        if broker is not None and getattr(broker, "response", None) is not None: return broker.response
        raise ExternalLLMConnectionError("governed execution has no provider response")
    def evidence(self) -> dict[str, Any]:
        execution_evidence = self.execution.evidence() if hasattr(self.execution, "evidence") else {
            "transition_id": self.execution.envelope.transition_id,
            "response_hash": self.response_hash,
            "runtime_profile_id": getattr(self.execution, "runtime_profile_id", None),
            "authority_effect": getattr(self.execution, "authority_effect", "NONE"),
        }
        return {"schema":"stegverse.llm_adapter.external_llm_connection/v1","provider":self.provider,"execution_path":self.execution_path,"response_hash":self.response_hash,"execution":execution_evidence,"egress_intr_required":True,"authority_effect":"NONE"}


def normalize_provider(provider: str) -> str:
    normalized = _PROVIDER_ALIASES.get(provider.lower().strip())
    if not normalized: raise ExternalLLMConnectionError(f"unsupported external LLM provider: {provider}")
    return normalized


def execute_governed_external_llm(request: ProviderRequest, *, session_id: str, transition_id: str, measurement_id: str, ingress_disposition: str, ingress_receipt_hash: str, carrier_ref: str, credential_resolver: Callable[[], str] | None = None, lease_receipt: Mapping[str, Any] | None = None, broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None, **provider_options: Any) -> GovernedConnectionResult:
    provider = normalize_provider(request.provider)
    base = dict(request=request, session_id=session_id, transition_id=transition_id, measurement_id=measurement_id, ingress_disposition=ingress_disposition, ingress_receipt_hash=ingress_receipt_hash, carrier_ref=carrier_ref)

    if lease_receipt is not None and broker_submitter is not None:
        tvc = dict(base, lease_receipt=lease_receipt, broker_submitter=broker_submitter, max_output_tokens=int(provider_options.get("max_output_tokens", 2048)), response_format=str(provider_options.get("response_format", "text")))
        if provider == "zai": execution = execute_governed_zai_via_tvc_runtime(**tvc, endpoint_profile=provider_options.get("endpoint_profile", "general"))
        elif provider == "deepseek": execution = execute_governed_deepseek_via_tvc_runtime(**tvc)
        elif provider == "kimi": execution = execute_governed_kimi_via_tvc_runtime(**tvc)
        elif provider == "anthropic": execution = execute_governed_anthropic_via_tvc_runtime(**tvc)
        else: raise ExternalLLMConnectionError("provider TVC dispatch invariant violated")
        return GovernedConnectionResult(provider, execution, "TVC_NON_EXPORTABLE_RUNTIME")

    if not callable(credential_resolver):
        raise ExternalLLMConnectionError(f"{provider} requires canonical TV/TVC execution material")
    direct = dict(base, credential_resolver=credential_resolver)
    if provider == "zai": execution = execute_governed_zai(**direct, endpoint_profile=provider_options.get("endpoint_profile", "general"))
    elif provider == "deepseek": execution = execute_governed_deepseek(**direct)
    elif provider == "kimi": execution = execute_governed_kimi(**direct)
    elif provider == "anthropic": execution = execute_governed_anthropic(**direct, max_tokens=int(provider_options.get("max_tokens", 1024)))
    else: raise ExternalLLMConnectionError("provider compatibility dispatch invariant violated")
    return GovernedConnectionResult(provider, execution, "TV_TVC_RESOLVER_COMPATIBILITY")


def admit_external_llm_egress(result: GovernedConnectionResult, *, egress_disposition: str, egress_receipt_hash: str, admitted_response_hash: str) -> Any:
    kwargs = dict(execution=result.execution, egress_disposition=egress_disposition, egress_receipt_hash=egress_receipt_hash, admitted_response_hash=admitted_response_hash)
    if result.execution_path == "TVC_NON_EXPORTABLE_RUNTIME":
        if result.provider == "zai": return admit_zai_tvc_runtime_egress(**kwargs)
        if result.provider == "deepseek": return admit_deepseek_tvc_runtime_egress(**kwargs)
        if result.provider == "kimi": return admit_kimi_tvc_runtime_egress(**kwargs)
        if result.provider == "anthropic": return admit_anthropic_tvc_runtime_egress(**kwargs)
    if result.provider == "zai": return admit_zai_egress(**kwargs)
    if result.provider == "deepseek": return admit_deepseek_egress(**kwargs)
    if result.provider == "kimi": return admit_kimi_egress(**kwargs)
    if result.provider == "anthropic": return admit_anthropic_egress(**kwargs)
    raise ExternalLLMConnectionError("provider egress dispatch invariant violated")

__all__ = ["ExternalLLMConnectionError","GovernedConnectionResult","normalize_provider","execute_governed_external_llm","admit_external_llm_egress"]
