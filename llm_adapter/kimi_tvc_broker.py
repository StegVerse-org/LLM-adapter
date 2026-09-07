"""Runtime-profile bridge from admitted Kimi InTr execution to TVC.

This module never accepts provider credential material. It constructs the existing
TVC non-exportable provider-operation request and consumes only the canonical
sanitized measurement evidence returned by TVC. InTr remains ingress/egress
transition authority; TV/TVC remains credential/provider-operation authority;
provider output remains non-authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .kimi_intr_transport import KimiInTrEnvelope, KimiTransportAdmissionError
from .provider_client import ProviderResponse
from .provider_request import ProviderRequest, stable_hash

RUNTIME_PROFILE_ID = "stegverse:runtime-profile:llm-adapter-kimi:v1"
BASE_RUNTIME_PROFILE_ID = "stegverse:runtime-profile:hb-intr-resident:v1"
TVC_REQUEST_SCHEMA = "stegverse.vault.non_exportable_operation_request.v1"
TVC_MEASUREMENT_EVIDENCE_SCHEMA = "stegverse.tvc.provider-measurement-evidence.v1"
TVC_SECRET_REF = "vault://tvc/providers/kimi/api-key"
TVC_OPERATION = "chat_completion_with_usage"


class KimiTVCBrokerError(RuntimeError):
    pass


def _prompt(request: ProviderRequest) -> str:
    return "\n".join(f"{message.role}: {message.content}" for message in request.messages)


def build_tvc_kimi_operation_request(
    envelope: KimiInTrEnvelope,
    request: ProviderRequest,
    *,
    lease_receipt: Mapping[str, Any],
    max_output_tokens: int = 2048,
    response_format: str = "text",
) -> dict[str, Any]:
    if envelope.provider != "kimi" or request.provider.lower().strip() not in {"kimi", "moonshot", "kimi_http"}:
        raise KimiTVCBrokerError("Kimi provider binding required")
    if envelope.model != request.model:
        raise KimiTVCBrokerError("Kimi model binding mismatch")
    if envelope.authority_effect != "NONE" or not envelope.egress_intr_required:
        raise KimiTransportAdmissionError("Kimi envelope authority boundary invalid")
    if not isinstance(lease_receipt, Mapping) or lease_receipt.get("decision") != "ALLOW_CAPABILITY_LEASE":
        raise KimiTVCBrokerError("TVC single-use capability lease required")
    if lease_receipt.get("provider") != "kimi" or lease_receipt.get("operation") != TVC_OPERATION:
        raise KimiTVCBrokerError("TVC lease outside Kimi provider-operation boundary")
    if lease_receipt.get("model") not in (None, request.model):
        raise KimiTVCBrokerError("TVC lease model does not match Kimi request")
    if lease_receipt.get("single_use") is not True:
        raise KimiTVCBrokerError("TVC lease must be single-use")
    for key in ("secret_values_exported", "protected_values_exposed", "authority_granted"):
        if lease_receipt.get(key) is not False:
            raise KimiTVCBrokerError(f"TVC lease authority/secret boundary invalid: {key}")
    if not isinstance(max_output_tokens, int) or max_output_tokens < 1 or max_output_tokens > 16384:
        raise KimiTVCBrokerError("max_output_tokens outside TVC boundary")
    if response_format not in {"text", "json"}:
        raise KimiTVCBrokerError("unsupported response format")

    operation = {
        "provider": "kimi",
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
class KimiTVCBrokerResult:
    response: ProviderResponse
    use_receipt: Mapping[str, Any]
    measurement_evidence: Mapping[str, Any]
    broker_response_hash: str
    runtime_profile_id: str = RUNTIME_PROFILE_ID
    authority_effect: str = "NONE"
    credential_material_present: bool = False


def _canonical_measurement_evidence(reply: Mapping[str, Any], request: ProviderRequest) -> Mapping[str, Any]:
    evidence = reply.get("measurement_evidence")
    if not isinstance(evidence, Mapping):
        raise KimiTVCBrokerError("TVC canonical Kimi measurement evidence missing")
    if evidence.get("schema") != TVC_MEASUREMENT_EVIDENCE_SCHEMA:
        raise KimiTVCBrokerError("TVC Kimi measurement evidence schema mismatch")
    if evidence.get("provider") != "kimi":
        raise KimiTVCBrokerError("TVC Kimi measurement evidence provider mismatch")
    if evidence.get("model") != request.model:
        raise KimiTVCBrokerError("TVC Kimi measurement evidence model mismatch")
    if evidence.get("provider_api_key_transferred_to_consumer") is not False:
        raise KimiTVCBrokerError("TVC Kimi measurement evidence indicates credential transfer")
    if evidence.get("secret_material_returned") is not False:
        raise KimiTVCBrokerError("TVC Kimi measurement evidence indicates secret return")
    output = evidence.get("candidate_output")
    if not isinstance(output, str) or not output.strip():
        raise KimiTVCBrokerError("TVC Kimi measurement evidence missing candidate output")
    usage = evidence.get("provider_usage")
    normalized_usage = evidence.get("normalized_usage")
    if not isinstance(usage, Mapping) or not isinstance(normalized_usage, Mapping):
        raise KimiTVCBrokerError("TVC Kimi measurement evidence missing usage")
    return evidence


def execute_kimi_via_tvc_broker(
    envelope: KimiInTrEnvelope,
    request: ProviderRequest,
    *,
    lease_receipt: Mapping[str, Any],
    broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    max_output_tokens: int = 2048,
    response_format: str = "text",
) -> KimiTVCBrokerResult:
    if not callable(broker_submitter):
        raise KimiTVCBrokerError("TVC broker submitter required")
    broker_request = build_tvc_kimi_operation_request(
        envelope,
        request,
        lease_receipt=lease_receipt,
        max_output_tokens=max_output_tokens,
        response_format=response_format,
    )
    reply = broker_submitter(broker_request)
    if not isinstance(reply, Mapping) or reply.get("decision") != "ALLOW_OPERATION_RESULT":
        raise KimiTVCBrokerError("TVC broker did not admit provider result")
    result = reply.get("result")
    receipt = reply.get("use_receipt")
    if not isinstance(result, Mapping) or not isinstance(receipt, Mapping):
        raise KimiTVCBrokerError("TVC broker result malformed")
    if receipt.get("provider") not in (None, "kimi"):
        raise KimiTVCBrokerError("TVC use receipt provider mismatch")
    for key, expected in {
        "secret_material_returned": False,
        "secret_material_logged": False,
        "secret_material_retained": False,
        "single_use_consumed": True,
    }.items():
        if receipt.get(key) != expected:
            raise KimiTVCBrokerError(f"TVC use receipt boundary mismatch: {key}")

    measurement_evidence = _canonical_measurement_evidence(reply, request)
    output = str(measurement_evidence["candidate_output"])
    usage = dict(measurement_evidence["provider_usage"])
    normalized_usage = dict(measurement_evidence["normalized_usage"])
    response_id = measurement_evidence.get("provider_response_id")
    if not isinstance(response_id, str) or not response_id:
        raise KimiTVCBrokerError("TVC Kimi measurement evidence missing provider response id")

    response = ProviderResponse(
        provider="kimi",
        model=request.model,
        output=output,
        request_hash=envelope.request_hash,
        metadata={
            "provider_mode": "kimi_tvc_non_exportable_operation",
            "runtime_profile_id": RUNTIME_PROFILE_ID,
            "base_runtime_profile_id": BASE_RUNTIME_PROFILE_ID,
            "transport_id": envelope.transport_id,
            "ingress_receipt_hash": envelope.ingress_receipt_hash,
            "provider_response_id": response_id,
            "usage": usage,
            "normalized_usage": normalized_usage,
            "tvc_measurement_evidence_hash": stable_hash(dict(measurement_evidence)),
            "tvc_use_receipt_hash": stable_hash(dict(receipt)),
            "credential_authority": "TV/TVC",
            "credential_material_present": False,
            "egress_intr_required": True,
            "authority_effect": "NONE",
        },
    )
    return KimiTVCBrokerResult(
        response=response,
        use_receipt=dict(receipt),
        measurement_evidence=dict(measurement_evidence),
        broker_response_hash=stable_hash(dict(reply)),
    )


__all__ = [
    "RUNTIME_PROFILE_ID", "BASE_RUNTIME_PROFILE_ID", "TVC_REQUEST_SCHEMA",
    "TVC_MEASUREMENT_EVIDENCE_SCHEMA", "TVC_SECRET_REF", "TVC_OPERATION",
    "KimiTVCBrokerError", "KimiTVCBrokerResult", "build_tvc_kimi_operation_request",
    "execute_kimi_via_tvc_broker",
]
