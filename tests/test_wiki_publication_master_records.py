from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest

from llm_adapter import wiki_publication_master_records as mod


def transition(decision="ALLOW_PUBLICATION_CANDIDATE"):
    return {
        "schema_version": "1.0.0",
        "transition_type": "external_framework_wiki_publication_transition",
        "package_id": "external-review-package:sha256:" + "1" * 64,
        "correction_receipt_id": "external-framework-correction-receipt:hmac-sha256:" + "2" * 64,
        "publisher_ref": "publisher:test",
        "target_path": "docs/external-frameworks/reports/test.md",
        "decision": decision,
        "source_commit_ref": "commit:test",
        "evidence_references": ["compat:test", "review:test"],
        "publication_executed": False,
        "boundary": {
            "transition_is_not_repository_write": True,
            "transition_is_not_certification": True,
            "transition_creates_no_standing": True,
            "separate_repository_mutation_required": True,
        },
    }


def manifest(value):
    digest = mod.canonical_sha256(value)
    return {
        "manifest_profile": "stegverse.ingress-manifest.v1",
        "manifest_profile_version": "1",
        "source_framework": "external_chat_publication_transition",
        "source_output_id": digest,
        "payload": deepcopy(value),
        "candidate": {
            "actor_class": "external_framework_publication_candidate",
            "action": "publish_governed_wiki_projection",
            "target": "StegVerse-Labs/admissibility-wiki:" + value["target_path"],
            "scope": "wiki_publication",
            "parameters": {
                "publication_transition_sha256": digest,
                "package_id": value["package_id"],
                "correction_receipt_id": value["correction_receipt_id"],
                "publisher_ref": value["publisher_ref"],
                "source_commit_ref": value["source_commit_ref"],
                "target_repository": "StegVerse-Labs/admissibility-wiki",
                "target_path": value["target_path"],
                "decision": value["decision"],
                "evidence_references": list(value["evidence_references"]),
                "publication_executed": False,
                "external_side_effect": True,
            },
        },
        "completion": {"egress": {"transport": "INTERLOCK_INTR"}},
    }


def governed(value):
    return {
        "request_id": "sdk-0b-test",
        "manifest_receipt_id": "MR-TEST",
        "governance_state": "ALLOW",
        "chain_verified": True,
        "posture_bound_execution": True,
        "intr_security_posture_binding": {
            "schema": "stegverse.sdk.intr-posture-runtime-binding.v1",
            "task_id": mod.TASK_ID,
            "payload_sha256": "sha256:" + mod.canonical_sha256(value),
            "transition_request_sha256": "sha256:" + "a" * 64,
            "resolution_authority": "INTERLOCK_INTR",
            "authority_effect": "NONE_VERIFICATION_AND_BINDING_ONLY",
        },
    }


def decision():
    return {
        "disposition": "ALLOW",
        "request_hash": "a" * 64,
        "transition_id": "sdk-0b-test",
        "ingress_receipt_hash": "b" * 64,
        "carrier_ref": "carrier:test",
        "authority": "Interlock/InTr",
        "locally_generated_allow": False,
    }


class FakeResponse:
    def __init__(self, body):
        self.body = body
    def raise_for_status(self):
        return None
    def json(self):
        return self.body


def test_build_receipt_binds_exact_publication_manifest_intr_and_sdk_result():
    value = transition()
    receipt = mod.build_publication_state_receipt(
        publication_transition_id="publication:test",
        publication_transition=value,
        sdk_manifest=manifest(value),
        governed_result=governed(value),
        intr_allow_decision=decision(),
        recorded_at="2026-09-21T20:00:00Z",
    )
    evidence = receipt["transition_evidence"]
    assert receipt["transition_id"] == mod.TRANSITION_ID
    assert receipt["transition_outcome"] == "ALLOW"
    assert evidence["publication_transition_sha256"] == mod.canonical_sha256(value)
    assert evidence["sdk_manifest_sha256"] == mod.canonical_sha256(manifest(value))
    assert evidence["intr_transition_request_sha256"] == "a" * 64
    assert evidence["intr_ingress_receipt_hash"] == "b" * 64
    assert evidence["locally_generated_allow"] is False
    assert len(receipt["required_evidence_manifest"]) == 4


def test_non_allow_publication_never_builds_allow_closure():
    value = transition("DENY_PUBLICATION")
    with pytest.raises(mod.PublicationCustodyError, match="not_allow_candidate"):
        mod.build_publication_state_receipt(
            publication_transition_id="publication:test",
            publication_transition=value,
            sdk_manifest=manifest(value),
            governed_result=governed(value),
            intr_allow_decision=decision(),
        )


def test_local_or_detached_intr_allow_is_rejected():
    value = transition()
    local = decision()
    local["locally_generated_allow"] = True
    with pytest.raises(mod.PublicationCustodyError, match="locally_generated"):
        mod.build_publication_state_receipt(
            publication_transition_id="publication:test",
            publication_transition=value,
            sdk_manifest=manifest(value),
            governed_result=governed(value),
            intr_allow_decision=local,
        )
    detached = decision()
    detached["request_hash"] = "c" * 64
    with pytest.raises(mod.PublicationCustodyError, match="request_hash_mismatch"):
        mod.build_publication_state_receipt(
            publication_transition_id="publication:test",
            publication_transition=value,
            sdk_manifest=manifest(value),
            governed_result=governed(value),
            intr_allow_decision=detached,
        )


