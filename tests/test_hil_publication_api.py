from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app

PRIMARY = "52102cccb9ba9016c76434a64e22031b6a8c3edd3b8806e7b664e609216b2946"
PROMPT = "0ebe215318b4eeeb8ed6422e0954372c314fadc8fac9254e452bc7670a1b9922"


def _manifest(pdf: bytes) -> dict:
    return {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1",
        "primary_version": "v0.5",
        "primary_sha256": PRIMARY,
        "protocol_version": "HIL-PROTOCOL-v1.0",
        "prompt_version": "HIL-PROMPT-v1.0",
        "prompt_sha256": PROMPT,
        "response_sha256": hashlib.sha256(pdf).hexdigest(),
        "model": "test-model",
        "provider": "test-provider",
        "generated_at": None,
        "conversation_reference": None,
        "producer_signature": {"state": "UNAVAILABLE", "scheme": None, "value": None, "key_id": None},
    }


def _configure(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
    monkeypatch.setenv("STEGVERSE_HIL_REVIEW_TOKEN", "review-secret")
    monkeypatch.setenv("STEGVERSE_HIL_PUBLICATION_TOKEN", "publication-secret")


def _submit(client: TestClient, consent: str = "public") -> str:
    pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
    response = client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", pdf, "application/pdf"),
            "provenance_manifest": ("response.provenance.json", json.dumps(_manifest(pdf)), "application/json"),
        },
        data={
            "participant_identifier": "Participant One",
            "publication_consent": consent,
            "primary_sha256": PRIMARY,
            "model_response_declared_unedited": "true",
            "participant_consent_authority_acknowledged": "true",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["submission_id"]


def _review(client: TestClient, submission_id: str, decision: str = "ACCEPT_PRIVATE") -> None:
    response = client.post(
        f"/api/hil/submissions/{submission_id}/review-decisions",
        headers={"X-SteGVerse-HIL-Review-Token": "review-secret"},
        data={"decision": decision, "reviewer": "reviewer", "notes": "checked"},
    )
    assert response.status_code == 200, response.text


def _publish(client: TestClient, submission_id: str, response_id: str = "HIL-RESP-2026-0001"):
    return client.post(
        f"/api/hil/submissions/{submission_id}/publication-decisions",
        headers={"X-SteGVerse-HIL-Publication-Token": "publication-secret"},
        data={
            "response_id": response_id,
            "publisher": "authorized-publisher",
            "participant_display_name": "Participant One",
            "artifact_public_path": f"data/hil-responses/{response_id}.pdf",
        },
    )


def test_publication_requires_private_acceptance(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    client = TestClient(app)
    submission_id = _submit(client)
    response = _publish(client, submission_id)
    assert response.status_code == 409
    assert response.json()["detail"] == "hil_private_acceptance_required"


def test_publication_requires_public_or_anonymous_consent(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    client = TestClient(app)
    submission_id = _submit(client, consent="private")
    _review(client, submission_id)
    response = _publish(client, submission_id)
    assert response.status_code == 409
    assert response.json()["detail"] == "hil_publication_consent_required"


def test_publication_is_append_only_and_publicly_readable(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    client = TestClient(app)
    submission_id = _submit(client)
    _review(client, submission_id)
    response = _publish(client, submission_id)
    assert response.status_code == 200, response.text
    record = response.json()
    assert record["schema_version"] == "HIL-PUBLICATION-RECORD-v1"
    assert record["response_id"] == "HIL-RESP-2026-0001"
    assert record["authority"]["public_projection_authorized"] is True
    assert record["authority"]["execution"] is False
    assert record["authority"]["master_record_append"] is False
    assert record["publication_record_sha256"]

    fetched = client.get("/api/hil/publications/HIL-RESP-2026-0001")
    assert fetched.status_code == 200
    assert fetched.json()["publication_record_sha256"] == record["publication_record_sha256"]

    duplicate = _publish(client, submission_id, response_id="HIL-RESP-2026-0002")
    assert duplicate.status_code == 409
    reused_id_submission = _submit(client)
    _review(client, reused_id_submission)
    reused = _publish(client, reused_id_submission, response_id="HIL-RESP-2026-0001")
    assert reused.status_code == 409


def test_anonymous_publication_suppresses_display_name(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    client = TestClient(app)
    submission_id = _submit(client, consent="anonymous")
    _review(client, submission_id)
    response = _publish(client, submission_id)
    assert response.status_code == 200
    assert response.json()["participant_display_name"] is None
