"""Explicit canonical admission boundary for hosted Kimi provider operations.

Universal InTr proves exact-packet transport only.  StegCore/Governance provides
ALLOW/DENY/FAIL-CLOSED separately.  Neither grants provider-operation or
credential authority; a valid TVC lease remains mandatory for the consequence.

The older ``build_kimi_intr_envelope(..., ingress_disposition=...)`` API is kept
as a compatibility surface.  Production composition should use this module so
TRANSPORT_COMPLETE cannot be confused with Governance ALLOW.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from .kimi_intr_transport import KimiInTrEnvelope, KimiTransportAdmissionError, build_kimi_intr_envelope
from .provider_request import ProviderRequest

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class GovernedKimiAdmission:
    envelope: KimiInTrEnvelope
    ingress_transport_state: str
    ingress_receipt_hash: str
    governance_disposition: str
    governance_receipt_hash: str
    governance_authority: str = "StegCore"
    provider_operation_authority: str = "TV/TVC"
    authority_effect: str = "NONE"

    def evidence(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.llm_adapter.kimi_governed_admission/v1",
            "transport_id": self.envelope.transport_id,
            "transition_id": self.envelope.transition_id,
            "request_hash": self.envelope.request_hash,
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
) -> GovernedKimiAdmission:
    if ingress_transport_state != "TRANSPORT_COMPLETE":
        raise KimiTransportAdmissionError("Kimi provider operation requires canonical InTr TRANSPORT_COMPLETE evidence")
    _exact_sha256(ingress_receipt_hash, "ingress_receipt_hash")
    if governance_disposition != "ALLOW":
        raise KimiTransportAdmissionError("Kimi provider operation requires a separate contemporaneous Governance ALLOW")
    _exact_sha256(governance_receipt_hash, "governance_receipt_hash")

    # The legacy envelope builder's `ingress_disposition` field predates the
    # canonical transport/governance separation.  Here the supplied ALLOW is
    # explicitly the already-validated Governance disposition, while
    # ingress_receipt_hash remains the exact Universal InTr transport receipt.
    envelope = build_kimi_intr_envelope(
        request,
        transition_id=transition_id,
        ingress_disposition=governance_disposition,
        ingress_receipt_hash=ingress_receipt_hash,
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
