"""Provider-neutral governed external-LLM connection primitive.

This module does not create governance, runtime, credential, worker, heartbeat,
or custody authority. It only selects an already-implemented provider adapter
behind the same Interlock/InTr -> TV/TVC -> provider -> Master Records ->
Interlock/InTr sequence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .provider_request import ProviderRequest
from .zai_intr_executor import execute_governed_zai, admit_zai_egress
from .deepseek_intr_executor import execute_governed_deepseek, admit_deepseek_egress
from .kimi_intr_executor import execute_governed_kimi, admit_kimi_egress
from .anthropic_intr_executor import execute_governed_anthropic, admit_anthropic_egress

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
    authority_effect: str = "NONE"
    egress_intr_required: bool = True
    @property
    def response_hash(self) -> str: return str(self.execution.response_hash)
    @property
    def egress_handoff(self) -> Any: return self.execution.egress_handoff
    def evidence(self) -> dict[str, Any]:
        return {"schema":"stegverse.llm_adapter.external_llm_connection/v1","provider":self.provider,"response_hash":self.response_hash,"execution":self.execution.evidence(),"egress_intr_required":True,"authority_effect":"NONE"}

def normalize_provider(provider: str) -> str:
    normalized = _PROVIDER_ALIASES.get(provider.lower().strip())
    if not normalized: raise ExternalLLMConnectionError(f"unsupported external LLM provider: {provider}")
    return normalized

def execute_governed_external_llm(request: ProviderRequest, *, session_id: str, transition_id: str, measurement_id: str, ingress_disposition: str, ingress_receipt_hash: str, carrier_ref: str, credential_resolver: Callable[[], str], **provider_options: Any) -> GovernedConnectionResult:
    provider = normalize_provider(request.provider)
    common = dict(request=request, session_id=session_id, transition_id=transition_id, measurement_id=measurement_id, ingress_disposition=ingress_disposition, ingress_receipt_hash=ingress_receipt_hash, carrier_ref=carrier_ref, credential_resolver=credential_resolver)
    if provider == "zai": execution = execute_governed_zai(**common, endpoint_profile=provider_options.get("endpoint_profile", "general"))
    elif provider == "deepseek": execution = execute_governed_deepseek(**common)
    elif provider == "kimi": execution = execute_governed_kimi(**common)
    elif provider == "anthropic": execution = execute_governed_anthropic(**common, max_tokens=int(provider_options.get("max_tokens", 1024)))
    else: raise ExternalLLMConnectionError("provider dispatch invariant violated")
    return GovernedConnectionResult(provider, execution)

def admit_external_llm_egress(result: GovernedConnectionResult, *, egress_disposition: str, egress_receipt_hash: str, admitted_response_hash: str) -> Any:
    kwargs = dict(execution=result.execution, egress_disposition=egress_disposition, egress_receipt_hash=egress_receipt_hash, admitted_response_hash=admitted_response_hash)
    if result.provider == "zai": return admit_zai_egress(**kwargs)
    if result.provider == "deepseek": return admit_deepseek_egress(**kwargs)
    if result.provider == "kimi": return admit_kimi_egress(**kwargs)
    if result.provider == "anthropic": return admit_anthropic_egress(**kwargs)
    raise ExternalLLMConnectionError("provider egress dispatch invariant violated")

__all__ = ["ExternalLLMConnectionError","GovernedConnectionResult","normalize_provider","execute_governed_external_llm","admit_external_llm_egress"]
