from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app

PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"


def _manifest(pdf: bytes, *, response_sha256: str | None = None, metadata: bool = True) -> dict:
    payload = {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1.1",
        "primary_version": "v1.1",
        "primary_sha256": PRIMARY,
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": PROMPT,
        "response_sha256": response_sha256 or hashlib.sha256(pdf).hexdigest(),
        "model": "test-model" if metadata else None,
        "provider": "test-provider" if metadata else None,
        "conversation_reference": None,
        "producer_signature": {"state": "UNAVAILABLE", "scheme": None, "value": None, "key_id": None},
    }
    return payload


def _enable(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")


def _submit(client: TestClient, pdf: bytes, manifest: dict, data: dict | None = None):
    form = {"primary_sha256": PRIMARY, "prompt_sha256": PROMPT}
    if data:
        form.update(data)
    return client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", pdf, "application/pdf"),
            "provenance_manifest": ("response.provenance.json", json.dumps(manifest).encode(), "application/json"),
        },
        data=form,
    )


def test_hil_readiness_reports_v1_1_and_fails_closed_when_disabled(monkeypatch):
    monkeypatch.setenv("STEGVERSE_HIL_INTAKE_ENABLED", "false")
    payload = TestClient(app).get("/api/hil/readiness").json()
    assert payload["state"] == "CONFIGURATION_REQUIRED"
    assert "hil_intake_disabled" in payload["blockers"]
    assert payload["primary_version"] == "v1.1"
    assert payload["primary_sha256"] == PRIMARY
    assert payload["prompt_sha256"] == PROMPT
    assert payload["participant_metadata_required"] is False


