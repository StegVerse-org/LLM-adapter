"""Offline exact-boundary integration only; never evidence of resident/provider execution."""
from __future__ import annotations
import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

from llm_adapter.provider_request import ProviderMessage, ProviderRequest
from llm_adapter.governed_external_provider_client import (
    GovernedExternalProviderClient, GovernedExternalProviderClientError,
    external_wire_request_hash,
)
from llm_adapter.openai_tvc_runtime_executor import (
    OpenAIEphemeralExecutionError, openai_wire_request_hash,
    verify_tvc_lease, execute_governed_openai_via_tvc_runtime,
    admit_openai_tvc_runtime_egress,
)
from llm_adapter.external_llm_connection import (
    ExternalLLMConnectionError, execute_governed_external_llm,
)

TASK = "EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001"
MODEL = "gpt-5.6"
SESSION = "ephemeral-browser-lease-1"
TRANSITION = "intr-transition-1"
INGRESS = "a" * 64
CARRIER = "hb32:current"


def sha(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def request():
    return ProviderRequest(
        provider="openai", model=MODEL, messages=(ProviderMessage(role="user", content="Non-private test input"),),
        temperature=0.0,
    )


def lease(req=None):
    req = req or request()
    now = datetime.now(timezone.utc)
    row = {
        "schema": "stegverse.tvc.ephemeral-openai-capability-lease/v1",
        "decision": "ALLOW_CAPABILITY_LEASE", "provider": "openai",
        "capability": "llm.ephemeral.openai", "operation": "chat_completion_with_usage",
        "task_id": TASK, "model": req.model,
        "request_hash": openai_wire_request_hash(req),
        "invocation_id": "task-invocation-1", "worker_claim_ref": "authentic-claim-ref",
        "fence_ref": "authentic-fence-ref", "browser_lease_id": SESSION,
        "browser_lease_commitment": "sha256:" + "f" * 64,
        "transition_id": TRANSITION, "ingress_receipt_hash": INGRESS,
        "carrier_ref": CARRIER, "request_nonce": "unique-source-test-nonce",
        "authenticated_admission_receipt_ref": "source-test-only-admission",
        "issued_at_utc": (now-timedelta(seconds=3)).isoformat(),
        "expiry_utc": (now+timedelta(seconds=90)).isoformat(),
        "single_use": True, "credential_authority": "TV/TVC",
        "credential_material_present": False, "secret_values_exported": False,
        "protected_values_exposed": False, "wallet_contacted": False,
        "signing_authority": False, "broadcast_authority": False,
        "custody_authority": False, "authority_granted": False,
        "second_machine_required": False,
    }
    row["lease_id"] = "tvc-ephemeral-openai:" + sha(row)
    row["receipt_sha256"] = "sha256:" + sha(row)
    return row


def fixture_boundaries(*, request_override=None, lease_override=None, org_override=None, custody_override=None,
                       ingress_override=None, egress_override=None, broker_override=None,
                       admission_baseline=None, admission_override=None, chain_override=None):
    req = request_override or request()
    l = lease_override or lease(req)
    # Snapshot the TVC-issued admission independently from any caller-modified
    # lease. In live execution this readback is owned by resident custody.
    original = copy.deepcopy(admission_baseline or l)
    calls = []
    retained_org = {}
    def verify_admission(proposed):
        calls.append("verify_admission")
        row = {
            "verified": True,
            "authority": "WorkerCoordinator+Interlock/InTr+StegBrowser+TV/TVC",
            "current_fence_active": True,
            "browser_lease_active": True,
        }
        for field in (
            "task_id", "invocation_id", "worker_claim_ref", "fence_ref",
            "browser_lease_id", "browser_lease_commitment", "transition_id",
            "ingress_receipt_hash", "request_hash", "carrier_ref",
            "authenticated_admission_receipt_ref", "lease_id", "receipt_sha256",
        ):
            row[field] = original[field]
        if admission_override:
            row.update(admission_override)
        return row
    def ingress(r, request_hash):
        calls.append("ingress")
        assert r is req
        response = {"disposition": "ALLOW", "request_hash": request_hash,
                    "transition_id": TRANSITION, "receipt_hash": INGRESS, "carrier_ref": CARRIER}
        if ingress_override:
            response.update(ingress_override)
        return response
    def tvc(r, decision):
        calls.append("tvc")
        return {"credential_authority": "TV/TVC", "credential_material_present": False,
                "lease_receipt": l, "broker_submitter": broker}
    def broker(operation):
        calls.append("broker")
        assert operation["secret_ref"] == "vault://tvc/providers/openai/api-key"
        assert operation["lease_receipt"]["task_id"] == TASK
        assert "api_key" not in operation
        return broker_override or {
            "decision": "ALLOW_OPERATION_RESULT",
            "measurement_evidence": {
                "provider": "openai", "model": MODEL,
                "provider_response_id": "source-test-response-1",
                "candidate_output": "The non-private task has a useful answer.",
                "normalized_usage": {"input_tokens": 8, "output_tokens": 11, "total_tokens": 19},
                "provider_api_key_transferred_to_consumer": False, "secret_material_returned": False,
            },
            "use_receipt": {k: False for k in (
                "secret_material_returned", "secret_material_logged", "secret_material_retained",
                "wallet_contacted", "signed", "broadcast",
            )} | {"single_use_consumed": True},
        }
    def org(event):
        calls.append("organization")
        assert event["subject_or_correlation_id"] == TASK
        digest = "sha256:" + sha(event)
        body = {
            "schema": "stegverse.organization-transition-receipt/v1",
            "organization": "StegVerse-org",
            "source_receipt_schema": "stegverse.canonical-state-transition-receipt/v1",
            "subject_or_correlation_id": TASK,
            "org_transition_class": "ORGANIZATION_STATE_TRANSITION",
            "source_transition_sha256": "sha256:" + "b" * 64,
            "canonical_state_transition_receipt_sha256": "sha256:" + "b" * 64,
            "boundary_evidence": {"provider_event_sha256": digest},
            "previous_receipt_sha256": "sha256:" + "c" * 64,
        }
        if org_override:
            body.update(org_override)
        retained_org.clear()
        retained_org.update({**body, "receipt_sha256": "sha256:" + sha(body)})
        return dict(retained_org)
    def org_chain(receipt):
        calls.append("org_replay")
        # Source-level fake of a separate read-only organization ledger lookup.
        # Production MUST bind this to real predecessor and successor readback.
        response = {
            "verified": receipt == retained_org,
            "organization": retained_org.get("organization"),
            "receipt_sha256": retained_org.get("receipt_sha256"),
            "previous_receipt_sha256": retained_org.get("previous_receipt_sha256"),
            "predecessor_verified": True,
            "source_event_sha256": retained_org.get("boundary_evidence", {}).get("provider_event_sha256"),
        }
        if chain_override:
            response.update(chain_override)
        return response
    def custody(event):
        calls.append("custody")
        row = {"status": "CUSTODY_RECORDED", "custody_recorded": True,
               "event_sha256": event["event_sha256"], "session_id": SESSION,
               "authority_granted": False}
        if custody_override:
            row.update(custody_override)
        return row
    def egress(handoff):
        calls.append("egress")
        row = {"disposition": "ALLOW", "response_hash": handoff["response_hash"],
               "receipt_hash": "d" * 64}
        if egress_override:
            row.update(egress_override)
        return row
    client = GovernedExternalProviderClient(
        session_id=SESSION, measurement_id_factory=lambda _: "source-test-measurement",
        ingress_evaluator=ingress, tvc_material_resolver=tvc,
        org_transition_recorder=org, org_chain_verifier=org_chain, usage_submitter=custody,
        egress_evaluator=egress,
        current_admission_verifier=verify_admission,
    )
    return req, l, client, calls


def test_exact_hash_convergence_across_provider_client_and_tvc_canonical_payload():
    r = request()
    wire = {
        "protocol": "stegverse.intr.openai.responses.v1", "provider": "openai",
        "endpoint_profile": "openai_responses",
        "payload": {"model": MODEL, "input": "user: Non-private test input", "max_output_tokens": 2048},
    }
    assert openai_wire_request_hash(r) == sha(wire) == external_wire_request_hash(r)
    assert openai_wire_request_hash(r) != r.request_hash


def test_one_complete_offline_provider_operation_order_and_attributed_usage():
    r, l, client, calls = fixture_boundaries()
    result = client.complete(r)
    assert result.output == "The non-private task has a useful answer."
    assert result.metadata["usage"]["total_tokens"] == 19
    assert result.metadata["governed_external_connection"] is True
    assert result.metadata["egress_intr_admitted"] is True
    assert result.metadata["credential_material_present"] is False
    assert calls == ["ingress", "tvc", "verify_admission", "broker", "organization", "org_replay", "custody", "egress"]


@pytest.mark.parametrize("field,value", [
    ("worker_claim_ref", "wrong-worker"), ("fence_ref", "stale-fence"),
    ("browser_lease_id", "other-session"), ("transition_id", "different-transition"),
    ("ingress_receipt_hash", "f" * 64), ("request_hash", "e" * 64),
    ("credential_material_present", True), ("capability", "llm.measure.openai"),
])
def test_forged_or_stale_task_lease_never_reaches_broker(field, value):
    r = request()
    l = lease(r)
    original = copy.deepcopy(l)
    l[field] = value
    # Deliberately recompute hash: an attacker who can edit source JSON still
    # cannot substitute exact authority bindings.
    body = dict(l)
    body.pop("receipt_sha256")
    l["receipt_sha256"] = "sha256:" + sha(body)
    _, _, client, calls = fixture_boundaries(request_override=r, lease_override=l, admission_baseline=original)
    with pytest.raises(OpenAIEphemeralExecutionError):
        client.complete(r)
    assert "broker" not in calls
    if field in {"worker_claim_ref", "fence_ref"}:
        assert "verify_admission" in calls


def test_ingress_deny_and_exact_hash_mismatch_fail_before_tvc():
    for reply in ({"disposition": "DENY"}, {"request_hash": "f" * 64}):
        r, _, client, calls = fixture_boundaries(ingress_override=reply)
        with pytest.raises(GovernedExternalProviderClientError):
            client.complete(r)
        assert calls == ["ingress"]


def test_measurement_only_credential_fallback_is_rejected():
    with pytest.raises(ExternalLLMConnectionError, match="non-exportable"):
        execute_governed_external_llm(
            request(), session_id=SESSION, transition_id=TRANSITION,
            measurement_id="source-test", ingress_disposition="ALLOW",
            ingress_receipt_hash=INGRESS, carrier_ref=CARRIER,
            credential_resolver=lambda: "not-a-real-credential",
        )


def test_org_receipt_must_bind_original_event_and_correct_owner():
    for broken in (
        {"organization": "another-org"},
        {"boundary_evidence": {"provider_event_sha256": "sha256:"+"0"*64}},
        {"previous_receipt_sha256": None, "source_transition_sha256": "sha256:"+"b"*64},
    ):
        r, l, client, calls = fixture_boundaries(org_override=broken)
        with pytest.raises(OpenAIEphemeralExecutionError):
            client.complete(r)
        assert calls == ["ingress", "tvc", "verify_admission", "broker", "organization"]


def test_usage_custody_cannot_be_inferred_from_source_or_unavailable_receipt():
    for custody in ({"status": "NOT_CONFIGURED", "custody_recorded": False},
                    {"event_sha256": "0" * 64}, {"authority_granted": True}):
        r, _, client, calls = fixture_boundaries(custody_override=custody)
        with pytest.raises(OpenAIEphemeralExecutionError):
            client.complete(r)
        assert calls == ["ingress", "tvc", "verify_admission", "broker", "organization", "org_replay", "custody"]


def test_egress_deny_and_response_hash_mismatch_fail_closed():
    for reply in ({"disposition": "DENY"}, {"response_hash": "0" * 64}):
        r, _, client, calls = fixture_boundaries(egress_override=reply)
        with pytest.raises(GovernedExternalProviderClientError):
            client.complete(r)
        assert calls == ["ingress", "tvc", "verify_admission", "broker", "organization", "org_replay", "custody", "egress"]


def test_missing_org_recorder_fails_before_provider_execution():
    r, l, client, calls = fixture_boundaries()
    invalid = GovernedExternalProviderClient(
        session_id=client.session_id, measurement_id_factory=client.measurement_id_factory,
        ingress_evaluator=client.ingress_evaluator, tvc_material_resolver=client.tvc_material_resolver,
        egress_evaluator=client.egress_evaluator,
    )
    with pytest.raises(GovernedExternalProviderClientError, match="organization"):
        invalid.complete(r)
    assert calls == ["ingress", "tvc"]


def test_replayed_org_receipt_must_have_exact_existing_predecessor():
    for alteration in (
        {"verified": False},
        {"predecessor_verified": False},
        {"previous_receipt_sha256": "sha256:" + "0"*64},
        {"source_event_sha256": "sha256:" + "0"*64},
        {"organization": "unknown-org"},
    ):
        r, _, client, calls = fixture_boundaries(chain_override=alteration)
        with pytest.raises(OpenAIEphemeralExecutionError, match="predecessor replay"):
            client.complete(r)
        assert calls == ["ingress", "tvc", "verify_admission", "broker", "organization", "org_replay"]


def test_missing_existing_org_chain_verifier_refuses_before_broker():
    r, _, client, calls = fixture_boundaries()
    invalid = GovernedExternalProviderClient(
        session_id=client.session_id, measurement_id_factory=client.measurement_id_factory,
        ingress_evaluator=client.ingress_evaluator, tvc_material_resolver=client.tvc_material_resolver,
        org_transition_recorder=client.org_transition_recorder,
        current_admission_verifier=client.current_admission_verifier,
        egress_evaluator=client.egress_evaluator,
    )
    with pytest.raises(GovernedExternalProviderClientError, match="predecessor verifier"):
        invalid.complete(r)
    assert calls == ["ingress", "tvc"]


def _candidate_broker_result():
    return {
        "decision": "ALLOW_OPERATION_RESULT",
        "measurement_evidence": {
            "provider": "openai", "model": MODEL,
            "provider_response_id": "source-test-response-1",
            "candidate_output": "Test response",
            "normalized_usage": {"input_tokens": 8, "output_tokens": 11, "total_tokens": 19},
            "provider_api_key_transferred_to_consumer": False,
            "secret_material_returned": False,
        },
        "use_receipt": {k: False for k in (
            "secret_material_returned", "secret_material_logged", "secret_material_retained",
            "wallet_contacted", "signed", "broadcast",
        )} | {"single_use_consumed": True},
    }


@pytest.mark.parametrize("path,value", [
    (("measurement_evidence", "api_key"), "sk-proj-source-test-NEVER_REAL"),
    (("measurement_evidence", "authorization"), "Bearer source-test-only"),
    (("measurement_evidence", "normalized_usage", "secret"), "source-test-secret"),
    (("use_receipt", "credential"), "source-test-secret"),
])
def test_broker_evidence_secret_injection_is_refused(path, value):
    reply = _candidate_broker_result()
    cursor = reply
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    r, _, client, calls = fixture_boundaries(broker_override=reply)
    with pytest.raises(OpenAIEphemeralExecutionError, match="protected material"):
        client.complete(r)
    assert calls == ["ingress", "tvc", "verify_admission", "broker"]


@pytest.mark.parametrize("invalid_usage", [
    {"input_tokens": 8, "output_tokens": 11},
    {"input_tokens": 8, "output_tokens": 11, "total_tokens": 18},
    {"input_tokens": 0, "output_tokens": 11, "total_tokens": 11},
    {"input_tokens": 8, "output_tokens": True, "total_tokens": 9},
    {"input_tokens": 8, "output_tokens": -1, "total_tokens": 7},
])
def test_incomplete_or_fabricated_native_usage_is_refused(invalid_usage):
    reply = _candidate_broker_result()
    reply["measurement_evidence"]["normalized_usage"] = invalid_usage
    r, _, client, calls = fixture_boundaries(broker_override=reply)
    with pytest.raises(OpenAIEphemeralExecutionError, match="usage"):
        client.complete(r)
    assert calls == ["ingress", "tvc", "verify_admission", "broker"]
