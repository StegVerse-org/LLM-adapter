"""Credential-nonexporting relay for the immutable StegBrowser state-transition custody receipt.

The browser supplies only the canonical non-secret state-transition submission. This
module uses the existing service-gateway Master Records configuration materialized
under TV/TVC authority, forwards the unchanged submission to the sole canonical
Master Records API, and returns only the canonical custody result after exact
reconstruction validation.

This is transport only. It grants no transition, execution, credential, custody,
publication, or governance authority and does not implement a second custody store.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

import requests

SUBMISSION_SCHEMA = "stegverse.master-records.state-transition-submission/v1"
RECEIPT_SCHEMA = "stegverse.canonical-state-transition-receipt/v1"
CUSTODY_SCHEMA = "stegverse.master-records.state-transition-custody-receipt/v1"
CANONICAL_PATH = "/api/master-records/state-transitions"

NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"
TRANSITION_ID = "STEGBROWSER_RUNTIME_READINESS_MASTER_RECORDS_CUSTODY"
CANONICAL_TASK = "STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001"
COSV = "40000100100000"
SOURCE_SCHEMA = "stegverse.master-records.stegbrowser-readiness-custody-intr-admission/v1"

SHA_URI = re.compile(r"^sha256:[0-9a-f]{64}$")


class StegBrowserMasterRecordsRelayError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def receipt_digest(receipt: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(dict(receipt)).encode("utf-8")).hexdigest()


def _configuration() -> tuple[str, str, float, set[str], bool]:
    explicit = os.getenv("STEGVERSE_MASTER_RECORDS_ENDPOINT", "").strip().rstrip("/")
    private_hostport = os.getenv("STEGVERSE_MASTER_RECORDS_HOSTPORT", "").strip().strip("/")
    private_network = bool(private_hostport and not explicit)
    endpoint = explicit or (f"http://{private_hostport}" if private_hostport else "")
    if endpoint and not endpoint.endswith(CANONICAL_PATH):
        endpoint += CANONICAL_PATH
    token = os.getenv("STEGVERSE_MASTER_RECORDS_TOKEN", "").strip()
    try:
        timeout = float(os.getenv("STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS", "10"))
    except ValueError as exc:
        raise StegBrowserMasterRecordsRelayError("master_records_timeout_invalid") from exc
    allowed_hosts = {
        host.strip().lower()
        for host in os.getenv("STEGVERSE_MASTER_RECORDS_ALLOWED_HOSTS", "").split(",")
        if host.strip()
    }
    return endpoint, token, timeout, allowed_hosts, private_network


def enabled() -> bool:
    try:
        endpoint, token, timeout, allowed_hosts, private_network = _configuration()
    except StegBrowserMasterRecordsRelayError:
        return False
    if not endpoint or not token or timeout <= 0:
        return False
    parsed = urlparse(endpoint)
    local_http = parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    allow_local = os.getenv("STEGVERSE_ALLOW_LOCAL_MASTER_RECORDS_HTTP", "").lower() == "true"
    allow_private = os.getenv("STEGVERSE_ALLOW_PRIVATE_MASTER_RECORDS_HTTP", "").lower() == "true"
    if parsed.scheme != "https" and not ((local_http and allow_local) or (private_network and allow_private)):
        return False
    if not parsed.hostname:
        return False
    if allowed_hosts and parsed.hostname.lower() not in allowed_hosts:
        return False
    return True


def _validate_submission(payload: Mapping[str, Any]) -> dict[str, Any]:
    if set(payload) != {"schema", "receipt", "authority_requested", "custody_requested", "reconstruction_requested"}:
        raise StegBrowserMasterRecordsRelayError("state_transition_submission_field_set_invalid")
    if payload.get("schema") != SUBMISSION_SCHEMA:
        raise StegBrowserMasterRecordsRelayError("state_transition_submission_schema_mismatch")
    if payload.get("authority_requested") is not False or payload.get("custody_requested") is not True or payload.get("reconstruction_requested") is not True:
        raise StegBrowserMasterRecordsRelayError("state_transition_submission_boundary_invalid")
    receipt = payload.get("receipt")
    if not isinstance(receipt, Mapping):
        raise StegBrowserMasterRecordsRelayError("state_transition_receipt_required")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise StegBrowserMasterRecordsRelayError("state_transition_receipt_schema_mismatch")
    if receipt.get("transition_id") != TRANSITION_ID or receipt.get("transition_sequence") != 1:
        raise StegBrowserMasterRecordsRelayError("stegbrowser_transition_identity_mismatch")
    if receipt.get("subject_or_correlation_id") != NONCE:
        raise StegBrowserMasterRecordsRelayError("stegbrowser_immutable_nonce_mismatch")
    if receipt.get("transition_outcome") != "OBSERVED":
        raise StegBrowserMasterRecordsRelayError("stegbrowser_transition_outcome_must_be_observed")
    if receipt.get("authority_effect") != "NONE_STATE_RECEIPT_ONLY":
        raise StegBrowserMasterRecordsRelayError("stegbrowser_receipt_authority_effect_invalid")
    if receipt.get("master_records_may_grant_transition_authority") is not False or receipt.get("master_records_may_grant_execution_authority") is not False:
        raise StegBrowserMasterRecordsRelayError("master_records_authority_escalation_requested")

    evidence = receipt.get("transition_evidence")
    if not isinstance(evidence, Mapping):
        raise StegBrowserMasterRecordsRelayError("stegbrowser_transition_evidence_required")
    exact = {
        "source_schema": SOURCE_SCHEMA,
        "transition_id": TRANSITION_ID,
        "canonical_task": CANONICAL_TASK,
        "cosv_task_vector": COSV,
        "invocation_request_nonce": NONCE,
        "intr_governance_decision": "ALLOW",
        "intr_ingress_state": "INGRESS_ADMITTED",
    }
    for key, expected in exact.items():
        if evidence.get(key) != expected:
            raise StegBrowserMasterRecordsRelayError(f"stegbrowser_transition_evidence_mismatch:{key}")
    for key in (
        "source_receipt_sha256",
        "runtime_readiness_receipt_sha256",
        "readiness_node_receipt_sha256",
        "registration_receipt_sha256",
        "exported_bundle_sha256",
    ):
        if not SHA_URI.fullmatch(str(evidence.get(key) or "")):
            raise StegBrowserMasterRecordsRelayError(f"stegbrowser_transition_digest_invalid:{key}")
    for key in ("node_id", "interlock_id", "lease_id", "runtime_id"):
        if not isinstance(evidence.get(key), str) or not evidence[key]:
            raise StegBrowserMasterRecordsRelayError(f"stegbrowser_transition_identity_missing:{key}")
    return dict(receipt)


def _validate_response(response: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    expected = receipt_digest(receipt)
    if response.get("schema") != CUSTODY_SCHEMA:
        raise StegBrowserMasterRecordsRelayError("master_records_state_transition_response_schema_mismatch")
    if response.get("state") != "RECORDED" or response.get("reconstruction_status") != "PASS":
        raise StegBrowserMasterRecordsRelayError("master_records_state_transition_reconstruction_not_pass")
    if response.get("receipt_sha256") != expected or response.get("reconstructed_receipt_sha256") != expected:
        raise StegBrowserMasterRecordsRelayError("master_records_state_transition_digest_mismatch")
    if response.get("transition_id") != TRANSITION_ID or response.get("transition_sequence") != 1 or response.get("subject_or_correlation_id") != NONCE:
        raise StegBrowserMasterRecordsRelayError("master_records_state_transition_identity_mismatch")
    for key in ("master_records_grants_transition_authority", "master_records_grants_execution_authority", "master_records_grants_credential_authority"):
        if response.get(key) is not False:
            raise StegBrowserMasterRecordsRelayError(f"master_records_authority_escalation:{key}")
    return dict(response)


def relay_stegbrowser_state_transition(
    payload: Mapping[str, Any],
    *,
    post: Callable[..., Any] = requests.post,
) -> dict[str, Any]:
    receipt = _validate_submission(payload)
    endpoint, token, timeout, _allowed_hosts, _private_network = _configuration()
    if not enabled():
        raise StegBrowserMasterRecordsRelayError("master_records_state_transition_relay_not_configured")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        response = post(endpoint, data=canonical_json(dict(payload)).encode("utf-8"), headers=headers, timeout=timeout)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        raise StegBrowserMasterRecordsRelayError("master_records_state_transition_transport_failed") from exc
    if not isinstance(result, Mapping):
        raise StegBrowserMasterRecordsRelayError("master_records_state_transition_response_not_object")
    return _validate_response(result, receipt)


__all__ = [
    "CANONICAL_PATH",
    "NONCE",
    "TRANSITION_ID",
    "StegBrowserMasterRecordsRelayError",
    "enabled",
    "relay_stegbrowser_state_transition",
]
