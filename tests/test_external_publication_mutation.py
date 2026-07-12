from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from llm_adapter import external_publication_mutation as mutation
from llm_adapter.combined_gateway import app


def seed_database(path: str) -> str:
    mutation.os.environ["STEGVERSE_EXTERNAL_REVIEW_DB"] = path
    with mutation._connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS review_packages (
            package_id TEXT PRIMARY KEY, framework_id TEXT NOT NULL,
            compatibility_receipt_id TEXT NOT NULL, submission_sha256 TEXT NOT NULL,
            content_sha256 TEXT NOT NULL, payload_json TEXT NOT NULL,
            intake_receipt_id TEXT NOT NULL, review_state TEXT NOT NULL, received_at TEXT NOT NULL)"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS correction_receipts (
            correction_receipt_id TEXT PRIMARY KEY, package_id TEXT NOT NULL,
            challenged_receipt_id TEXT NOT NULL, reviewer_ref TEXT NOT NULL,
            reviewer_delegation_ref TEXT NOT NULL, decision TEXT NOT NULL,
            content_sha256 TEXT NOT NULL, payload_json TEXT NOT NULL, issued_at TEXT NOT NULL)"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS publication_transitions (
            publication_transition_id TEXT PRIMARY KEY, package_id TEXT NOT NULL,
            correction_receipt_id TEXT NOT NULL, publisher_ref TEXT NOT NULL,
            publisher_delegation_ref TEXT NOT NULL, target_path TEXT NOT NULL,
            decision TEXT NOT NULL, content_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL, issued_at TEXT NOT NULL)"""
        )
        package_id = "external-review-package:sha256:" + "1" * 64
        correction_id = "external-framework-correction-receipt:hmac-sha256:" + "2" * 64
        publication_id = "external-framework-publication-transition:hmac-sha256:" + "3" * 64
        db.execute(
            "INSERT OR REPLACE INTO review_packages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (package_id, "decisionassure", "external-compatibility-receipt:sha256:" + "4" * 64,
             "5" * 64, "6" * 64, "{}", "intake:test", "PUBLICATION_TRANSITION_RECORDED", datetime.now(timezone.utc).isoformat()),
        )
        db.execute(
            "INSERT OR REPLACE INTO correction_receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (correction_id, package_id, "external-compatibility-receipt:sha256:" + "4" * 64,
             "reviewer:test", "delegation:reviewer:test", "UPHOLD", "7" * 64, "{}", datetime.now(timezone.utc).isoformat()),
        )
        db.execute(
            "INSERT OR REPLACE INTO publication_transitions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (publication_id, package_id, correction_id, "publisher:test", "delegation:publisher:test",
             "docs/external-frameworks/reports/decisionassure-reviewed.md", "ALLOW_PUBLICATION_CANDIDATE",
             "8" * 64, json.dumps({"source_commit_ref": "commit:test"}), datetime.now(timezone.utc).isoformat()),
        )
        db.commit()
    return publication_id


def configure(monkeypatch, tmp_path):
    publication_id = seed_database(str(tmp_path / "review.db"))
    token = "mutator-secret"
    now = datetime.now(timezone.utc)
    monkeypatch.setenv("STEGVERSE_EXTERNAL_MUTATION_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_EXTERNAL_GITHUB_TOKEN", "github-secret")
    monkeypatch.setenv("STEGVERSE_EXTERNAL_MUTATION_RECEIPT_KEY", "receipt-secret")
    monkeypatch.setenv("STEGVERSE_EXTERNAL_MUTATION_POLICY_REF", "policy:external-wiki:v1")
    monkeypatch.setenv(
        "STEGVERSE_EXTERNAL_MUTATORS_JSON",
        json.dumps({
            "mutator:test": {
                "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
                "delegation_ref": "delegation:mutator:test",
                "scopes": [
                    "repository:StegVerse-Labs/admissibility-wiki",
                    "path:docs/external-frameworks/*",
                    "framework:decisionassure",
                    "repository:mutate",
                ],
                "valid_from": (now - timedelta(minutes=5)).isoformat(),
                "valid_until": (now + timedelta(hours=1)).isoformat(),
            }
        }),
    )
    return publication_id, token


def request(publication_id: str) -> dict:
    return {
        "schema_version": "1.0.0",
        "request_type": "external_framework_repository_mutation_request",
        "publication_transition_id": publication_id,
        "actor_ref": "mutator:test",
        "repository_full_name": "StegVerse-Labs/admissibility-wiki",
        "target_path": "docs/external-frameworks/reports/decisionassure-reviewed.md",
        "content": "# Reviewed DecisionAssure finding\n",
        "expected_repository_head_sha": "a" * 40,
        "expected_target_blob_sha": None,
        "commit_message": "Publish reviewed DecisionAssure finding",
        "authority_ref": "authority:wiki-mutation:test",
        "delegation_ref": "delegation:mutator:test",
        "policy_ref": "policy:external-wiki:v1",
        "freshness_valid_until": (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat(),
        "branch": "main",
    }


def test_mutation_disabled_fails_closed(monkeypatch, tmp_path):
    publication_id, token = configure(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_EXTERNAL_MUTATION_ENABLED", "false")
    response = TestClient(app).post(
        "/api/external-review/repository-mutations",
        json=request(publication_id),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "repository_mutation_disabled"


def test_commit_time_revalidation_and_confirmed_github_receipt(monkeypatch, tmp_path):
    publication_id, token = configure(monkeypatch, tmp_path)
    calls = []

    def fake_github(method, url, github_token, payload=None):
        calls.append((method, url, payload))
        if "/git/ref/heads/main" in url:
            return {"object": {"sha": "a" * 40}}
        if method == "GET" and "/contents/" in url:
            raise mutation.HTTPException(status_code=502, detail={"reason": "github_api_error", "status": 404})
        return {"commit": {"sha": "b" * 40}, "content": {"sha": "c" * 40}}

    monkeypatch.setattr(mutation, "_github_json", fake_github)
    response = TestClient(app).post(
        "/api/external-review/repository-mutations",
        json=request(publication_id),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["commit_sha"] == "b" * 40
    assert body["new_blob_sha"] == "c" * 40
    assert body["commit_time_revalidation"]["publication_identity"] == "PASS"
    assert body["boundary"]["mutation_receipt_is_certification"] is False
    assert any(call[0] == "PUT" for call in calls)


def test_repository_head_drift_blocks_before_write(monkeypatch, tmp_path):
    publication_id, token = configure(monkeypatch, tmp_path)
    writes = []

    def fake_github(method, url, github_token, payload=None):
        if method == "PUT":
            writes.append(url)
        return {"object": {"sha": "d" * 40}}

    monkeypatch.setattr(mutation, "_github_json", fake_github)
    response = TestClient(app).post(
        "/api/external-review/repository-mutations",
        json=request(publication_id),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["reason"] == "repository_head_drift"
    assert writes == []


def test_wrong_policy_and_path_fail_closed(monkeypatch, tmp_path):
    publication_id, token = configure(monkeypatch, tmp_path)
    bad_policy = request(publication_id)
    bad_policy["policy_ref"] = "policy:wrong"
    response = TestClient(app).post(
        "/api/external-review/repository-mutations",
        json=bad_policy,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["reason"] == "commit_time_policy_mismatch"

    bad_path = request(publication_id)
    bad_path["target_path"] = "README.md"
    response = TestClient(app).post(
        "/api/external-review/repository-mutations",
        json=bad_path,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
