"""Explicit canonical admission boundary for hosted Kimi provider operations.

Universal InTr proves exact-packet transport only. StegCore/Governance provides
ALLOW/DENY/FAIL-CLOSED separately. Neither grants provider-operation or
credential authority; a valid TVC lease remains mandatory for the consequence.

Canonical production request identity is the exact non-secret JSON payload the
TVC vault broker will serialize to Moonshot, not the legacy direct-client wire.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from .kimi_intr_transport import KimiInTrEnvelope, KimiTransportAdmissionError, KimiTransportConfigurationError, PROTOCOL_VERSION
from .kimi_tvc_provider_wire import canonical_kimi_tvc_provider_request_hash
from .provider_request import ProviderRequest, stable_hash

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class GovernedKimiAdmission:
    envelope: KimiInTrEnvelope
    ingress_transport_state: str
    ingress_receipt_hash: str
    governance_disposition: str
    governance_receipt_hash: str
    provider_wire_profile: str = "tvc_openai_chat_completions_v1"
    governance_authority: str = "StegCore"
    provider_operation_authority: str = "TV/TVC"
    authority_effect: str = "NONE"

    def evidence(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.llm_adapter.kimi_governed_admission/v1",
            "transport_id": self.envelope.transport_id,
            "transition_id": self.envelope.transition_id,
            "request_hash": self.envelope.request_hash,
            "provider_wire_profile": self.provider_wire_profile,
            "ingress_transport_state": self.ingress_transport_state,
            "ingress_receipt_hash": self.ingress_receipt_hash,
            "governance_disposition": self.governance_disposition,
            "governance_receipt_hash": self.governance_receipt_hash,
            "governance_authority": self.governance_authority,
            "provider_operation_authority": self.provider_operation_authority,
            "credential_authority": "TV/TVC",
            "transport_grants_execution_authority": False,
            "governance_grants_execution_authority": False,
            "governance_grants_credential_authority": False,
            "tvc_lease_required": True,
            "authority_effect": "NONE",
        }


def _exact_sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise KimiTransportAdmissionError(f"{label} must be an exact lowercase sha256")
    return value


def build_governed_kimi_admission(
    request: ProviderRequest,
    *,
    transition_id: str,
    ingress_transport_state: str,
    ingress_receipt_hash: str,
    governance_disposition: str,
    governance_receipt_hash: str,
    carrier_ref: str,
    max_output_tokens: int = 2048,
    response_format: str = "text",
    endpoint_profile: str = "moonshot_openai_compatible",
    credential_class: str = "TV_TVC_PROVIDER_SECRET",
) -> GovernedKimiAdmission:
    if ingress_transport_state != "TRANSPORT_COMPLETE":
        raise KimiTransportAdmissionError("Kimi provider operation requires canonical InTr TRANSPORT_COMPLETE evidence")
    _exact_sha256(ingress_receipt_hash, "ingress_receipt_hash")
    if governance_disposition != "ALLOW":
        raise KimiTransportAdmissionError("Kimi provider operation requires a separate contemporaneous Governance ALLOW")
    _exact_sha256(governance_receipt_hash, "governance_receipt_hash")
    if not transition_id.strip() or not carrier_ref.strip():
        raise KimiTransportAdmissionError("transition_id and carrier_ref are required")
    if endpoint_profile != "moonshot_openai_compatible":
        raise KimiTransportConfigurationError("unsupported Kimi endpoint profile")
    if credential_class != "TV_TVC_PROVIDER_SECRET":
        raise KimiTransportAdmissionError("hosted Kimi credentials must remain under TV/TVC authority")

    wire_hash = canonical_kimi_tvc_provider_request_hash(
        request,
        max_output_tokens=max_output_tokens,
        response_format=response_format,
    )
    transport_id = "kmit-" + stable_hash({
        "protocol_version": PROTOCOL_VERSION,
        "transition_id": transition_id,
        "request_hash": wire_hash,
        "ingress_receipt_hash": ingress_receipt_hash,
        "carrier_ref": carrier_ref,
        "endpoint_profile": endpoint_profile,
        "provider_wire_profile": "tvc_openai_chat_completions_v1",
    })
    envelope = KimiInTrEnvelope(
        protocol_version=PROTOCOL_VERSION,
        transport_id=transport_id,
        transition_id=transition_id,
        request_hash=wire_hash,
        provider="kimi",
        model=request.model,
        endpoint_profile=endpoint_profile,
        ingress_receipt_hash=ingress_receipt_hash,
        credential_authority="TV/TVC",
        credential_class=credential_class,
        carrier_ref=carrier_ref,
    )
    return GovernedKimiAdmission(
        envelope=envelope,
        ingress_transport_state=ingress_transport_state,
        ingress_receipt_hash=ingress_receipt_hash,
        governance_disposition=governance_disposition,
        governance_receipt_hash=governance_receipt_hash,
    )


def validate_governed_kimi_admission(value: GovernedKimiAdmission | Mapping[str, Any]) -> None:
    evidence = value.evidence() if isinstance(value, GovernedKimiAdmission) else dict(value)
    required = {
        "provider_wire_profile": "tvc_openai_chat_completions_v1",
        "ingress_transport_state": "TRANSPORT_COMPLETE",
        "governance_disposition": "ALLOW",
        "governance_authority": "StegCore",
        "provider_operation_authority": "TV/TVC",
        "credential_authority": "TV/TVC",
        "transport_grants_execution_authority": False,
        "governance_grants_execution_authority": False,
        "governance_grants_credential_authority": False,
        "tvc_lease_required": True,
        "authority_effect": "NONE",
    }
    for key, expected in required.items():
        if evidence.get(key) != expected:
            raise KimiTransportAdmissionError(f"governed Kimi admission boundary mismatch: {key}")
    _exact_sha256(str(evidence.get("ingress_receipt_hash") or ""), "ingress_receipt_hash")
    _exact_sha256(str(evidence.get("governance_receipt_hash") or ""), "governance_receipt_hash")


__all__ = ["GovernedKimiAdmission", "build_governed_kimi_admission", "validate_governed_kimi_admission"]
