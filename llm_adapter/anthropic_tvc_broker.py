"""Non-exportable TVC broker binding for admitted Anthropic InTr execution."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .anthropic_convergence_bridge import AnthropicConvergenceEnvelope
from .provider_client import ProviderResponse
from .provider_request import ProviderRequest, stable_hash

RUNTIME_PROFILE_ID = "stegverse:runtime-profile:llm-adapter-anthropic:v1"
BASE_RUNTIME_PROFILE_ID = "stegverse:runtime-profile:hb-intr-resident:v1"
TVC_REQUEST_SCHEMA = "stegverse.vault.non_exportable_operation_request.v1"
TVC_SECRET_REF = "vault://tvc/providers/anthropic/api-key"
TVC_OPERATION = "message_with_usage"

class AnthropicTVCBrokerError(RuntimeError): pass


def _prompt(request: ProviderRequest) -> str:
    return "\n".join(f"{m.role}: {m.content}" for m in request.messages)


def _verify_lease(envelope: AnthropicConvergenceEnvelope, lease: Mapping[str, Any]) -> None:
    expected = {"provider":"anthropic","operation":TVC_OPERATION,"model":envelope.model,"transition_id":envelope.transition_id,"request_hash":envelope.request_hash,"ingress_receipt_hash":envelope.ingress_receipt_hash,"carrier_ref":envelope.carrier_ref,"runtime_profile_id":RUNTIME_PROFILE_ID}
    for key, value in expected.items():
        if lease.get(key) != value: raise AnthropicTVCBrokerError(f"TVC lease exact binding mismatch: {key}")
    if lease.get("credential_authority") != "TV/TVC": raise AnthropicTVCBrokerError("TVC lease credential authority mismatch")
    if lease.get("credential_material_present") is not False: raise AnthropicTVCBrokerError("TVC lease contains credential material")
    if lease.get("second_machine_required") is not False: raise AnthropicTVCBrokerError("TVC lease introduced second-machine requirement")


def build_tvc_anthropic_operation_request(envelope: AnthropicConvergenceEnvelope, request: ProviderRequest, *, lease_receipt: Mapping[str, Any], max_output_tokens: int = 2048, response_format: str = "text") -> dict[str, Any]:
    if envelope.provider != "anthropic" or request.provider.lower().strip() not in {"anthropic","claude","anthropic_http"}: raise AnthropicTVCBrokerError("Anthropic provider binding required")
    if envelope.model != request.model: raise AnthropicTVCBrokerError("Anthropic model binding mismatch")
    if envelope.authority_effect != "NONE" or not envelope.egress_intr_required: raise AnthropicTVCBrokerError("Anthropic envelope authority boundary invalid")
    if not isinstance(lease_receipt, Mapping) or lease_receipt.get("decision") != "ALLOW_CAPABILITY_LEASE": raise AnthropicTVCBrokerError("TVC single-use capability lease required")
    if lease_receipt.get("single_use") is not True: raise AnthropicTVCBrokerError("TVC lease must be single-use")
    for key in ("secret_values_exported","protected_values_exposed","authority_granted"):
        if lease_receipt.get(key) is not False: raise AnthropicTVCBrokerError(f"TVC lease boundary invalid: {key}")
    _verify_lease(envelope, lease_receipt)
    if not isinstance(max_output_tokens, int) or not 1 <= max_output_tokens <= 16384: raise AnthropicTVCBrokerError("max_output_tokens outside TVC boundary")
    if response_format not in {"text","json"}: raise AnthropicTVCBrokerError("unsupported response format")
    return {"schema":TVC_REQUEST_SCHEMA,"secret_ref":TVC_SECRET_REF,"lease_receipt":dict(lease_receipt),"operation":{"provider":"anthropic","operation":TVC_OPERATION,"model":request.model,"prompt":_prompt(request),"max_output_tokens":max_output_tokens,"response_format":response_format,"return_secret_material":False,"wallet_contacted":False,"signed":False,"broadcast":False},"single_use":True,"export_allowed":False,"return_secret_material":False,"runtime_profile_id":RUNTIME_PROFILE_ID,"base_runtime_profile_id":BASE_RUNTIME_PROFILE_ID,"intr_binding":{"transition_id":envelope.transition_id,"transport_id":envelope.transport_id,"ingress_receipt_hash":envelope.ingress_receipt_hash,"request_hash":envelope.request_hash,"carrier_ref":envelope.carrier_ref},"credential_material_present":False,"authority_effect":"NONE"}

@dataclass(frozen=True)
class AnthropicTVCBrokerResult:
    response: ProviderResponse
    use_receipt: Mapping[str, Any]
    broker_response_hash: str
    runtime_profile_id: str = RUNTIME_PROFILE_ID
    authority_effect: str = "NONE"
    credential_material_present: bool = False


# Keys are compared after lowercasing and dropping non-alphanumerics, so spelling
# variants (apiKey, x-api-key, openai_api_key) cannot slip past the guard.
_CREDENTIAL_RESULT_KEYS = {"apikey", "xapikey", "accesstoken", "refreshtoken", "bearertoken", "secret", "secretvalue",
                           "credentialmaterial", "authorization", "password"}
_MAX_RESULT_DEPTH = 64


def _credential_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized in _CREDENTIAL_RESULT_KEYS or normalized.endswith("apikey")


def _contains_credential_field(value: Any, depth: int = 0) -> bool:
    """True when any mapping key at any depth names credential material."""
    if depth > _MAX_RESULT_DEPTH:
        raise AnthropicTVCBrokerError("TVC Anthropic result exceeds nesting limit")
    if isinstance(value, Mapping):
        return any(_credential_key(k) or _contains_credential_field(v, depth + 1) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_credential_field(v, depth + 1) for v in value)
    return False
USAGE_KEYS = ("input_tokens", "output_tokens")


def _measured_usage(result: Mapping[str, Any]) -> dict[str, int] | None:
    """Native Anthropic token usage, only when every count is a measured non-negative int."""
    usage = result.get("usage")
    if not isinstance(usage, Mapping):
        return None
    if not all(isinstance(usage.get(k), int) and not isinstance(usage[k], bool) and usage[k] >= 0 for k in USAGE_KEYS):
        return None
    return {k: usage[k] for k in USAGE_KEYS}


def execute_anthropic_via_tvc_broker(envelope: AnthropicConvergenceEnvelope, request: ProviderRequest, *, lease_receipt: Mapping[str, Any], broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]], max_output_tokens: int = 2048, response_format: str = "text") -> AnthropicTVCBrokerResult:
    if not callable(broker_submitter): raise AnthropicTVCBrokerError("TVC broker submitter required")
    reply = broker_submitter(build_tvc_anthropic_operation_request(envelope, request, lease_receipt=lease_receipt, max_output_tokens=max_output_tokens, response_format=response_format))
    if not isinstance(reply, Mapping) or reply.get("decision") != "ALLOW_OPERATION_RESULT": raise AnthropicTVCBrokerError("TVC broker did not admit provider result")
    result, receipt = reply.get("result"), reply.get("use_receipt")
    if not isinstance(result, Mapping) or not isinstance(receipt, Mapping): raise AnthropicTVCBrokerError("TVC broker result malformed")
    for key, expected in {"secret_material_returned":False,"secret_material_logged":False,"secret_material_retained":False,"single_use_consumed":True}.items():
        if receipt.get(key) != expected: raise AnthropicTVCBrokerError(f"TVC use receipt boundary mismatch: {key}")
    # A clean use receipt cannot override credential material embedded in the result.
    if _contains_credential_field(result):
        raise AnthropicTVCBrokerError("TVC Anthropic result contains credential material")
    output = result.get("output") or result.get("content")
    if not isinstance(output, str) or not output.strip(): raise AnthropicTVCBrokerError("TVC Anthropic result missing text output")
    usage = _measured_usage(result)
    runtime_model = result.get("model")
    response = ProviderResponse(provider="anthropic", model=request.model, output=output, request_hash=envelope.request_hash, metadata={"provider_mode":"anthropic_tvc_non_exportable_operation","runtime_profile_id":RUNTIME_PROFILE_ID,"base_runtime_profile_id":BASE_RUNTIME_PROFILE_ID,"transport_id":envelope.transport_id,"ingress_receipt_hash":envelope.ingress_receipt_hash,"runtime_model":runtime_model if isinstance(runtime_model, str) and runtime_model else None,"usage":usage,"usage_measured":usage is not None,"tvc_use_receipt_hash":stable_hash(dict(receipt)),"credential_authority":"TV/TVC","credential_material_present":False,"egress_intr_required":True,"authority_effect":"NONE"})
    return AnthropicTVCBrokerResult(response=response,use_receipt=dict(receipt),broker_response_hash=stable_hash(dict(reply)))

__all__=["RUNTIME_PROFILE_ID","BASE_RUNTIME_PROFILE_ID","TVC_REQUEST_SCHEMA","TVC_SECRET_REF","TVC_OPERATION","AnthropicTVCBrokerError","AnthropicTVCBrokerResult","build_tvc_anthropic_operation_request","execute_anthropic_via_tvc_broker"]
