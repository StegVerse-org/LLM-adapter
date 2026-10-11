"""Non-exportable TVC broker binding for admitted OpenAI (ChatGPT) InTr execution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .openai_intr_transport import OPENAI_PROVIDER_ALIASES, OpenAIInTrEnvelope, OpenAITransportAdmissionError
from .provider_client import ProviderResponse
from .provider_request import ProviderRequest, stable_hash

RUNTIME_PROFILE_ID = "stegverse:runtime-profile:llm-adapter-openai:v1"
BASE_RUNTIME_PROFILE_ID = "stegverse:runtime-profile:hb-intr-resident:v1"
TVC_REQUEST_SCHEMA = "stegverse.vault.non_exportable_operation_request.v1"
TVC_SECRET_REF = "vault://tvc/providers/openai/api-key"
TVC_OPERATION = "chat_completion_with_usage"
USAGE_KEYS = ("prompt_tokens", "completion_tokens", "total_tokens")


class OpenAITVCBrokerError(RuntimeError):
    pass


def _verify_lease(envelope: OpenAIInTrEnvelope, lease: Mapping[str, Any]) -> None:
    expected = {
        "provider": "openai", "operation": TVC_OPERATION, "model": envelope.model,
        "transition_id": envelope.transition_id, "request_hash": envelope.request_hash,
        "ingress_receipt_hash": envelope.ingress_receipt_hash, "carrier_ref": envelope.carrier_ref,
        "runtime_profile_id": RUNTIME_PROFILE_ID,
    }
    for key, value in expected.items():
        if lease.get(key) != value:
            raise OpenAITVCBrokerError(f"TVC lease exact binding mismatch: {key}")
    if lease.get("credential_authority") != "TV/TVC":
        raise OpenAITVCBrokerError("TVC lease credential authority mismatch")
    if lease.get("credential_material_present") is not False:
        raise OpenAITVCBrokerError("TVC lease contains credential material")
    if lease.get("second_machine_required") is not False:
        raise OpenAITVCBrokerError("TVC lease introduced second-machine requirement")


def build_tvc_openai_operation_request(envelope: OpenAIInTrEnvelope, request: ProviderRequest, *, lease_receipt: Mapping[str, Any], max_output_tokens: int = 2048, response_format: str = "text") -> dict[str, Any]:
    if envelope.provider != "openai" or request.provider.lower().strip() not in OPENAI_PROVIDER_ALIASES:
        raise OpenAITVCBrokerError("OpenAI provider binding required")
    if envelope.model != request.model:
        raise OpenAITVCBrokerError("OpenAI model binding mismatch")
    if envelope.authority_effect != "NONE" or not envelope.egress_intr_required:
        raise OpenAITransportAdmissionError("OpenAI envelope authority boundary invalid")
    if not isinstance(lease_receipt, Mapping) or lease_receipt.get("decision") != "ALLOW_CAPABILITY_LEASE":
        raise OpenAITVCBrokerError("TVC single-use capability lease required")
    if lease_receipt.get("single_use") is not True:
        raise OpenAITVCBrokerError("TVC lease must be single-use")
    for key in ("secret_values_exported", "protected_values_exposed", "authority_granted"):
        if lease_receipt.get(key) is not False:
            raise OpenAITVCBrokerError(f"TVC lease boundary invalid: {key}")
    _verify_lease(envelope, lease_receipt)
    if not isinstance(max_output_tokens, int) or isinstance(max_output_tokens, bool) or not 1 <= max_output_tokens <= 131072:
        raise OpenAITVCBrokerError("max_output_tokens outside TVC boundary")
    if response_format not in {"text", "json"}:
        raise OpenAITVCBrokerError("unsupported response format")
    return {
        "schema": TVC_REQUEST_SCHEMA, "secret_ref": TVC_SECRET_REF, "lease_receipt": dict(lease_receipt),
        "operation": {
            "provider": "openai", "operation": TVC_OPERATION, "model": request.model,
            "messages": [message.to_dict() for message in request.messages],
            "temperature": request.temperature, "max_output_tokens": max_output_tokens,
            "response_format": response_format, "return_secret_material": False,
            "wallet_contacted": False, "signed": False, "broadcast": False,
        },
        "single_use": True, "export_allowed": False, "return_secret_material": False,
        "runtime_profile_id": RUNTIME_PROFILE_ID, "base_runtime_profile_id": BASE_RUNTIME_PROFILE_ID,
        "intr_binding": {
            "transition_id": envelope.transition_id, "transport_id": envelope.transport_id,
            "ingress_receipt_hash": envelope.ingress_receipt_hash, "request_hash": envelope.request_hash,
            "carrier_ref": envelope.carrier_ref,
        },
        "credential_material_present": False, "authority_effect": "NONE",
    }


def _measured_usage(result: Mapping[str, Any]) -> dict[str, int] | None:
    usage = result.get("usage")
    if not isinstance(usage, Mapping):
        return None
    if not all(isinstance(usage.get(k), int) and not isinstance(usage[k], bool) and usage[k] >= 0 for k in USAGE_KEYS):
        return None
    return {k: usage[k] for k in USAGE_KEYS}


@dataclass(frozen=True)
class OpenAITVCBrokerResult:
    response: ProviderResponse
    use_receipt: Mapping[str, Any]
    broker_response_hash: str
    runtime_profile_id: str = RUNTIME_PROFILE_ID
    authority_effect: str = "NONE"
    credential_material_present: bool = False


def execute_openai_via_tvc_broker(envelope: OpenAIInTrEnvelope, request: ProviderRequest, *, lease_receipt: Mapping[str, Any], broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]], max_output_tokens: int = 2048, response_format: str = "text") -> OpenAITVCBrokerResult:
    if not callable(broker_submitter):
        raise OpenAITVCBrokerError("TVC broker submitter required")
    reply = broker_submitter(build_tvc_openai_operation_request(envelope, request, lease_receipt=lease_receipt, max_output_tokens=max_output_tokens, response_format=response_format))
    if not isinstance(reply, Mapping) or reply.get("decision") != "ALLOW_OPERATION_RESULT":
        raise OpenAITVCBrokerError("TVC broker did not admit provider result")
    result, receipt = reply.get("result"), reply.get("use_receipt")
    if not isinstance(result, Mapping) or not isinstance(receipt, Mapping):
        raise OpenAITVCBrokerError("TVC broker result malformed")
    for key, expected in {"secret_material_returned": False, "secret_material_logged": False, "secret_material_retained": False, "single_use_consumed": True}.items():
        if receipt.get(key) != expected:
            raise OpenAITVCBrokerError(f"TVC use receipt boundary mismatch: {key}")
    # A clean use receipt cannot override credential material embedded in the result.
    # Reject known secret-bearing fields before creating any downstream response or usage event.
    forbidden = {"api_key", "access_token", "refresh_token", "secret", "secret_value", "credential_material", "authorization"}
    def contains_secret_field(value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(
                (isinstance(key, str) and key.lower() in forbidden)
                or contains_secret_field(child)
                for key, child in value.items()
            )
        if isinstance(value, (list, tuple)):
            return any(contains_secret_field(child) for child in value)
        return False

    if contains_secret_field(result):
        raise OpenAITVCBrokerError("TVC OpenAI result contains credential material")
    output = result.get("output") or result.get("content")
    if not isinstance(output, str) or not output.strip():
        raise OpenAITVCBrokerError("TVC OpenAI result missing text output")
    usage = _measured_usage(result)
    runtime_model = result.get("model")
    response = ProviderResponse(
        provider="openai", model=request.model, output=output, request_hash=envelope.request_hash,
        metadata={
            "provider_mode": "openai_tvc_non_exportable_operation",
            "runtime_profile_id": RUNTIME_PROFILE_ID, "base_runtime_profile_id": BASE_RUNTIME_PROFILE_ID,
            "transport_id": envelope.transport_id, "ingress_receipt_hash": envelope.ingress_receipt_hash,
            "response_id": result.get("response_id") if isinstance(result.get("response_id"), str) else None,
            "runtime_model": runtime_model if isinstance(runtime_model, str) and runtime_model else None,
            "usage": usage, "usage_measured": usage is not None,
            "tvc_use_receipt_hash": stable_hash(dict(receipt)),
            "credential_authority": "TV/TVC", "credential_material_present": False,
            "egress_intr_required": True, "authority_effect": "NONE",
        },
    )
    return OpenAITVCBrokerResult(response=response, use_receipt=dict(receipt), broker_response_hash=stable_hash(dict(reply)))


__all__ = ["RUNTIME_PROFILE_ID", "BASE_RUNTIME_PROFILE_ID", "TVC_REQUEST_SCHEMA", "TVC_SECRET_REF", "TVC_OPERATION",
           "OpenAITVCBrokerError", "OpenAITVCBrokerResult", "build_tvc_openai_operation_request", "execute_openai_via_tvc_broker"]
