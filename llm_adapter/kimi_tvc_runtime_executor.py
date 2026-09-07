"""Governed Kimi execution through the canonical runtime-profile/TVC broker path."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .kimi_intr_transport import KimiInTrEnvelope, build_kimi_intr_envelope
from .kimi_tvc_broker import RUNTIME_PROFILE_ID, KimiTVCBrokerResult, execute_kimi_via_tvc_broker
from .master_records_usage_submission import submit_provider_usage_to_master_records
from .provider_request import ProviderRequest
from .provider_usage import ProviderMetric, build_provider_usage_event


class KimiTVCRuntimeExecutionError(RuntimeError):
    pass


def _metric(value: Any, source_ref: str) -> ProviderMetric:
    if isinstance(value, bool):
        value = None
    if isinstance(value, (int, float)):
        return ProviderMetric(value=str(value), unit="tokens", evidence_class="MEASURED", source_ref=source_ref)
    return ProviderMetric(value=None, unit="tokens", evidence_class="UNAVAILABLE", source_ref=source_ref)


@dataclass(frozen=True)
class KimiTVCRuntimeExecution:
    envelope: KimiInTrEnvelope
    broker: KimiTVCBrokerResult
    provider_usage_event: Mapping[str, Any]
    master_records_usage: Mapping[str, Any]
    egress_handoff: Mapping[str, Any]
    session_id: str
    measurement_id: str
    runtime_profile_id: str = RUNTIME_PROFILE_ID
    authority_effect: str = "NONE"
    credential_material_present: bool = False

    @property
    def response_hash(self) -> str:
        return self.broker.response.response_hash


def execute_governed_kimi_via_tvc_runtime(
    request: ProviderRequest,
    *,
    session_id: str,
    transition_id: str,
    measurement_id: str,
    ingress_disposition: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    lease_receipt: Mapping[str, Any],
    broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    usage_submitter: Callable[[dict[str, Any]], dict[str, Any]] = submit_provider_usage_to_master_records,
    max_output_tokens: int = 2048,
    response_format: str = "text",
    admitted_envelope: KimiInTrEnvelope | None = None,
) -> KimiTVCRuntimeExecution:
    for label, value in (("session_id", session_id), ("transition_id", transition_id), ("measurement_id", measurement_id)):
        if not isinstance(value, str) or not value.strip():
            raise KimiTVCRuntimeExecutionError(f"{label}_required")

    envelope = admitted_envelope or build_kimi_intr_envelope(
        request,
        transition_id=transition_id,
        ingress_disposition=ingress_disposition,
        ingress_receipt_hash=ingress_receipt_hash,
        carrier_ref=carrier_ref,
    )
    if admitted_envelope is not None:
        if (
            envelope.transition_id != transition_id
            or envelope.ingress_receipt_hash != ingress_receipt_hash
            or envelope.carrier_ref != carrier_ref
            or envelope.provider != "kimi"
            or envelope.model != request.model
            or envelope.authority_effect != "NONE"
            or envelope.egress_intr_required is not True
            or envelope.credential_material_present is not False
        ):
            raise KimiTVCRuntimeExecutionError("admitted Kimi envelope binding mismatch")
    broker = execute_kimi_via_tvc_broker(
        envelope,
        request,
        lease_receipt=lease_receipt,
        broker_submitter=broker_submitter,
        max_output_tokens=max_output_tokens,
        response_format=response_format,
    )
    usage = broker.response.metadata.get("usage")
    usage_map = usage if isinstance(usage, Mapping) else {}
    source_ref = f"kimi:tvc:{envelope.transport_id}"
    event = build_provider_usage_event(
        measurement_id=measurement_id,
        session_id=session_id,
        transition_id=transition_id,
        origin_entry_point="intr",
        interaction_type="governed_kimi_inference",
        provider="kimi",
        model=broker.response.model,
        metrics={
            "prompt_tokens": _metric(usage_map.get("prompt_tokens"), source_ref),
            "completion_tokens": _metric(usage_map.get("completion_tokens"), source_ref),
            "total_tokens": _metric(usage_map.get("total_tokens"), source_ref),
        },
        receipt_refs=[ingress_receipt_hash, envelope.envelope_hash, broker.response.response_hash],
    )
    custody = usage_submitter(event)
    if not isinstance(custody, Mapping):
        raise KimiTVCRuntimeExecutionError("master_records_usage_reply_malformed")
    if custody.get("authority_effect") not in (None, "NONE"):
        raise KimiTVCRuntimeExecutionError("master_records_usage_authority_escalation")
    for key in ("authority_granted", "grants_authority", "assumes_governance"):
        if custody.get(key):
            raise KimiTVCRuntimeExecutionError(f"master_records_usage_authority_escalation:{key}")

    egress_handoff = {
        "schema": "stegverse.llm_adapter.kimi_tvc_runtime_egress_handoff/v1",
        "runtime_profile_id": RUNTIME_PROFILE_ID,
        "protocol_version": envelope.protocol_version,
        "transport_id": envelope.transport_id,
        "transition_id": envelope.transition_id,
        "request_hash": envelope.request_hash,
        "ingress_receipt_hash": envelope.ingress_receipt_hash,
        "envelope_hash": envelope.envelope_hash,
        "response_hash": broker.response.response_hash,
        "tvc_use_receipt_hash": broker.response.metadata["tvc_use_receipt_hash"],
        "provider_usage_event_sha256": event["event_sha256"],
        "master_records_usage_status": custody.get("status"),
        "requested_disposition": "ALLOW",
        "egress_intr_required": True,
        "credential_material_present": False,
        "authority_effect": "NONE",
    }
    return KimiTVCRuntimeExecution(
        envelope=envelope,
        broker=broker,
        provider_usage_event=event,
        master_records_usage=dict(custody),
        egress_handoff=egress_handoff,
        session_id=session_id,
        measurement_id=measurement_id,
    )


__all__ = [
    "KimiTVCRuntimeExecutionError", "KimiTVCRuntimeExecution",
    "execute_governed_kimi_via_tvc_runtime",
]
