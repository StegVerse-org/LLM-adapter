from __future__ import annotations

import hashlib
import json
import sqlite3

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app

PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
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
        "model": "controlled-cycle-model",
        "provider": "controlled-cycle-provider",
        "generated_at": "2026-07-24T00:00:00Z",
        "conversation_reference": "controlled-cycle-fixture",
        "producer_signature": {
            "state": "UNAVAILABLE",
            "scheme": None,
            "value": None,
            "key_id": None,
        },
    }


def test_hil_complete_controlled_cycle_survives_client_restart(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
    monkeypatch.setenv("STEGVERSE_HIL_REVIEW_TOKEN", "review-secret")
    monkeypatch.setenv("STEGVERSE_HIL_PUBLICATION_TOKEN", "publication-secret")

    pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
    response_hash = hashlib.sha256(pdf).hexdigest()

    first_client = TestClient(app)
    readiness = first_client.get("/api/hil/readiness").json()
    assert readiness["state"] == "READY"
    assert readiness["primary_sha256"] == PRIMARY
    assert readiness["prompt_sha256"] == PROMPT
    assert readiness["private_review_configured"] is True

    submitted = first_client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", pdf, "application/pdf"),
            "provenance_manifest": (
                "response.provenance.json",
                json.dumps(_manifest(pdf)).encode("utf-8"),
                "application/json",
            ),
        },
        data={
            "participant_identifier": "Controlled Participant",
            "publication_consent": "public",
            "primary_sha256": PRIMARY,
            "model_response_declared_unedited": "true",
            "participant_consent_authority_acknowledged": "true",
        },
    )
    assert submitted.status_code == 200, submitted.text
    receiver_receipt = submitted.json()
    submission_id = receiver_receipt["submission_id"]
    assert receiver_receipt["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
    assert receiver_receipt["submitted_file_sha256"] == response_hash
    assert receiver_receipt["chain_validation_state"] == "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED"

    second_client = TestClient(app)
    review_state = second_client.get(
        f"/api/hil/submissions/{submission_id}/review-state",
        headers={"X-SteGVerse-HIL-Review-Token": "review-secret"},
    )
    assert review_state.status_code == 200, review_state.text
    assert review_state.json()["submission"]["submitted_file_sha256"] == response_hash

    reviewed = second_client.post(
        f"/api/hil/submissions/{submission_id}/review-decisions",
        headers={"X-SteGVerse-HIL-Review-Token": "review-secret"},
        data={"decision": "ACCEPT_PRIVATE", "reviewer": "controlled-reviewer", "notes": "fixture accepted"},
    )
    assert reviewed.status_code == 200, reviewed.text
    private_receipt = reviewed.json()
    assert private_receipt["schema_version"] == "HIL-PRIVATE-REVIEW-RECEIPT-v1"
    assert private_receipt["authority"]["publication"] is False

    published = second_client.post(
        f"/api/hil/submissions/{submission_id}/publication-decisions",
        headers={"X-SteGVerse-HIL-Publication-Token": "publication-secret"},
        data={
            "response_id": "HIL-RESP-CONTROLLED-0001",
            "publisher": "controlled-publisher",
            "participant_display_name": "Controlled Participant",
            "artifact_public_path": "data/hil-responses/HIL-RESP-CONTROLLED-0001.pdf",
        },
    )
    assert published.status_code == 200, published.text
    publication = published.json()
    assert publication["schema_version"] == "HIL-PUBLICATION-RECORD-v1"
    assert publication["response_sha256"] == response_hash
    assert publication["authority"] == {
        "public_projection_authorized": True,
        "execution": False,
        "endorsement": False,
        "master_record_append": False,
    }

    third_client = TestClient(app)
    fetched = third_client.get("/api/hil/publications/HIL-RESP-CONTROLLED-0001")
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["publication_record_sha256"] == publication["publication_record_sha256"]

    assert list((tmp_path / "originals").glob("*.pdf"))[0].read_bytes() == pdf
    persisted_manifest = json.loads(list((tmp_path / "provenance").glob("*.json"))[0].read_text(encoding="utf-8"))
    assert persisted_manifest["response_sha256"] == response_hash

    with sqlite3.connect(tmp_path / "hil-intake.db") as connection:
        assert connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM submission_reviews").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM publications").fetchone()[0] == 1
