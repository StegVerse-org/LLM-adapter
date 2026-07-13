from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from llm_adapter import external_review_api
from llm_adapter.external_review_store import ExternalReviewStore

COMPATIBILITY_RECEIPT = "external-compatibility-receipt:sha256:" + "b" * 64


def package() -> dict:
    return {
        "packet_type": "external_framework_cooperative_review_package",
        "schema_version": "1.0.0",
        "framework_id": "decisionassure",
        "framework_name": "DecisionAssure",
        "compatibility_receipt_id": COMPATIBILITY_RECEIPT,
        "submission_sha256": "a" * 64,
        "compatibility_result": "COMPATIBILITY_EVIDENCE_READY",
        "submitter_opt_in": True,
        "review_scope": ["evidence_model"],
        "evidence_references": ["evidence:test:1"],
        "publication_requested": False,
        "raw_submission_included": False,
        "contact_reference": None,
        "boundary": {
            "package_is_publication_authority": False,
            "package_is_certification": False,
            "package_creates_standing": False,
            "review_may_change_result_without_receipt": False,
        },
    }


def package_id() -> str:
    material = COMPATIBILITY_RECEIPT + "a" * 64
    return "external-review-package:sha256:" + hashlib.sha256(material.encode()).hexdigest()


def correction() -> dict:
    return {
        "packet_type": "external_framework_correction_request",
        "schema_version": "1.0.0",
        "package_id": package_id(),
        "challenged_receipt_id": COMPATIBILITY_RECEIPT,
        "challenged_submission_sha256": "a" * 64,
        "reviewer_ref": "reviewer:test",
        "decision": "UPHOLD",
        "reviewed_fields": ["evidence_model"],
        "supporting_evidence_references": ["evidence:review:test"],
        "rationale": "The submitted evidence model matches the reviewed structural claim.",
        "replacement_result": None,
        "replacement_receipt_id": None,
        "publication_authorized": False,
    }


def configure(monkeypatch, tmp_path) -> TestClient:
    """Create an isolated application for the review router under test.

    Production uses ``combined_gateway.app``. These focused tests intentionally mount only
    the review router so unrelated gateway routers, middleware, import-time databases, and
    environment configuration cannot change review-contract outcomes.
    """
    monkeypatch.setattr(external_review_api, "store", ExternalReviewStore(str(tmp_path / "review.db")))
    monkeypatch.setenv("STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN", "submit-secret")
    monkeypatch.setenv("STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY", "receipt-secret")
    now = datetime.now(timezone.utc)
    monkeypatch.setenv(
        "STEGVERSE_EXTERNAL_REVIEWERS_JSON",
        json.dumps({
            "reviewer:test": {
                "token_sha256": hashlib.sha256(b"reviewer-secret").hexdigest(),
                "delegation_ref": "delegation:external-review:test",
                "scopes": ["field:evidence_model"],
                "valid_from": (now - timedelta(minutes=5)).isoformat(),
                "valid_until": (now + timedelta(hours=1)).isoformat(),
            }
        }),
    )
    app = FastAPI()
    app.include_router(external_review_api.router)
    return TestClient(app)


def test_package_only_intake_is_authenticated_append_only_and_idempotent(monkeypatch, tmp_path):
    client = configure(monkeypatch, tmp_path)
    assert client.post("/api/external-review/packages", json=package()).status_code == 401
    headers = {"Authorization": "Bearer submit-secret"}
    created = client.post("/api/external-review/packages", json=package(), headers=headers)
    assert created.status_code == 200
    body = created.json()
    assert body["created"] is True
    assert body["package_id"] == package_id()
    assert body["review_state"] == "AWAITING_DELEGATED_REVIEW"
    assert body["raw_submission_stored"] is False
    assert body["wiki_record_created"] is False
    assert body["publication_authorized"] is False
    assert body["intake_receipt_id"].startswith("external-review-intake-receipt:hmac-sha256:")
    repeated = client.post("/api/external-review/packages", json=package(), headers=headers)
    assert repeated.status_code == 200
    assert repeated.json()["created"] is False