def test_downstream_recording_reports_recorded_only_on_pass_evidence_digest_and_reconstruction(monkeypatch):
    value = transition()
    monkeypatch.setattr(mod, "master_records_transport_enabled", lambda: True)
    monkeypatch.setattr(mod, "_master_records_configuration", lambda: ("https://master-records.example/api/master-records/state-transitions", "server-token", 10.0, set(), False))
    observed = {}
    def post(url, json, headers, timeout):
        submitted_receipt = json["receipt"]
        digest = mod.canonical_sha256(submitted_receipt)
        observed["post"] = (url, json, headers, timeout)
        observed["receipt"] = submitted_receipt
        observed["digest"] = digest
        return FakeResponse({
            "state": "RECORDED",
            "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": digest,
            "reconstructed_receipt_sha256": digest,
            "master_record_ref": "master-record:test",
            "custody_receipt_id": "custody:test",
            "master_records_grants_transition_authority": False,
        })
    def get(url, headers, timeout):
        observed["get"] = (url, headers, timeout)
        digest = observed["digest"]
        return FakeResponse({
            "state": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": digest,
            "reconstructed_receipt_sha256": digest,
            "receipt": observed["receipt"],
            "master_records_grants_transition_authority": False,
        })
    closure = mod.record_governed_publication_closure(
        publication_transition_id="publication:test",
        publication_transition=value,
        sdk_manifest=manifest(value),
        governed_result=governed(value),
        intr_allow_decision=decision(),
        post=post,
        get=get,
    )
    digest = observed["digest"]
    assert closure["state"] == "RECORDED"
    assert closure["reconstruction_status"] == "PASS"
    assert closure["required_evidence_validation_status"] == "PASS"
    assert closure["receipt_sha256"] == closure["reconstructed_receipt_sha256"] == digest
    assert observed["post"][2]["Authorization"] == "Bearer server-token"
    assert observed["post"][1]["record_requested"] is True
    assert "custody_requested" not in observed["post"][1]
    assert observed["get"][0].endswith(f"/{digest}/reconstruction")
    assert closure["gates_publication"] is False

def _receipt(value):
    return mod.build_publication_state_receipt(
        publication_transition_id="publication:test",
        publication_transition=value,
        sdk_manifest=manifest(value),
        governed_result=governed(value),
        intr_allow_decision=decision(),
    )


def test_mutation_closes_on_organization_receipt_without_master_records(monkeypatch):
    value = transition()
    receipt = _receipt(value)
    digest = mod.canonical_sha256(receipt)

    def unreachable(*_args, **_kwargs):
        raise AssertionError("verification must not consult Master Records")

    monkeypatch.setattr(mod, "master_records_transport_enabled", unreachable)
    monkeypatch.setattr(mod, "_master_records_configuration", unreachable)
    verified = mod.verify_publication_transition_receipt(
        transition_receipt=receipt,
        receipt_sha256=digest,
        publication_transition_id="publication:test",
        publication_transition=value,
    )
    assert verified["state"] == "VERIFIED"
    assert verified["verified_on"] == "ORGANIZATION_TRANSITION_RECEIPT"
    assert verified["master_records_gates_publication"] is False


def test_organization_receipt_verification_rejects_tampering():
    value = transition()
    receipt = _receipt(value)
    digest = mod.canonical_sha256(receipt)
    with pytest.raises(mod.PublicationCustodyError, match="digest_mismatch"):
        mod.verify_publication_transition_receipt(
            transition_receipt=receipt, receipt_sha256="0" * 64,
            publication_transition_id="publication:test", publication_transition=value)
    with pytest.raises(mod.PublicationCustodyError, match="subject_mismatch"):
        mod.verify_publication_transition_receipt(
            transition_receipt=receipt, receipt_sha256=digest,
            publication_transition_id="publication:other", publication_transition=value)
    forged = deepcopy(receipt)
    forged["transition_evidence"]["locally_generated_allow"] = True
    with pytest.raises(mod.PublicationCustodyError, match="local_allow_rejected"):
        mod.verify_publication_transition_receipt(
            transition_receipt=forged, receipt_sha256=mod.canonical_sha256(forged),
            publication_transition_id="publication:test", publication_transition=value)


def test_master_records_recording_is_optional_and_non_gating(monkeypatch):
    value = transition()
    monkeypatch.setattr(mod, "master_records_transport_enabled", lambda: False)
    monkeypatch.setattr(mod, "_master_records_configuration", lambda: ("", "", 10.0, set(), False))
    result = mod.record_governed_publication_closure(
        publication_transition_id="publication:test",
        publication_transition=value,
        sdk_manifest=manifest(value),
        governed_result=governed(value),
        intr_allow_decision=decision(),
    )
    assert result["state"] == "NOT_RECORDED"
    assert result["gates_publication"] is False
    for field in ("failure_code", "failed_predicate", "required_evidence_or_repair",
                  "retry_entrypoint", "owning_existing_goal", "next_attempt"):
        assert result[field]
    assert result["receipt_sha256"] == mod.canonical_sha256(result["receipt"])


def test_master_records_rejection_is_reported_not_raised(monkeypatch):
    value = transition()
    monkeypatch.setattr(mod, "master_records_transport_enabled", lambda: True)
    monkeypatch.setattr(mod, "_master_records_configuration", lambda: ("https://master-records.example/api/master-records/state-transitions", "server-token", 10.0, set(), False))
    result = mod.record_governed_publication_closure(
        publication_transition_id="publication:test",
        publication_transition=value,
        sdk_manifest=manifest(value),
        governed_result=governed(value),
        intr_allow_decision=decision(),
        post=lambda *a, **k: FakeResponse({"state": "PENDING"}),
    )
    assert result["state"] == "NOT_RECORDED"
    assert result["failure_code"].startswith("master_records_recording_failed")
    assert result["gates_publication"] is False
