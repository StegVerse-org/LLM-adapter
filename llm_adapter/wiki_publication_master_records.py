"""Organization transition receipt of a governed wiki-publication decision.

Interlock/InTr admits the publication transition. This module validates the
already-produced SDK and Interlock/InTr evidence and builds the one canonical
state-transition receipt the organization holds for it. The repository mutation
closes on that organization receipt, verified locally by
``verify_publication_transition_receipt``; nothing here waits on Master Records.

Master Records is the downstream recorder of released organization batch
receipts. ``record_governed_publication_closure`` may hand it a released receipt
for cross-organization reconstruction; that recording is optional, never gates
the publication, and reports a failure as a six-field non-ALLOW instead of
raising. It creates no governance, transition, credential, record, publication,
or execution authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Callable, Mapping

import requests

from llm_adapter.stegbrowser_master_records_state_transition_relay import (
    _configuration as _master_records_configuration,
    enabled as master_records_transport_enabled,
)

TASK_ID = "GOVERNED-WIKI-PUBLICATION-TRANSITION-001"
TRANSITION_ID = "PUBLIC_WIKI_GOVERNED_PUBLICATION_DECISION"
RECEIPT_SCHEMA = "stegverse.canonical-state-transition-receipt/v1"
SUBMISSION_SCHEMA = "stegverse.master-records.state-transition-submission/v1"
CLOSURE_SCHEMA = "stegverse.external-framework-wiki-publication-governed-closure/v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
OWNING_EXISTING_GOAL = "LLMA-DECLARED-PATH-CONFORMANCE-368"
RECORDING_RETRY_ENTRYPOINT = "llm_adapter.wiki_publication_master_records.record_governed_publication_closure"


class PublicationCustodyError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _evidence(transition_id: str, evidence_id: str, evidence_type: str, content: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(content)
    return {
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "origin_transition_id": transition_id,
        "encoding": "canonical-json",
        "sha256": canonical_sha256(body),
        "content": body,
    }


def _require_sha256(value: Any, label: str) -> str:
    text = str(value or "")
    if not SHA256.fullmatch(text):
        raise PublicationCustodyError(f"{label}_invalid")
    return text


def _validate_exact_bindings(
    *,
    publication_transition_id: str,
    publication_transition: Mapping[str, Any],
    sdk_manifest: Mapping[str, Any],
    governed_result: Mapping[str, Any],
    intr_allow_decision: Mapping[str, Any],
) -> dict[str, Any]:
    if not publication_transition_id:
        raise PublicationCustodyError("publication_transition_id_required")
    transition = dict(publication_transition)
    if transition.get("transition_type") != "external_framework_wiki_publication_transition":
        raise PublicationCustodyError("publication_transition_type_invalid")
    if transition.get("decision") != "ALLOW_PUBLICATION_CANDIDATE":
        raise PublicationCustodyError("publication_transition_not_allow_candidate")
    if transition.get("publication_executed") is not False:
        raise PublicationCustodyError("publication_transition_execution_boundary_invalid")

    transition_sha = canonical_sha256(transition)
    manifest = dict(sdk_manifest)
    if manifest.get("payload") != transition:
        raise PublicationCustodyError("sdk_manifest_publication_payload_mismatch")
    if manifest.get("source_output_id") != transition_sha:
        raise PublicationCustodyError("sdk_manifest_source_output_identity_mismatch")
    candidate = manifest.get("candidate")
    params = candidate.get("parameters") if isinstance(candidate, Mapping) else None
    if not isinstance(params, Mapping):
        raise PublicationCustodyError("sdk_manifest_publication_candidate_missing")
    exact = {
        "publication_transition_sha256": transition_sha,
        "package_id": transition.get("package_id"),
        "correction_receipt_id": transition.get("correction_receipt_id"),
        "publisher_ref": transition.get("publisher_ref"),
        "source_commit_ref": transition.get("source_commit_ref"),
        "target_repository": "StegVerse-Labs/admissibility-wiki",
        "target_path": transition.get("target_path"),
        "decision": "ALLOW_PUBLICATION_CANDIDATE",
        "publication_executed": False,
    }
    for key, expected in exact.items():
        if params.get(key) != expected:
            raise PublicationCustodyError(f"sdk_manifest_candidate_binding_mismatch:{key}")
    if list(params.get("evidence_references") or []) != list(transition.get("evidence_references") or []):
        raise PublicationCustodyError("sdk_manifest_evidence_binding_mismatch")
    completion = manifest.get("completion")
    egress = completion.get("egress") if isinstance(completion, Mapping) else None
    if not isinstance(egress, Mapping) or egress.get("transport") != "INTERLOCK_INTR":
        raise PublicationCustodyError("sdk_manifest_intr_completion_binding_missing")

    governed = dict(governed_result)
    if governed.get("governance_state") != "ALLOW":
        raise PublicationCustodyError("sdk_governance_did_not_allow_publication")
    if governed.get("posture_bound_execution") is not True:
        raise PublicationCustodyError("sdk_execution_not_intr_posture_bound")
    if governed.get("chain_verified") is not True:
        raise PublicationCustodyError("sdk_governed_chain_not_verified")
    manifest_receipt_id = str(governed.get("manifest_receipt_id") or "")
    if not manifest_receipt_id.startswith("MR-"):
        raise PublicationCustodyError("sdk_manifest_receipt_missing")
    posture = governed.get("intr_security_posture_binding")
    if not isinstance(posture, Mapping):
        raise PublicationCustodyError("intr_posture_binding_missing")
    if posture.get("schema") != "stegverse.sdk.intr-posture-runtime-binding.v1":
        raise PublicationCustodyError("intr_posture_binding_schema_invalid")
    if posture.get("task_id") != TASK_ID or posture.get("resolution_authority") != "INTERLOCK_INTR":
        raise PublicationCustodyError("intr_posture_binding_authority_invalid")
    if posture.get("payload_sha256") != f"sha256:{transition_sha}":
        raise PublicationCustodyError("intr_posture_payload_binding_mismatch")
    transition_request_uri = str(posture.get("transition_request_sha256") or "")
    if not transition_request_uri.startswith("sha256:"):
        raise PublicationCustodyError("intr_transition_request_binding_missing")
    transition_request_sha = _require_sha256(transition_request_uri.split(":", 1)[1], "intr_transition_request_sha256")

    decision = dict(intr_allow_decision)
    if decision.get("disposition") != "ALLOW" or decision.get("authority") != "Interlock/InTr":
        raise PublicationCustodyError("external_intr_allow_required")
    if decision.get("locally_generated_allow") is not False:
        raise PublicationCustodyError("locally_generated_intr_allow_rejected")
    if decision.get("request_hash") != transition_request_sha:
        raise PublicationCustodyError("intr_allow_request_hash_mismatch")
    request_id = str(governed.get("request_id") or "")
    if not request_id or decision.get("transition_id") != request_id:
        raise PublicationCustodyError("intr_allow_transition_identity_mismatch")
    ingress_receipt_hash = _require_sha256(decision.get("ingress_receipt_hash"), "intr_ingress_receipt_hash")
    if not isinstance(decision.get("carrier_ref"), str) or not decision["carrier_ref"]:
        raise PublicationCustodyError("intr_allow_carrier_ref_missing")

    return {
        "publication_transition_sha256": transition_sha,
        "sdk_manifest_sha256": canonical_sha256(manifest),
        "sdk_governed_result_sha256": canonical_sha256(governed),
        "sdk_manifest_receipt_id": manifest_receipt_id,
        "sdk_request_id": request_id,
        "intr_transition_request_sha256": transition_request_sha,
        "intr_ingress_receipt_hash": ingress_receipt_hash,
        "intr_carrier_ref": decision["carrier_ref"],
        "target_repository": params["target_repository"],
        "target_path": params["target_path"],
    }


def build_publication_state_receipt(
    *,
    publication_transition_id: str,
    publication_transition: Mapping[str, Any],
    sdk_manifest: Mapping[str, Any],
    governed_result: Mapping[str, Any],
    intr_allow_decision: Mapping[str, Any],
    recorded_at: str | None = None,
) -> dict[str, Any]:
    bindings = _validate_exact_bindings(
        publication_transition_id=publication_transition_id,
        publication_transition=publication_transition,
        sdk_manifest=sdk_manifest,
        governed_result=governed_result,
        intr_allow_decision=intr_allow_decision,
    )
    evidence = [
        _evidence(TRANSITION_ID, "publication-transition-candidate", "PUBLICATION_TRANSITION_CANDIDATE", publication_transition),
        _evidence(TRANSITION_ID, "sdk-ingress-manifest", "SDK_INGRESS_MANIFEST", sdk_manifest),
        _evidence(TRANSITION_ID, "interlock-intr-allow", "INTERLOCK_INTR_ALLOW_DECISION", intr_allow_decision),
        _evidence(TRANSITION_ID, "sdk-governed-result", "SDK_GOVERNED_RESULT", governed_result),
    ]
    transition_evidence = {
        "canonical_task": TASK_ID,
        "publication_transition_id": publication_transition_id,
        **bindings,
        "intr_governance_decision": "ALLOW",
        "intr_decision_origin": "external_interlock_intr",
        "locally_generated_allow": False,
        "publication_mutation_executed": False,
    }
    return {
        "schema": RECEIPT_SCHEMA,
        "transition_id": TRANSITION_ID,
        "transition_sequence": 1,
        "subject_or_correlation_id": publication_transition_id,
        "prior_state_ref_or_hash": None,
        "resulting_state_ref_or_hash": "sha256:" + bindings["sdk_governed_result_sha256"],
        "governance_decision_ref_where_applicable": "sha256:" + bindings["intr_ingress_receipt_hash"],
        "transition_evidence": transition_evidence,
        "required_evidence_manifest": evidence,
        "recorded_at": recorded_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "transition_outcome": "ALLOW",
        "authority_effect": "NONE_STATE_RECEIPT_ONLY",
        "proof_scope": "THIS_TRANSITION_ONLY",
        "proof_ceiling": "OBSERVED_GOVERNED_PUBLICATION_DECISION_AND_CUSTODY_ONLY",
        "master_records_may_grant_transition_authority": False,
        "master_records_may_grant_execution_authority": False,
    }


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}


def _validate_recorded(response: Mapping[str, Any], receipt: Mapping[str, Any]) -> str:
    expected = canonical_sha256(receipt)
    if response.get("state") != "RECORDED":
        raise PublicationCustodyError("master_records_state_not_recorded")
    if response.get("reconstruction_status") != "PASS":
        raise PublicationCustodyError("master_records_reconstruction_not_pass")
    if response.get("required_evidence_validation_status") != "PASS":
        raise PublicationCustodyError("master_records_required_evidence_not_pass")
    if response.get("receipt_sha256") != expected or response.get("reconstructed_receipt_sha256") != expected:
        raise PublicationCustodyError("master_records_receipt_digest_mismatch")
    if response.get("master_records_grants_transition_authority") is not False:
        raise PublicationCustodyError("master_records_authority_escalation")
    return expected


def _validate_reconstruction(response: Mapping[str, Any], receipt_sha256: str, *, expected_receipt: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if response.get("state") != "PASS":
        raise PublicationCustodyError("master_records_retained_reconstruction_not_pass")
    if response.get("required_evidence_validation_status") != "PASS":
        raise PublicationCustodyError("master_records_retained_evidence_not_pass")
    if response.get("receipt_sha256") != receipt_sha256 or response.get("reconstructed_receipt_sha256") != receipt_sha256:
        raise PublicationCustodyError("master_records_retained_digest_mismatch")
    receipt = response.get("receipt")
    if not isinstance(receipt, Mapping):
        raise PublicationCustodyError("master_records_reconstructed_receipt_missing")
    if expected_receipt is not None and dict(receipt) != dict(expected_receipt):
        raise PublicationCustodyError("master_records_reconstructed_receipt_identity_mismatch")
    if response.get("master_records_grants_transition_authority") is not False:
        raise PublicationCustodyError("master_records_reconstruction_authority_escalation")
    return dict(receipt)


def _recording_not_completed(failure_code: str, receipt_sha256: str | None, **detail: Any) -> dict[str, Any]:
    """A downstream recording that did not complete, as six fields; never a gate."""
    return {
        "schema": CLOSURE_SCHEMA,
        "state": "NOT_RECORDED",
        "disposition": "NOT_RECORDED",
        "failure_code": failure_code,
        "failed_predicate": "master_records_downstream_recording_completed",
        "required_evidence_or_repair": "configure the Master Records recorder and resubmit the released organization receipt",
        "retry_entrypoint": RECORDING_RETRY_ENTRYPOINT,
        "owning_existing_goal": OWNING_EXISTING_GOAL,
        "next_attempt": "resubmit the released receipt downstream; the publication transition is already closed on the organization receipt",
        "receipt_sha256": receipt_sha256,
        "gates_publication": False,
        "master_records_grants_transition_authority": False,
        "authority_effect": "NONE",
        **detail,
    }


def record_governed_publication_closure(
    *,
    publication_transition_id: str,
    publication_transition: Mapping[str, Any],
    sdk_manifest: Mapping[str, Any],
    governed_result: Mapping[str, Any],
    intr_allow_decision: Mapping[str, Any],
    post: Callable[..., Any] = requests.post,
    get: Callable[..., Any] = requests.get,
) -> dict[str, Any]:
    """Hand the released organization receipt to Master Records downstream.

    Optional and non-gating: invalid transition evidence still raises, because no
    organization receipt exists, but every Master Records outcome is returned as
    data and never blocks or reverses the publication.
    """
    receipt = build_publication_state_receipt(
        publication_transition_id=publication_transition_id,
        publication_transition=publication_transition,
        sdk_manifest=sdk_manifest,
        governed_result=governed_result,
        intr_allow_decision=intr_allow_decision,
    )
    receipt_sha256 = canonical_sha256(receipt)
    endpoint, token, timeout, _allowed_hosts, _private_network = _master_records_configuration()
    if not master_records_transport_enabled():
        return _recording_not_completed("master_records_recorder_not_configured", receipt_sha256, receipt=receipt)
    body = {
        "schema": SUBMISSION_SCHEMA,
        "receipt": receipt,
        "authority_requested": False,
        # Formerly ``custody_requested`` (MASTER-RECORDS-BULK-SEMANTIC-REMEDIATION-002).
        "record_requested": True,
        "reconstruction_requested": True,
    }
    try:
        recorded_response = post(endpoint, json=body, headers=_headers(token), timeout=timeout)
        recorded_response.raise_for_status()
        recorded = recorded_response.json()
        _validate_recorded(recorded, receipt)
    except Exception as exc:
        return _recording_not_completed(
            f"master_records_recording_failed:{type(exc).__name__}", receipt_sha256, detail=str(exc)[:200], receipt=receipt)
    try:
        reconstruction_response = get(
            endpoint.rstrip("/") + f"/{receipt_sha256}/reconstruction",
            headers=_headers(token),
            timeout=timeout,
        )
        reconstruction_response.raise_for_status()
        rebuilt = _validate_reconstruction(reconstruction_response.json(), receipt_sha256, expected_receipt=receipt)
    except Exception as exc:
        return _recording_not_completed(
            f"master_records_reconstruction_failed:{type(exc).__name__}", receipt_sha256, detail=str(exc)[:200], receipt=receipt)
    return {
        "schema": CLOSURE_SCHEMA,
        "state": "RECORDED",
        "publication_transition_id": publication_transition_id,
        "transition_id": TRANSITION_ID,
        "master_record_ref": recorded.get("master_record_ref"),
        "custody_receipt_id": recorded.get("custody_receipt_id"),
        "receipt_sha256": receipt_sha256,
        "reconstructed_receipt_sha256": receipt_sha256,
        "reconstruction_status": "PASS",
        "required_evidence_validation_status": "PASS",
        "receipt": rebuilt,
        "gates_publication": False,
        "master_records_grants_transition_authority": False,
        "authority_effect": "NONE_DOWNSTREAM_RECORDING_ONLY",
    }


def verify_publication_transition_receipt(
    *,
    transition_receipt: Mapping[str, Any],
    receipt_sha256: str,
    publication_transition_id: str,
    publication_transition: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify the organization's own publication transition receipt locally.

    The repository mutation closes on this receipt. No Master Records reply,
    reconstruction or reference is consulted or awaited.
    """
    receipt_sha256 = _require_sha256(receipt_sha256, "transition_receipt_sha256")
    if not isinstance(transition_receipt, Mapping):
        raise PublicationCustodyError("publication_transition_receipt_missing")
    receipt = dict(transition_receipt)
    if canonical_sha256(receipt) != receipt_sha256:
        raise PublicationCustodyError("publication_transition_receipt_digest_mismatch")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise PublicationCustodyError("publication_transition_receipt_schema_mismatch")
    if receipt.get("transition_id") != TRANSITION_ID or receipt.get("transition_sequence") != 1:
        raise PublicationCustodyError("publication_transition_identity_mismatch")
    if receipt.get("subject_or_correlation_id") != publication_transition_id:
        raise PublicationCustodyError("publication_transition_subject_mismatch")
    if receipt.get("transition_outcome") != "ALLOW":
        raise PublicationCustodyError("publication_transition_outcome_not_allow")
    evidence = receipt.get("transition_evidence")
    if not isinstance(evidence, Mapping):
        raise PublicationCustodyError("publication_transition_evidence_missing")
    if evidence.get("publication_transition_id") != publication_transition_id:
        raise PublicationCustodyError("publication_transition_publication_id_mismatch")
    expected_transition_sha = canonical_sha256(publication_transition)
    if evidence.get("publication_transition_sha256") != expected_transition_sha:
        raise PublicationCustodyError("publication_transition_digest_mismatch")
    if evidence.get("target_repository") != "StegVerse-Labs/admissibility-wiki":
        raise PublicationCustodyError("publication_transition_repository_mismatch")
    if evidence.get("target_path") != publication_transition.get("target_path"):
        raise PublicationCustodyError("publication_transition_target_path_mismatch")
    if evidence.get("intr_governance_decision") != "ALLOW" or evidence.get("intr_decision_origin") != "external_interlock_intr":
        raise PublicationCustodyError("publication_transition_intr_allow_missing")
    if evidence.get("locally_generated_allow") is not False:
        raise PublicationCustodyError("publication_transition_local_allow_rejected")
    manifest = receipt.get("required_evidence_manifest")
    if not isinstance(manifest, list) or not manifest:
        raise PublicationCustodyError("publication_transition_required_evidence_missing")
    for item in manifest:
        if not isinstance(item, Mapping) or item.get("sha256") != canonical_sha256(item.get("content")):
            raise PublicationCustodyError("publication_transition_required_evidence_digest_mismatch")
    if receipt.get("master_records_may_grant_transition_authority") is not False:
        raise PublicationCustodyError("publication_transition_master_records_authority_escalation")
    return {
        "state": "VERIFIED",
        "verified_on": "ORGANIZATION_TRANSITION_RECEIPT",
        "receipt_sha256": receipt_sha256,
        "receipt": receipt,
        "master_records_gates_publication": False,
        "authority_effect": "NONE_VERIFICATION_ONLY",
    }


__all__ = [
    "PublicationCustodyError",
    "TASK_ID",
    "TRANSITION_ID",
    "build_publication_state_receipt",
    "record_governed_publication_closure",
    "verify_publication_transition_receipt",
]
