"""Governed execution wrapper for optional Kimi/Moonshot InTr transport.

Ingress/egress decisions are externally produced by Interlock/InTr. This module
reuses canonical provider-usage and Master Records submission paths and grants no
authority itself. Production runtime-profile execution uses the TVC broker bridge.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .kimi_intr_transport import (
    KIMI_BASE_URL,
    KimiHTTPTransport,
    KimiInTrEnvelope,
    KimiTransportAdmissionError,
    KimiTransportResult,
    build_kimi_intr_envelope,
)
from .master_records_usage_submission import submit_provider_usage_to_master_records
from .provider_request import ProviderRequest
from .provider_usage import ProviderMetric, build_provider_usage_event

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class KimiExecutionError(RuntimeError):
    """Fail-closed governed Kimi execution error."""


@dataclass(frozen=True)
class KimiGovernedExecution:
    envelope: KimiInTrEnvelope
    transport: KimiTransportResult
    provider_usage_event: Mapping[str, Any]
    master_records_usage: Mapping[str, Any]
    session_id: str
    measurement_id: str
    egress_handoff: Mapping[str, Any]
    authority_effect: str = "NONE"
    egress_intr_required: bool = True

    @property
    def response_hash(self) -> str:
        return str(self.transport.evidence()["response_hash"])

    def evidence(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.llm_adapter.kimi_governed_execution/v1",
            "protocol_version": self.envelope.protocol_version,
            "session_id": self.session_id,
            "transition_id": self.envelope.transition_id,
            "measurement_id": self.measurement_id,
            "transport_id": self.envelope.transport_id,
            "request_hash": self.envelope.request_hash,
            "provider_request_hash": self.transport.provider_request_hash,
            "response_hash": self.response_hash,
            "ingress_receipt_hash": self.envelope.ingress_receipt_hash,
            "provider_usage_event_sha256": self.provider_usage_event["event_sha256"],
            "master_records_usage_status": self.master_records_usage.get("status"),
            "provider_usage_custody_recorded": self.master_records_usage.get("custody_recorded") is True,
            "credential_authority": "TV/TVC",
            "credential_material_present": False,
            "egress_intr_required": True,
            "authority_effect": "NONE",
        }


@dataclass(frozen=True)
class KimiEgressAdmission:
    transition_id: str
    response_hash: str
    egress_receipt_hash: str
    state: str = "EGRESS_ADMITTED"
    transition_authority: str = "Interlock/InTr"
    authority_effect: str = "NONE_LOCAL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.llm_adapter.kimi_egress_admission/v1",
            "transition_id": self.transition_id,
            "response_hash": self.response_hash,
            "egress_receipt_hash": self.egress_receipt_hash,
            "state": self.state,
            "transition_authority": self.transition_authority,
            "authority_effect": self.authority_effect,
        }


def _metric(value: Any, *, source_ref: str) -> ProviderMetric:
    if isinstance(value, bool):
        value = None
    if isinstance(value, (int, float)):
        return ProviderMetric(value=str(value), unit="tokens", evidence_class="MEASURED", source_ref=source_ref)
    return ProviderMetric(value=None, unit="tokens", evidence_class="UNAVAILABLE", source_ref=source_ref)


def _verify_custody_reply(reply: Mapping[str, Any]) -> None:
    for key in ("authority_granted", "grants_authority", "assumes_governance"):
        if reply.get(key):
            raise KimiExecutionError(f"master_records_usage_authority_escalation:{key}")
    effect = reply.get("authority_effect")
    if effect is not None and effect != "NONE":
        raise KimiExecutionError("master_records_usage_authority_escalation:authority_effect")


def execute_governed_kimi(
    request: ProviderRequest,
    *,
    session_id: str,
    transition_id: str,
    measurement_id: str,
    ingress_disposition: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    credential_resolver: Callable[[], str],
    transport_factory: Callable[..., KimiHTTPTransport] = KimiHTTPTransport,
    usage_submitter: Callable[[dict[str, Any]], dict[str, Any]] = submit_provider_usage_to_master_records,
) -> KimiGovernedExecution:
    for label, value in (("session_id", session_id), ("transition_id", transition_id), ("measurement_id", measurement_id)):
        if not value.strip():
            raise KimiExecutionError(f"{label}_required")
    if not callable(credential_resolver):
        raise KimiExecutionError("credential_resolver_required")

    envelope = build_kimi_intr_envelope(
        request,
        transition_id=transition_id,
        ingress_disposition=ingress_disposition,
        ingress_receipt_hash=ingress_receipt_hash,
        carrier_ref=carrier_ref,
    )
    transport = transport_factory(credential_resolver=credential_resolver, base_url=KIMI_BASE_URL)
    transport_result = transport.complete(envelope, request)

    usage = transport_result.response.metadata.get("usage")
    usage_map = usage if isinstance(usage, Mapping) else {}
    source_ref = f"kimi:{envelope.transport_id}"
    event = build_provider_usage_event(
        measurement_id=measurement_id,
        session_id=session_id,
        transition_id=transition_id,
        origin_entry_point="intr",
        interaction_type="governed_kimi_inference",
        provider="kimi",
        model=transport_result.response.model,
        metrics={
            "prompt_tokens": _metric(usage_map.get("prompt_tokens"), source_ref=source_ref),
            "completion_tokens": _metric(usage_map.get("completion_tokens"), source_ref=source_ref),
            "total_tokens": _metric(usage_map.get("total_tokens"), source_ref=source_ref),
        },
        receipt_refs=[ingress_receipt_hash, envelope.envelope_hash, transport_result.evidence()["response_hash"]],
    )
    master_records_usage = usage_submitter(event)
    if not isinstance(master_records_usage, Mapping):
        raise KimiExecutionError("master_records_usage_reply_malformed")
    _verify_custody_reply(master_records_usage)

    egress_handoff = {
        "schema": "stegverse.llm_adapter.kimi_egress_handoff/v1",
        "protocol_version": envelope.protocol_version,
        "transport_id": envelope.transport_id,
        "transition_id": envelope.transition_id,
        "request_hash": envelope.request_hash,
        "provider_request_hash": transport_result.provider_request_hash,
        "ingress_receipt_hash": envelope.ingress_receipt_hash,
        "envelope_hash": envelope.envelope_hash,
        "response_hash": transport_result.evidence()["response_hash"],
        "provider_usage_event_sha256": event["event_sha256"],
        "master_records_usage_status": master_records_usage.get("status"),
        "requested_disposition": "ALLOW",
        "egress_intr_required": True,
        "authority_effect": "NONE",
        "credential_material_present": False,
    }
    return KimiGovernedExecution(
        envelope=envelope,
        transport=transport_result,
        provider_usage_event=event,
        master_records_usage=master_records_usage,
        session_id=session_id,
        measurement_id=measurement_id,
        egress_handoff=egress_handoff,
    )


def admit_kimi_egress(
    execution: KimiGovernedExecution,
    *,
    egress_disposition: str,
    egress_receipt_hash: str,
    admitted_response_hash: str,
) -> KimiEgressAdmission:
    if egress_disposition != "ALLOW":
        raise KimiTransportAdmissionError("Kimi provider output requires egress InTr ALLOW")
    if not _SHA256_RE.fullmatch(egress_receipt_hash):
        raise KimiTransportAdmissionError("egress_receipt_hash must be an exact lowercase sha256")
    if admitted_response_hash != execution.response_hash:
        raise KimiTransportAdmissionError("egress InTr response hash does not match exact provider response")
    return KimiEgressAdmission(
        transition_id=execution.envelope.transition_id,
        response_hash=execution.response_hash,
        egress_receipt_hash=egress_receipt_hash,
    )


__all__ = [
    "KimiExecutionError", "KimiGovernedExecution", "KimiEgressAdmission",
    "execute_governed_kimi", "admit_kimi_egress",
]
