"""Runtime-profile bridge from admitted DeepSeek InTr execution to TVC.

This module never accepts provider credential material. It constructs the existing
TVC non-exportable provider-operation request and consumes only sanitized broker
results. InTr remains ingress/egress transition authority; TV/TVC remains
credential/route authority; provider output remains non-authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .deepseek_intr_transport import DeepSeekInTrEnvelope, DeepSeekTransportAdmissionError
from .provider_client import ProviderResponse
from .provider_request import ProviderRequest, stable_hash

RUNTIME_PROFILE_ID = "stegverse:runtime-profile:llm-adapter-deepseek:v1"
BASE_RUNTIME_PROFILE_ID = "stegverse:runtime-profile:hb-intr-resident:v1"
TVC_REQUEST_SCHEMA = "stegverse.vault.non_exportable_operation_request.v1"
TVC_SECRET_REF = "vault://tvc/providers/deepseek/api-key"
TVC_OPERATION = "chat_completion_with_usage"


class DeepSeekTVCBrokerError(RuntimeError):
    pass


def _prompt(request: ProviderRequest) -> str:
    # Preserve role/content deterministically without asking TVC to reconstruct chat state.
    return "\n".join(f"{message.role}: {message.content}" for message in request.messages)


def build_tvc_deepseek_operation_request(
    envelope: DeepSeekInTrEnvelope,
    request: ProviderRequest,
    *,
    lease_receipt: Mapping[str, Any],
    max_output_tokens: int = 2048,
    response_format: str = "text",
) -> dict[str, Any]:
    if envelope.provider != "deepseek" or request.provider.lower().strip() not in {"deepseek", "deepseek_http"}:
        raise DeepSeekTVCBrokerError("DeepSeek provider binding required")
    if envelope.model != request.model:
        raise DeepSeekTVCBrokerError("DeepSeek model binding mismatch")
    if envelope.authority_effect != "NONE" or not envelope.egress_intr_required:
        raise DeepSeekTransportAdmissionError("DeepSeek envelope authority boundary invalid")
    if not isinstance(lease_receipt, Mapping) or lease_receipt.get("decision") != "ALLOW_CAPABILITY_LEASE":
        raise DeepSeekTVCBrokerError("TVC single-use capability lease required")
    if lease_receipt.get("provider") != "deepseek" or lease_receipt.get("operation") != TVC_OPERATION:
        raise DeepSeekTVCBrokerError("TVC lease outside DeepSeek provider-operation boundary")
    if lease_receipt.get("single_use") is not True:
        raise DeepSeekTVCBrokerError("TVC lease must be single-use")
    for key in ("secret_values_exported", "protected_values_exposed", "authority_granted"):
        if lease_receipt.get(key) is not False:
            raise DeepSeekTVCBrokerError(f"TVC lease authority/secret boundary invalid: {key}")
    if not isinstance(max_output_tokens, int) or max_output_tokens < 1 or max_output_tokens > 16384:
        raise DeepSeekTVCBrokerError("max_output_tokens outside TVC boundary")
    if response_format not in {"text", "json"}:
        raise DeepSeekTVCBrokerError("unsupported response format")

    operation = {
        "provider": "deepseek",
        "operation": TVC_OPERATION,
        "model": request.model,
        "prompt": _prompt(request),
        "max_output_tokens": max_output_tokens,
        "response_format": response_format,
        "return_secret_material": False,
        "wallet_contacted": False,
        "signed": False,
        "broadcast": False,
    }
    return {
        "schema": TVC_REQUEST_SCHEMA,
        "secret_ref": TVC_SECRET_REF,
        "lease_receipt": dict(lease_receipt),
        "operation": operation,
        "single_use": True,
        "export_allowed": False,
        "return_secret_material": False,
        "runtime_profile_id": RUNTIME_PROFILE_ID,
        "base_runtime_profile_id": BASE_RUNTIME_PROFILE_ID,
        "intr_binding": {
            "transition_id": envelope.transition_id,
            "transport_id": envelope.transport_id,
            "ingress_receipt_hash": envelope.ingress_receipt_hash,
            "request_hash": envelope.request_hash,
            "carrier_ref": envelope.carrier_ref,
        },
        "credential_material_present": False,
        "authority_effect": "NONE",
    }


@dataclass(frozen=True)
class DeepSeekTVCBrokerResult:
    response: ProviderResponse
    use_receipt: Mapping[str, Any]
    broker_response_hash: str
    runtime_profile_id: str = RUNTIME_PROFILE_ID
    authority_effect: str = "NONE"
    credential_material_present: bool = False


def execute_deepseek_via_tvc_broker(
    envelope: DeepSeekInTrEnvelope,
    request: ProviderRequest,
    *,
    lease_receipt: Mapping[str, Any],
    broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    max_output_tokens: int = 2048,
    response_format: str = "text",
) -> DeepSeekTVCBrokerResult:
    if not callable(broker_submitter):
        raise DeepSeekTVCBrokerError("TVC broker submitter required")
    broker_request = build_tvc_deepseek_operation_request(
        envelope,
        request,
        lease_receipt=lease_receipt,
        max_output_tokens=max_output_tokens,
        response_format=response_format,
    )
    reply = broker_submitter(broker_request)
    if not isinstance(reply, Mapping) or reply.get("decision") != "ALLOW_OPERATION_RESULT":
        raise DeepSeekTVCBrokerError("TVC broker did not admit provider result")
    result = reply.get("result")
    receipt = reply.get("use_receipt")
    if not isinstance(result, Mapping) or not isinstance(receipt, Mapping):
        raise DeepSeekTVCBrokerError("TVC broker result malformed")
    for key, expected in {
        "secret_material_returned": False,
        "secret_material_logged": False,
        "secret_material_retained": False,
        "single_use_consumed": True,
    }.items():
        if receipt.get(key) != expected:
            raise DeepSeekTVCBrokerError(f"TVC use receipt boundary mismatch: {key}")

    output = result.get("output")
    if not isinstance(output, str) or not output.strip():
        # Canonical TVC normalization may expose text under a provider-neutral content field.
        output = result.get("content")
    if not isinstance(output, str) or not output.strip():
        raise DeepSeekTVCBrokerError("TVC DeepSeek result missing text output")

    usage = result.get("usage") if isinstance(result.get("usage"), Mapping) else None
    response = ProviderResponse(
        provider="deepseek",
        model=request.model,
        output=output,
        request_hash=envelope.request_hash,
        metadata={
            "provider_mode": "deepseek_tvc_non_exportable_operation",
            "runtime_profile_id": RUNTIME_PROFILE_ID,
            "base_runtime_profile_id": BASE_RUNTIME_PROFILE_ID,
            "transport_id": envelope.transport_id,
            "ingress_receipt_hash": envelope.ingress_receipt_hash,
            "usage": dict(usage) if usage is not None else None,
            "tvc_use_receipt_hash": stable_hash(dict(receipt)),
            "credential_authority": "TV/TVC",
            "credential_material_present": False,
            "egress_intr_required": True,
            "authority_effect": "NONE",
        },
    )
    return DeepSeekTVCBrokerResult(
        response=response,
        use_receipt=dict(receipt),
        broker_response_hash=stable_hash(dict(reply)),
    )


__all__ = [
    "RUNTIME_PROFILE_ID", "BASE_RUNTIME_PROFILE_ID", "TVC_REQUEST_SCHEMA", "TVC_SECRET_REF", "TVC_OPERATION",
    "DeepSeekTVCBrokerError", "DeepSeekTVCBrokerResult", "build_tvc_deepseek_operation_request",
    "execute_deepseek_via_tvc_broker",
]
