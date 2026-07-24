from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app

PRIMARY = "52102cccb9ba9016c76434a64e22031b6a8c3edd3b8806e7b664e609216b2946"
PROMPT = "0ebe215318b4eeeb8ed6422e0954372c314fadc8fac9254e452bc7670a1b9922"


def _manifest(pdf: bytes, *, response_sha256: str | None = None) -> dict:
    return {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1",
        "primary_version": "v0.5",
        "primary_sha256": PRIMARY,
        "protocol_version": "HIL-PROTOCOL-v1.0",
        "prompt_version": "HIL-PROMPT-v1.0",
        "prompt_sha256": PROMPT,
        "response_sha256": response_sha256 or hashlib.sha256(pdf).hexdigest(),
        "model": "test-model",
        "provider": "test-provider",
        "conversation_reference": None,
        "producer_signature": {
            "state": "UNAVAILABLE",
            "scheme": None,
            "value": None,
            "key_id": None,
        },
    }


def _enable(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")


def _submit(client: TestClient, pdf: bytes, manifest: dict, consent: str = "anonymous"):
    return client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", pdf, "application/pdf"),
            "provenance_manifest": (
                "response.provenance.json",
                json.dumps(manifest).encode("utf-8"),
                "application/json",
            ),
        },
        data={
            "participant_identifier": "tester",
            "publication_consent": consent,
            "primary_sha256": PRIMARY,
            "model_response_declared_unedited": "true",
            "participant_consent_authority_acknowledged": "true",
        },
    )


def test_hil_readiness_fails_closed_when_disabled(monkeypatch):
    monkeypatch.setenv("STEGVERSE_HIL_INTAKE_ENABLED", "false")
    client = TestClient(app)
    payload = client.get("/api/hil/readiness").json()
    assert payload["state"] == "CONFIGURATION_REQUIRED"
    assert "hil_intake_disabled" in payload["blockers"]
    assert payload["provenance_manifest_required"] is True
    assert payload["publication_authority"] is False


def test_hil_submission_preserves_exact_bytes_manifest_and_issues_receipt_v2(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    client = TestClient(app)
    pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
    response = _submit(client, pdf, _manifest(pdf))
    assert response.status_code == 200, response.text
    receipt = response.json()
    assert receipt["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
    assert receipt["validation_state"] == "PENDING_REVIEW"
    assert receipt["chain_validation_state"] == "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED"
    assert receipt["submitted_file_sha256"] == hashlib.sha256(pdf).hexdigest()
    assert receipt["authority"]["publication"] is False

    stored = list((tmp_path / "originals").glob("*.pdf"))
    manifests = list((tmp_path / "provenance").glob("*.json"))
    assert len(stored) == 1
    assert len(manifests) == 1
    assert stored[0].read_bytes() == pdf
    persisted_manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert persisted_manifest["response_sha256"] == hashlib.sha256(pdf).hexdigest()


def test_hil_submission_rejects_response_hash_mismatch(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    client = TestClient(app)
    pdf = b"%PDF-1.7\n%%EOF\n"
    response = _submit(client, pdf, _manifest(pdf, response_sha256="0" * 64))
    assert response.status_code == 400
    assert response.json()["detail"] == "provenance_response_sha256_mismatch"
    assert not (tmp_path / "originals").exists()


def test_hil_submission_rejects_wrong_primary_chain(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    client = TestClient(app)
    pdf = b"%PDF-1.7\n%%EOF\n"
    manifest = _manifest(pdf)
    manifest["primary_sha256"] = "1" * 64
    response = _submit(client, pdf, manifest)
    assert response.status_code == 400
    assert response.json()["detail"] == "provenance_primary_sha256_mismatch"


def test_hil_submission_rejects_active_content(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    client = TestClient(app)
    pdf = b"%PDF-1.7\n/JavaScript\n%%EOF\n"
    response = _submit(client, pdf, _manifest(pdf), consent="private")
    assert response.status_code == 400
    assert "active_pdf_content_detected" in response.json()["detail"]


def test_private_review_requires_configured_token(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    monkeypatch.delenv("STEGVERSE_HIL_REVIEW_TOKEN", raising=False)
    client = TestClient(app)
    response = client.get("/api/hil/submissions/unknown/review-state")
    assert response.status_code == 503
    assert response.json()["detail"] == "hil_review_not_configured"


def test_private_review_accepts_once_without_publication_authority(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_HIL_REVIEW_TOKEN", "test-review-token")
    client = TestClient(app)
    pdf = b"%PDF-1.7\n%%EOF\n"
    submission = _submit(client, pdf, _manifest(pdf)).json()
    submission_id = submission["submission_id"]
    headers = {"X-SteGVerse-HIL-Review-Token": "test-review-token"}

    initial = client.get(
        f"/api/hil/submissions/{submission_id}/review-state", headers=headers
    )
    assert initial.status_code == 200
    assert initial.json()["review"] is None
    assert initial.json()["artifact_bytes_exposed"] is False

    decision = client.post(
        f"/api/hil/submissions/{submission_id}/review-decisions",
        headers=headers,
        data={
            "decision": "ACCEPT_PRIVATE",
            "reviewer": "reviewer-1",
            "notes": "Hash chain matches; retained for private analysis.",
        },
    )
    assert decision.status_code == 200, decision.text
    receipt = decision.json()
    assert receipt["schema_version"] == "HIL-PRIVATE-REVIEW-RECEIPT-v1"
    assert receipt["decision"] == "ACCEPT_PRIVATE"
    assert receipt["authority"]["publication"] is False
    assert receipt["authority"]["public_acceptance"] is False

    repeated = client.post(
        f"/api/hil/submissions/{submission_id}/review-decisions",
        headers=headers,
        data={"decision": "QUARANTINE", "reviewer": "reviewer-2", "notes": ""},
    )
    assert repeated.status_code == 409
    assert repeated.json()["detail"] == "hil_review_already_recorded"

    final = client.get(
        f"/api/hil/submissions/{submission_id}/review-state", headers=headers
    ).json()
    assert final["submission"]["validation_state"] == "ACCEPT_PRIVATE"
    assert final["review"]["decision"] == "ACCEPT_PRIVATE"
    assert final["authority"]["publication"] is False