def test_minimal_upload_preserves_exact_bytes_and_issues_receipt(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    client = TestClient(app)
    pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
    response = _submit(client, pdf, _manifest(pdf, metadata=False))
    assert response.status_code == 200, response.text
    receipt = response.json()
    assert receipt["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
    assert receipt["participant_metadata_state"] == "NOT_PROVIDED"
    assert receipt["validation_state"] == "PENDING_REVIEW"
    assert receipt["submitted_file_sha256"] == hashlib.sha256(pdf).hexdigest()
    assert receipt["authority"]["publication"] is False
    stored = list((tmp_path / "originals").glob("*.pdf"))
    manifests = list((tmp_path / "provenance").glob("*.json"))
    assert len(stored) == 1 and stored[0].read_bytes() == pdf
    assert len(manifests) == 1


def test_optional_metadata_is_preserved_without_becoming_authority(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    pdf = b"%PDF-1.7\n%%EOF\n"
    response = _submit(
        TestClient(app), pdf, _manifest(pdf),
        {"participant_identifier": "Experiment Author", "publication_consent": "public", "model_response_declared_unedited": "true", "participant_consent_authority_acknowledged": "true"},
    )
    assert response.status_code == 200, response.text
    receipt = response.json()
    assert receipt["participant_metadata_state"] == "PROVIDED"
    assert receipt["participant_declarations"]["model_response_declared_unedited"] is True
    assert receipt["authority"]["publication"] is False


def test_response_hash_mismatch_is_rejected(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    pdf = b"%PDF-1.7\n%%EOF\n"
    response = _submit(TestClient(app), pdf, _manifest(pdf, response_sha256="0" * 64))
    assert response.status_code == 400
    assert response.json()["detail"] == "provenance_response_sha256_mismatch"


def test_wrong_primary_chain_is_rejected(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    pdf = b"%PDF-1.7\n%%EOF\n"
    manifest = _manifest(pdf)
    manifest["primary_sha256"] = "1" * 64
    response = _submit(TestClient(app), pdf, manifest)
    assert response.status_code == 400
    assert response.json()["detail"] == "provenance_primary_sha256_mismatch"


def test_active_content_is_rejected(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    pdf = b"%PDF-1.7\n/JavaScript\n%%EOF\n"
    response = _submit(TestClient(app), pdf, _manifest(pdf))
    assert response.status_code == 400
    assert "active_pdf_content_detected" in response.json()["detail"]


def test_public_status_exposes_hash_state_without_private_metadata(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    client = TestClient(app)
    pdf = b"%PDF-1.7\nstatus proof\n%%EOF\n"
    receipt = _submit(
        client,
        pdf,
        _manifest(pdf),
        {"participant_identifier": "private-participant", "publication_consent": "private"},
    ).json()

    response = client.get(f"/api/hil/submissions/{receipt['submission_id']}/status")
    assert response.status_code == 200, response.text
    status = response.json()
    assert status["schema_version"] == "HIL-SUBMISSION-STATUS-v1"
    assert status["submission_id"] == receipt["submission_id"]
    assert status["submitted_file_sha256"] == hashlib.sha256(pdf).hexdigest()
    assert status["artifact_bytes_exposed"] is False
    assert status["participant_metadata_exposed"] is False
    assert status["storage_paths_exposed"] is False
    assert "participant_identifier" not in status
    assert "publication_consent" not in status
    assert "storage_path" not in status
    assert status["authority"] == {
        "execution": False,
        "acceptance": False,
        "publication": False,
        "master_record_append": False,
    }


def test_exact_bytes_requires_existing_tvc_review_auth_and_reconstructs_exact_pdf(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_HIL_REVIEW_TOKEN", "tvc-controlled-review-token")
    client = TestClient(app)
    pdf = b"%PDF-1.7\nexact restart bytes\n%%EOF\n"
    receipt = _submit(client, pdf, _manifest(pdf, metadata=False)).json()
    endpoint = f"/api/hil/submissions/{receipt['submission_id']}/exact-bytes"

    denied = client.get(endpoint)
    assert denied.status_code == 403
    assert denied.json()["detail"] == "hil_review_forbidden"

    verified = client.get(
        endpoint,
        headers={"X-SteGVerse-HIL-Review-Token": "tvc-controlled-review-token"},
    )
    assert verified.status_code == 200, verified.text
    assert verified.content == pdf
    assert verified.headers["content-type"].startswith("application/pdf")
    assert verified.headers["x-stegverse-hil-submitted-sha256"] == hashlib.sha256(pdf).hexdigest()
    assert verified.headers["x-stegverse-hil-reconstruction-state"] == "EXACT_BYTES_HASH_VERIFIED"
    assert verified.headers["cache-control"] == "no-store"


def test_exact_byte_reconstruction_fails_closed_after_artifact_tamper(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_HIL_REVIEW_TOKEN", "tvc-controlled-review-token")
    client = TestClient(app)
    pdf = b"%PDF-1.7\noriginal bytes\n%%EOF\n"
    receipt = _submit(client, pdf, _manifest(pdf, metadata=False)).json()
    stored = next((tmp_path / "originals").glob("*.pdf"))
    stored.write_bytes(b"%PDF-1.7\ntampered bytes\n%%EOF\n")

    response = client.get(
        f"/api/hil/submissions/{receipt['submission_id']}/exact-bytes",
        headers={"X-SteGVerse-HIL-Review-Token": "tvc-controlled-review-token"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "hil_exact_bytes_hash_mismatch"


def test_private_review_remains_separately_authenticated_and_write_once(monkeypatch, tmp_path):
    _enable(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_HIL_REVIEW_TOKEN", "test-review-token")
    client = TestClient(app)
    pdf = b"%PDF-1.7\n%%EOF\n"
    submission_id = _submit(client, pdf, _manifest(pdf, metadata=False)).json()["submission_id"]
    headers = {"X-SteGVerse-HIL-Review-Token": "test-review-token"}
    decision = client.post(
        f"/api/hil/submissions/{submission_id}/review-decisions",
        headers=headers,
        data={"decision": "ACCEPT_PRIVATE", "reviewer": "reviewer-1", "notes": "Private acceptance only."},
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["authority"]["publication"] is False
    repeated = client.post(
        f"/api/hil/submissions/{submission_id}/review-decisions",
        headers=headers,
        data={"decision": "QUARANTINE", "reviewer": "reviewer-2", "notes": ""},
    )
    assert repeated.status_code == 409
    state = client.get(f"/api/hil/submissions/{submission_id}/review-state", headers=headers).json()
    assert state["submission"]["validation_state"] == "ACCEPT_PRIVATE"
