from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from llm_adapter import external_review_api
from llm_adapter.combined_gateway import app
from llm_adapter.external_review_store import ExternalReviewStore


def configure(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setattr(external_review_api, "store", ExternalReviewStore(str(tmp_path / "review.db")))
    monkeypatch.setenv("STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN", "submit-secret")
    monkeypatch.setenv("STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY", "receipt-secret")
    now = datetime.now(timezone.utc)
    monkeypatch.setenv("STEGVERSE_EXTERNAL_REVIEWERS_JSON", json.dumps({
        "reviewer:test": {
            "token_sha256": hashlib.sha256(b"reviewer-secret").hexdigest(),
            "delegation_ref": "delegation:reviewer:test",
            "scopes": ["package:read", "field:evidence_model"],
            "valid_from": (now - timedelta(minutes=5)).isoformat(),
            "valid_until": (now + timedelta(hours=1)).isoformat(),
        }
    }))
    monkeypatch.setenv("STEGVERSE_EXTERNAL_PUBLISHERS_JSON", json.dumps({
        "publisher:test": {
            "token_sha256": hashlib.sha256(b"publisher-secret").hexdigest(),
            "delegation_ref": "delegation:publisher:test",
            "scopes": ["publication:wiki", "framework:decisionassure"],
            "valid_from": (now - timedelta(minutes=5)).isoformat(),
            "valid_until": (now + timedelta(hours=1)).isoformat(),
        }
    }))
    return TestClient(app)


def review_package() -> dict:
    return {
        "schema_version": "1.0.0",
        "packet_type": "external_framework_cooperative_review_package",
        "framework_id": "decisionassure",
        "framework_name": "DecisionAssure",
        "compatibility_receipt_id": "external-compatibility-receipt:sha256:" + "a" * 64,
        "submission_sha256": "b" * 64,
        "compatibility_result": "COMPATIBILITY_EVIDENCE_READY",
        "submitter_opt_in": True,
        "publication_requested": False,
        "raw_submission_included": False,
        "review_scope": ["evidence_model"],
        "evidence_references": ["evidence:test"],
        "contact_reference": None,
        "boundary": {
            "package_is_publication_authority": False,
            "package_is_certification": False,
            "package_creates_standing": False,
            "review_may_change_result_without_receipt": False,
        },
    }


def correction(package_id: str) -> dict:
    return {
        "packet_type": "external_framework_correction_request",
        "schema_version": "1.0.0",
        "package_id": package_id,
        "challenged_receipt_id": "external-compatibility-receipt:sha256:" + "a" * 64,
        "challenged_submission_sha256": "b" * 64,
        "reviewer_ref": "reviewer:test",
        "decision": "UPHOLD",
        "reviewed_fields": ["evidence_model"],
        "supporting_evidence_references": ["evidence:review:test"],
        "rationale": "Reviewed evidence supports the bounded compatibility result.",
        "replacement_result": None,
        "replacement_receipt_id": None,
        "publication_authorized": False,
    }


def test_reviewer_lookup_requires_delegated_read_scope(monkeypatch, tmp_path):
    client = configure(monkeypatch, tmp_path)
    created = client.post("/api/external-review/packages", json=review_package(), headers={"Authorization": "Bearer submit-secret"})
    package_id = created.json()["package_id"]
    response = client.get(
        f"/api/external-review/reviewer/packages/{package_id}?reviewer_ref=reviewer:test",
        headers={"Authorization": "Bearer reviewer-secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reviewer_identity_verified"] is True
    assert body["raw_submission_stored"] is False
    assert body["publication_authorized"] is False


def test_publication_transition_requires_separate_publisher_and_does_not_write(monkeypatch, tmp_path):
    client = configure(monkeypatch, tmp_path)
    package_id = client.post("/api/external-review/packages", json=review_package(), headers={"Authorization": "Bearer submit-secret"}).json()["package_id"]
    correction_receipt_id = client.post(
        "/api/external-review/corrections",
        json=correction(package_id),
        headers={"Authorization": "Bearer reviewer-secret"},
    ).json()["correction_receipt_id"]
    payload = {
        "schema_version": "1.0.0",
        "transition_type": "external_framework_wiki_publication_transition",
        "package_id": package_id,
        "correction_receipt_id": correction_receipt_id,
        "publisher_ref": "publisher:test",
        "target_path": "docs/external-frameworks/reports/decisionassure.compatibility.json",
        "decision": "ALLOW_PUBLICATION_CANDIDATE",
        "source_commit_ref": "commit:reviewed-source",
        "evidence_references": [correction_receipt_id],
        "publication_executed": False,
        "boundary": {
            "transition_is_not_repository_write": True,
            "transition_is_not_certification": True,
            "transition_creates_no_standing": True,
            "separate_repository_mutation_required": True,
        },
    }
    unauthorized = client.post("/api/external-review/publication-transitions", json=payload, headers={"Authorization": "Bearer reviewer-secret"})
    assert unauthorized.status_code == 403
    accepted = client.post("/api/external-review/publication-transitions", json=payload, headers={"Authorization": "Bearer publisher-secret"})
    assert accepted.status_code == 200
    body = accepted.json()
    assert body["publisher_identity_verified"] is True
    assert body["publisher_delegation_verified"] is True
    assert body["publication_scope_verified"] is True
    assert body["publication_executed"] is False
    assert body["repository_mutation_authorized"] is False
    assert body["required_next_transition"] == "separately_authorized_repository_mutation"


def test_publication_identity_conflict_fails_closed(monkeypatch, tmp_path):
    client = configure(monkeypatch, tmp_path)
    package_id = client.post("/api/external-review/packages", json=review_package(), headers={"Authorization": "Bearer submit-secret"}).json()["package_id"]
    correction_receipt_id = client.post("/api/external-review/corrections", json=correction(package_id), headers={"Authorization": "Bearer reviewer-secret"}).json()["correction_receipt_id"]
    payload = {
        "schema_version": "1.0.0",
        "transition_type": "external_framework_wiki_publication_transition",
        "package_id": package_id,
        "correction_receipt_id": correction_receipt_id,
        "publisher_ref": "publisher:test",
        "target_path": "docs/external-frameworks/reports/decisionassure.compatibility.json",
        "decision": "REVIEW_REQUIRED",
        "source_commit_ref": "commit:one",
        "evidence_references": [correction_receipt_id],
        "publication_executed": False,
        "boundary": {
            "transition_is_not_repository_write": True,
            "transition_is_not_certification": True,
            "transition_creates_no_standing": True,
            "separate_repository_mutation_required": True,
        },
    }
    assert client.post("/api/external-review/publication-transitions", json=payload, headers={"Authorization": "Bearer publisher-secret"}).status_code == 200
    payload["source_commit_ref"] = "commit:two"
    conflict = client.post("/api/external-review/publication-transitions", json=payload, headers={"Authorization": "Bearer publisher-secret"})
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["reason"] == "publication_transition_conflict"
