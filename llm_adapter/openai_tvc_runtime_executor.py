"""Governed OpenAI (ChatGPT) execution through the canonical runtime-profile/TVC broker path."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .openai_intr_transport import OpenAIInTrEnvelope, build_openai_intr_envelope
from .openai_tvc_broker import RUNTIME_PROFILE_ID, USAGE_KEYS, OpenAITVCBrokerResult, execute_openai_via_tvc_broker
from .provider_request import ProviderRequest
from .provider_usage import ProviderMetric, build_provider_usage_event
from .provider_usage_submission import record_provider_usage_event_locally, record_usage_non_gating

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class OpenAITVCRuntimeExecutionError(RuntimeError):
    pass


def _metric(value: Any, source_ref: str) -> ProviderMetric:
    if isinstance(value, int) and not isinstance(value, bool):
        return ProviderMetric(value=str(value), unit="tokens", evidence_class="MEASURED", source_ref=source_ref)
    return ProviderMetric(value=None, unit="tokens", evidence_class="UNAVAILABLE", source_ref=source_ref)


@dataclass(frozen=True)
class OpenAITVCRuntimeExecution:
    envelope: OpenAIInTrEnvelope
    broker: OpenAITVCBrokerResult
    provider_usage_event: Mapping[str, Any]
    provider_usage_record: Mapping[str, Any]
    egress_handoff: Mapping[str, Any]
    session_id: str
    measurement_id: str
    runtime_profile_id: str = RUNTIME_PROFILE_ID
    authority_effect: str = "NONE"
    credential_material_present: bool = False

    @property
    def response_hash(self) -> str:
        return self.broker.response.response_hash


@dataclass(frozen=True)
class OpenAITVCRuntimeEgressAdmission:
    transition_id: str
    response_hash: str
    egress_receipt_hash: str
    runtime_profile_id: str = RUNTIME_PROFILE_ID
    state: str = "EGRESS_ADMITTED"
    transition_authority: str = "Interlock/InTr"
    authority_effect: str = "NONE_LOCAL"

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def execute_governed_openai_via_tvc_runtime(request: ProviderRequest, *, session_id: str, transition_id: str, measurement_id: str, ingress_disposition: str, ingress_receipt_hash: str, carrier_ref: str, lease_receipt: Mapping[str, Any], broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]], usage_submitter: Callable[[dict[str, Any]], dict[str, Any]] = record_provider_usage_event_locally, max_output_tokens: int = 2048, response_format: str = "text") -> OpenAITVCRuntimeExecution:
    for label, value in (("session_id", session_id), ("transition_id", transition_id), ("measurement_id", measurement_id)):
        if not isinstance(value, str) or not value.strip():
            raise OpenAITVCRuntimeExecutionError(f"{label}_required")
    envelope = build_openai_intr_envelope(request, transition_id=transition_id, ingress_disposition=ingress_disposition, ingress_receipt_hash=ingress_receipt_hash, carrier_ref=carrier_ref)
    broker = execute_openai_via_tvc_broker(envelope, request, lease_receipt=lease_receipt, broker_submitter=broker_submitter, max_output_tokens=max_output_tokens, response_format=response_format)
    usage_map = broker.response.metadata.get("usage") or {}
    source_ref = f"openai:tvc:{envelope.transport_id}"
    event = build_provider_usage_event(
        measurement_id=measurement_id, session_id=session_id, transition_id=transition_id,
        origin_entry_point="intr", interaction_type="governed_openai_inference", provider="openai",
        model=broker.response.model,
        metrics={key: _metric(usage_map.get(key), source_ref) for key in USAGE_KEYS},
        receipt_refs=[ingress_receipt_hash, envelope.envelope_hash, broker.response.response_hash],
    )
    usage_record = record_usage_non_gating(usage_submitter, event)
    if usage_record.get("authority_effect") not in (None, "NONE"):
        raise OpenAITVCRuntimeExecutionError("provider_usage_record_authority_escalation")
    for key in ("authority_granted", "grants_authority", "assumes_governance"):
        if usage_record.get(key):
            raise OpenAITVCRuntimeExecutionError(f"provider_usage_record_authority_escalation:{key}")
    handoff = {
        "schema": "stegverse.llm_adapter.openai_tvc_runtime_egress_handoff/v1",
        "runtime_profile_id": RUNTIME_PROFILE_ID, "protocol_version": envelope.protocol_version,
        "transport_id": envelope.transport_id, "transition_id": envelope.transition_id,
        "request_hash": envelope.request_hash, "ingress_receipt_hash": envelope.ingress_receipt_hash,
        "envelope_hash": envelope.envelope_hash, "response_hash": broker.response.response_hash,
        "tvc_use_receipt_hash": broker.response.metadata["tvc_use_receipt_hash"],
        # S1 attribution: the model asked for and the model the provider reported serving.
        "requested_model": broker.response.model,
        "runtime_model": broker.response.metadata["runtime_model"],
        "usage_measured": broker.response.metadata["usage_measured"],
        "provider_usage_event_sha256": event["event_sha256"],
        "provider_usage_record_status": usage_record.get("status"),
        "requested_disposition": "ALLOW", "egress_intr_required": True,
        "credential_material_present": False, "authority_effect": "NONE",
    }
    return OpenAITVCRuntimeExecution(envelope=envelope, broker=broker, provider_usage_event=event, provider_usage_record=dict(usage_record), egress_handoff=handoff, session_id=session_id, measurement_id=measurement_id)


def admit_openai_tvc_runtime_egress(execution: OpenAITVCRuntimeExecution, *, egress_disposition: str, egress_receipt_hash: str, admitted_response_hash: str) -> OpenAITVCRuntimeEgressAdmission:
    if egress_disposition != "ALLOW":
        raise OpenAITVCRuntimeExecutionError("OpenAI provider output requires egress InTr ALLOW")
    if not _SHA256_RE.fullmatch(egress_receipt_hash):
        raise OpenAITVCRuntimeExecutionError("egress_receipt_hash must be lowercase sha256")
    if admitted_response_hash != execution.response_hash:
        raise OpenAITVCRuntimeExecutionError("egress response hash mismatch")
    handoff = execution.egress_handoff
    if handoff.get("response_hash") != execution.response_hash or handoff.get("egress_intr_required") is not True or handoff.get("authority_effect") != "NONE":
        raise OpenAITVCRuntimeExecutionError("egress handoff binding invalid")
    return OpenAITVCRuntimeEgressAdmission(transition_id=execution.envelope.transition_id, response_hash=execution.response_hash, egress_receipt_hash=egress_receipt_hash)


__all__ = ["OpenAITVCRuntimeExecutionError", "OpenAITVCRuntimeExecution", "OpenAITVCRuntimeEgressAdmission",
           "execute_governed_openai_via_tvc_runtime", "admit_openai_tvc_runtime_egress"]
