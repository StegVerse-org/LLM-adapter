"""Canonical Kimi runtime composition with separate InTr and Governance evidence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .kimi_governed_admission import GovernedKimiAdmission, build_governed_kimi_admission, validate_governed_kimi_admission
from .kimi_tvc_runtime_executor import KimiTVCRuntimeExecution, execute_governed_kimi_via_tvc_runtime
from .master_records_usage_submission import submit_provider_usage_to_master_records
from .provider_request import ProviderRequest


@dataclass(frozen=True)
class CanonicalKimiRuntimeExecution:
    admission: GovernedKimiAdmission
    execution: KimiTVCRuntimeExecution
    egress_handoff: Mapping[str, Any]
    authority_effect: str = "NONE"


def execute_canonical_kimi_via_tvc_runtime(
    request: ProviderRequest,
    *,
    session_id: str,
    transition_id: str,
    measurement_id: str,
    ingress_transport_state: str,
    ingress_receipt_hash: str,
    governance_disposition: str,
    governance_receipt_hash: str,
    carrier_ref: str,
    lease_receipt: Mapping[str, Any],
    broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    usage_submitter: Callable[[dict[str, Any]], dict[str, Any]] = submit_provider_usage_to_master_records,
    max_output_tokens: int = 2048,
    response_format: str = "text",
) -> CanonicalKimiRuntimeExecution:
    admission = build_governed_kimi_admission(
        request,
        transition_id=transition_id,
        ingress_transport_state=ingress_transport_state,
        ingress_receipt_hash=ingress_receipt_hash,
        governance_disposition=governance_disposition,
        governance_receipt_hash=governance_receipt_hash,
        carrier_ref=carrier_ref,
    )
    validate_governed_kimi_admission(admission)
    execution = execute_governed_kimi_via_tvc_runtime(
        request,
        session_id=session_id,
        transition_id=transition_id,
        measurement_id=measurement_id,
        # Compatibility API: this value is the validated Governance decision,
        # never a claim that Universal InTr itself granted ALLOW.
        ingress_disposition=governance_disposition,
        ingress_receipt_hash=ingress_receipt_hash,
        carrier_ref=carrier_ref,
        lease_receipt=lease_receipt,
        broker_submitter=broker_submitter,
        usage_submitter=usage_submitter,
        max_output_tokens=max_output_tokens,
        response_format=response_format,
    )
    if execution.envelope.request_hash != admission.envelope.request_hash or execution.envelope.transport_id != admission.envelope.transport_id:
        raise RuntimeError("canonical Kimi admission/execution envelope mismatch")
    custody = execution.master_records_usage
    if (
        not isinstance(custody, Mapping)
        or custody.get("status") != "CUSTODY_RECORDED"
        or custody.get("custody_recorded") is not True
        or custody.get("authority_granted") is not False
    ):
        raise RuntimeError("canonical Kimi egress requires authentic Master Records custody")
    handoff = {
        **dict(execution.egress_handoff),
        "schema": "stegverse.llm_adapter.kimi_canonical_runtime_egress_handoff/v1",
        "ingress_transport_state": ingress_transport_state,
        "governance_disposition": governance_disposition,
        "governance_receipt_hash": governance_receipt_hash,
        "master_records_usage_status": "CUSTODY_RECORDED",
        "master_records_custody_recorded": True,
        "transport_grants_execution_authority": False,
        "governance_grants_execution_authority": False,
        "governance_grants_credential_authority": False,
        "provider_operation_authority": "TV/TVC",
        "authority_effect": "NONE",
    }
    return CanonicalKimiRuntimeExecution(admission=admission, execution=execution, egress_handoff=handoff)


__all__ = ["CanonicalKimiRuntimeExecution", "execute_canonical_kimi_via_tvc_runtime"]