def test_package_rejects_raw_submission_and_conflicting_content(monkeypatch, tmp_path):
    client = configure(monkeypatch, tmp_path)
    headers = {"Authorization": "Bearer submit-secret"}
    raw = package()
    raw["raw_submission_included"] = True
    assert client.post("/api/external-review/packages", json=raw, headers=headers).status_code == 422
    assert client.post("/api/external-review/packages", json=package(), headers=headers).status_code == 200
    changed = package()
    changed["review_scope"] = ["policy_or_rule_model"]
    conflict = client.post("/api/external-review/packages", json=changed, headers=headers)
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["reason"] == "review_package_conflict"


def test_delegated_reviewer_can_issue_one_identity_bound_receipt(monkeypatch, tmp_path):
    client = configure(monkeypatch, tmp_path)
    client.post("/api/external-review/packages", json=package(), headers={"Authorization": "Bearer submit-secret"})
    wrong = client.post("/api/external-review/corrections", json=correction(), headers={"Authorization": "Bearer wrong"})
    assert wrong.status_code == 403
    accepted = client.post("/api/external-review/corrections", json=correction(), headers={"Authorization": "Bearer reviewer-secret"})
    assert accepted.status_code == 200
    body = accepted.json()
    assert body["created"] is True
    assert body["reviewer_identity_verified"] is True
    assert body["reviewer_delegation_verified"] is True
    assert body["review_scope_verified"] is True
    assert body["publication_authorized"] is False
    assert body["correction_receipt_id"].startswith("external-framework-correction-receipt:hmac-sha256:")
    repeated = client.post("/api/external-review/corrections", json=correction(), headers={"Authorization": "Bearer reviewer-secret"})
    assert repeated.status_code == 200
    assert repeated.json()["created"] is False
    changed = correction()
    changed["rationale"] = "Conflicting rationale for the same challenged receipt."
    conflict = client.post("/api/external-review/corrections", json=changed, headers={"Authorization": "Bearer reviewer-secret"})
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["reason"] == "correction_conflict"


def test_scope_and_identity_drift_fail_closed(monkeypatch, tmp_path):
    client = configure(monkeypatch, tmp_path)
    client.post("/api/external-review/packages", json=package(), headers={"Authorization": "Bearer submit-secret"})
    drift = correction()
    drift["challenged_submission_sha256"] = "c" * 64
    response = client.post("/api/external-review/corrections", json=drift, headers={"Authorization": "Bearer reviewer-secret"})
    assert response.status_code == 409
    assert response.json()["detail"]["reason"] == "challenged_submission_identity_mismatch"
    out_of_scope = correction()
    out_of_scope["reviewed_fields"] = ["policy_or_rule_model"]
    response = client.post("/api/external-review/corrections", json=out_of_scope, headers={"Authorization": "Bearer reviewer-secret"})
    assert response.status_code == 403
    assert response.json()["detail"]["reason"] == "review_scope_not_delegated"


def test_expired_reviewer_delegation_is_rejected(monkeypatch, tmp_path):
    client = configure(monkeypatch, tmp_path)
    client.post("/api/external-review/packages", json=package(), headers={"Authorization": "Bearer submit-secret"})
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    monkeypatch.setenv(
        "STEGVERSE_EXTERNAL_REVIEWERS_JSON",
        json.dumps({"reviewer:test": {
            "token_sha256": hashlib.sha256(b"reviewer-secret").hexdigest(),
            "delegation_ref": "delegation:expired",
            "scopes": ["field:evidence_model"],
            "valid_until": past.isoformat(),
        }}),
    )
    response = client.post("/api/external-review/corrections", json=correction(), headers={"Authorization": "Bearer reviewer-secret"})
    assert response.status_code == 403
    assert response.json()["detail"]["reason"] == "reviewer_delegation_expired"
