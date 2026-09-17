import hashlib
import json

import pytest

from llm_adapter.stegbrowser_master_records_state_transition_relay import (
    NONCE,
    TRANSITION_ID,
    StegBrowserMasterRecordsRelayError,
    relay_stegbrowser_state_transition,
)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha_uri(seed):
    return "sha256:" + hashlib.sha256(seed.encode("utf-8")).hexdigest()


def receipt():
    evidence = {
        "source_schema": "stegverse.master-records.stegbrowser-readiness-custody-intr-admission/v1",
        "transition_id": TRANSITION_ID,
        "canonical_task": "STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001",
        "cosv_task_vector": "40000100100000",
        "source_receipt_sha256": _sha_uri("source"),
        "runtime_readiness_receipt_sha256": _sha_uri("runtime"),
        "readiness_node_receipt_sha256": _sha_uri("node-receipt"),
        "invocation_request_nonce": NONCE,
        "node_id": "SV-NODE-test",
        "interlock_id": "SV-IL-test",
        "registration_receipt_sha256": _sha_uri("registration"),
        "lease_id": "lease-1",
        "runtime_id": "runtime-1",
        "exported_bundle_sha256": _sha_uri("bundle"),
        "intr_governance_decision": "ALLOW",
        "intr_ingress_state": "INGRESS_ADMITTED",
    }
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": TRANSITION_ID,
        "transition_sequence": 1,
        "subject_or_correlation_id": NONCE,
        "prior_state_ref_or_hash": None,
        "resulting_state_ref_or_hash": evidence["runtime_readiness_receipt_sha256"],
        "governance_decision_ref_where_applicable": "intr:ALLOW:" + TRANSITION_ID,
        "transition_evidence": evidence,
        "recorded_at": "2026-09-17T23:10:00Z",
        "transition_outcome": "OBSERVED",
        "authority_effect": "NONE_STATE_RECEIPT_ONLY",
        "proof_scope": "THIS_TRANSITION_ONLY",
        "proof_ceiling": "OBSERVED_STATE_TRANSITION_AND_CUSTODY_ONLY",
        "master_records_may_grant_transition_authority": False,
        "master_records_may_grant_execution_authority": False,
    }


def submission():
    return {
        "schema": "stegverse.master-records.state-transition-submission/v1",
        "receipt": receipt(),
        "authority_requested": False,
        "custody_requested": True,
        "reconstruction_requested": True,
    }


class Response:
    def __init__(self, payload):
        self.payload = payload
    def raise_for_status(self):
        return None
    def json(self):
        return self.payload


def recorded(r):
    digest = hashlib.sha256(_canonical(r).encode("utf-8")).hexdigest()
    return {
        "schema": "stegverse.master-records.state-transition-custody-receipt/v1",
        "state": "RECORDED",
        "transition_id": TRANSITION_ID,
        "transition_sequence": 1,
        "subject_or_correlation_id": NONCE,
        "transition_outcome": "OBSERVED",
        "custody_receipt_id": "mr-receipt",
        "master_record_ref": "master-record:state-transition:sha256:" + digest,
        "receipt_sha256": digest,
        "reconstructed_receipt_sha256": digest,
        "recorded_at": "2026-09-17T23:10:01Z",
        "reconstruction_status": "PASS",
        "master_records_grants_transition_authority": False,
        "master_records_grants_execution_authority": False,
        "master_records_grants_credential_authority": False,
        "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
    }


def _configure(monkeypatch):
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_ENDPOINT", "https://master-records.example")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_TOKEN", "server-only-token")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_ALLOWED_HOSTS", "master-records.example")


def test_relay_uses_server_side_tvtvc_credential_and_returns_exact_canonical_result(monkeypatch):
    _configure(monkeypatch)
    observed = {}
    body = submission()
    def post(url, data=None, headers=None, timeout=None):
        observed.update(url=url, data=data, headers=headers, timeout=timeout)
        return Response(recorded(body["receipt"]))
    result = relay_stegbrowser_state_transition(body, post=post)
    assert observed["url"] == "https://master-records.example/api/master-records/state-transitions"
    assert observed["headers"]["Authorization"] == "Bearer server-only-token"
    assert b"server-only-token" not in observed["data"]
    assert "server-only-token" not in repr(result)
    assert result["state"] == "RECORDED"
    assert result["reconstruction_status"] == "PASS"
    assert result["receipt_sha256"] == result["reconstructed_receipt_sha256"]


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(authority_requested=True),
    lambda p: p["receipt"].update(subject_or_correlation_id="different"),
    lambda p: p["receipt"].update(transition_sequence=2),
    lambda p: p["receipt"].update(transition_outcome="INGRESS_ADMITTED"),
    lambda p: p["receipt"]["transition_evidence"].update(intr_governance_decision="DENY"),
])
def test_relay_fails_closed_on_boundary_or_immutable_identity_drift(monkeypatch, mutate):
    _configure(monkeypatch)
    body = submission()
    mutate(body)
    with pytest.raises(StegBrowserMasterRecordsRelayError):
        relay_stegbrowser_state_transition(body, post=lambda *a, **k: None)


def test_relay_requires_exact_reconstruction_digest(monkeypatch):
    _configure(monkeypatch)
    body = submission()
    bad = recorded(body["receipt"])
    bad["reconstructed_receipt_sha256"] = "0" * 64
    with pytest.raises(StegBrowserMasterRecordsRelayError, match="digest_mismatch"):
        relay_stegbrowser_state_transition(body, post=lambda *a, **k: Response(bad))
