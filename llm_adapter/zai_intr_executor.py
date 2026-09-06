"""Governed execution wrapper for the Z.ai Interlock/InTr transport.

This module binds the optional Z.ai transport to the existing provider-usage and
Master Records evidence path. It does not evaluate governance itself. Ingress and
egress decisions are supplied as already-observed Interlock/InTr evidence and are
validated fail-closed against the exact wire request/response hashes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .master_records_usage_submission import submit_provider_usage_to_master_records
from .provider_request import ProviderRequest
from .provider_usage import ProviderMetric, build_provider_usage_event
from .zai_intr_transport import (
    ZAI_CODING_BASE_URL,
    ZAI_GENERAL_BASE_URL,
    ZAIHTTPTransport,
    ZAIInTrEnvelope,
    ZAITransportAdmissionError,
    ZAITransportResult,
    assert_no_secret_material,
    build_zai_intr_envelope,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ZAIExecutionError(RuntimeError):
    """Fail-closed governed Z.ai execution error."""


@dataclass(frozen=True)
class ZAIGovernedExecution:
    envelope: ZAIInTrEnvelope
    transport: ZAITransportResult
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
        transport_evidence = self.transport.evidence()
        return {
            "schema": "stegverse.llm_adapter.zai_governed_execution/v1",
            "protocol_version": self.envelope.protocol_version,
            "session_id": self.session_id,
            "transition_id": self.envelope.transition_id,
            "measurement_id": self.measurement_id,
            "transport_id": self.envelope.transport_id,
            "request_hash": self.envelope.request_hash,
            "provider_request_hash": self.transport.provider_request_hash,
            "response_hash": transport_evidence["response_hash"],
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
class ZAIEgressAdmission:
    transition_id: str
    response_hash: str
    egress_receipt_hash: str
    state: str = "EGRESS_ADMITTED"
    transition_authority: str = "Interlock/InTr"
    authority_effect: str = "NONE_LOCAL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.llm_adapter.zai_egress_admission/v1",
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
            raise ZAIExecutionError(f"master_records_usage_authority_escalation:{key}")
    effect = reply.get("authority_effect")
    if effect is not None and effect != "NONE":
        raise ZAIExecutionError("master_records_usage_authority_escalation:authority_effect")


def execute_governed_zai(
    request: ProviderRequest,
    *,
    session_id: str,
    transition_id: str,
    measurement_id: str,
    ingress_disposition: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    credential_resolver: Callable[[], str],
    endpoint_profile: str = "general",
    transport_factory: Callable[..., ZAIHTTPTransport] = ZAIHTTPTransport,
    usage_submitter: Callable[[dict[str, Any]], dict[str, Any]] = submit_provider_usage_to_master_records,
) -> ZAIGovernedExecution:
    """Execute one exact ingress-admitted Z.ai wire request and preserve evidence."""

    for label, value in (("session_id", session_id), ("transition_id", transition_id), ("measurement_id", measurement_id)):
        if not value.strip():
            raise ZAIExecutionError(f"{label}_required")
    if not callable(credential_resolver):
        raise ZAIExecutionError("credential_resolver_required")

    envelope = build_zai_intr_envelope(
        request,
        transition_id=transition_id,
        ingress_disposition=ingress_disposition,
        ingress_receipt_hash=ingress_receipt_hash,
        carrier_ref=carrier_ref,
        endpoint_profile=endpoint_profile,
    )
    base_url = ZAI_CODING_BASE_URL if endpoint_profile == "coding" else ZAI_GENERAL_BASE_URL
    transport = transport_factory(credential_resolver=credential_resolver, base_url=base_url)
    transport_result = transport.complete(envelope, request)

    usage = transport_result.response.metadata.get("usage")
    usage_map = usage if isinstance(usage, Mapping) else {}
    source_ref = f"zai:{envelope.transport_id}"
    event = build_provider_usage_event(
        measurement_id=measurement_id,
        session_id=session_id,
        transition_id=transition_id,
        origin_entry_point="intr",
        interaction_type="governed_zai_inference",
        provider="z.ai",
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
        raise ZAIExecutionError("master_records_usage_reply_malformed")
    _verify_custody_reply(master_records_usage)

    egress_handoff = {
        "schema": "stegverse.llm_adapter.zai_egress_handoff/v1",
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

    return ZAIGovernedExecution(
        envelope=envelope,
        transport=transport_result,
        provider_usage_event=event,
        master_records_usage=master_records_usage,
        session_id=session_id,
        measurement_id=measurement_id,
        egress_handoff=egress_handoff,
    )


def admit_zai_egress(
    execution: ZAIGovernedExecution,
    *,
    egress_disposition: str,
    egress_receipt_hash: str,
    admitted_response_hash: str,
) -> ZAIEgressAdmission:
    """Verify externally-produced egress InTr admission for the exact response."""

    if egress_disposition != "ALLOW":
        raise ZAITransportAdmissionError("Z.ai provider output requires egress InTr ALLOW")
    if not _SHA256_RE.fullmatch(egress_receipt_hash):
        raise ZAITransportAdmissionError("egress_receipt_hash must be an exact lowercase sha256")
    if admitted_response_hash != execution.response_hash:
        raise ZAITransportAdmissionError("egress InTr response hash does not match exact provider response")
    return ZAIEgressAdmission(
        transition_id=execution.envelope.transition_id,
        response_hash=execution.response_hash,
        egress_receipt_hash=egress_receipt_hash,
    )


__all__ = [
    "ZAIExecutionError",
    "ZAIGovernedExecution",
    "ZAIEgressAdmission",
    "execute_governed_zai",
    "admit_zai_egress",
]
