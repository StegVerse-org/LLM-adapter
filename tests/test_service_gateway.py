import hashlib
import json

from fastapi.testclient import TestClient

from llm_adapter.service_gateway import app


def _tvc_receipt():
    return {
        "role": "service_gateway_intake",
        "admissible": True,
        "binding_matched": True,
        "allowed_keys": [
            "service-gateway/hil-intake/storage-root",
            "service-gateway/hil-intake/receipt-key",
        ],
        "denied_keys": [],
        "decision_id": "sha256:test-decision",
        "policy_hash": "sha256:test-policy",
    }


def _configure(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_TVC_DECISION_RECEIPT", json.dumps(_tvc_receipt()))
    monkeypatch.setenv("STEGVERSE_HIL_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_HIL_RECEIPT_KEY", "x" * 64)


def test_ready_requires_tvc_and_storage(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["protocol"] == "HIL-RECEIVER-RECEIPT-v2"

    site_ready = client.get("/api/hil/readiness")
    assert site_ready.status_code == 200
    payload = site_ready.json()
    assert payload["state"] == "READY"
    assert payload["primary_version"] == "v1.1"
    assert payload["provenance_manifest_schema"] == "HIL-RESPONSE-PROVENANCE-v1.1"


def test_pdf_intake_is_durable_and_idempotent(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    client = TestClient(app)
    pdf = b"%PDF-1.7\nfixture\n%%EOF\n"
    document_hash = "sha256:" + hashlib.sha256(pdf).hexdigest()
    metadata = {
        "packet_id": "research-packet-001",
        "document_hash": document_hash,
        "protocol": "HIL-RESPONSE-PACKET-v1",
    }
    files = {"document": ("experiment.pdf", pdf, "application/pdf")}
    data = {"metadata": json.dumps(metadata)}

    first = client.post("/v1/hil/intake", files=files, data=data)
    assert first.status_code == 200
    receipt = first.json()
    assert receipt["status"] == "SUBMISSION_ACCEPTED"
    assert receipt["document_hash"] == document_hash
    assert receipt["signature"].startswith("hmac-sha256:")
    assert (tmp_path / "packets" / "research-packet-001" / "document.pdf").read_bytes() == pdf
    assert (tmp_path / "receipts" / "research-packet-001.json").exists()

    duplicate = client.post("/v1/hil/intake", files=files, data=data)
    assert duplicate.status_code == 200
    assert duplicate.json() == receipt


def test_site_submission_contract(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    client = TestClient(app)
    pdf = b"%PDF-1.7\nsite fixture\n%%EOF\n"
    response_hash = hashlib.sha256(pdf).hexdigest()
    manifest = {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1.1",
        "primary_version": "v1.1",
        "primary_sha256": "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462",
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c",
        "response_sha256": response_hash,
    }
    response = client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", pdf, "application/pdf"),
            "provenance_manifest": ("response.pdf.provenance.json", json.dumps(manifest), "application/json"),
        },
        data={
            "participant_identifier": "not_provided",
            "publication_consent": "not_provided",
            "primary_sha256": manifest["primary_sha256"],
            "prompt_sha256": manifest["prompt_sha256"],
            "model_response_declared_unedited": "true",
            "participant_consent_authority_acknowledged": "true",
        },
    )
    assert response.status_code == 200
    receipt = response.json()
    assert receipt["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
    assert receipt["submitted_file_sha256"] == response_hash
    assert receipt["chain_validation_state"] == "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED"
    unsigned = dict(receipt)
    receipt_hash = unsigned.pop("receipt_sha256")
    unsigned.pop("receiver_signature")
    assert receipt_hash == hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_intake_scope_cannot_use_provider_keys(monkeypatch, tmp_path):
    receipt = _tvc_receipt()
    receipt["allowed_keys"].append("service-gateway/provider/token")
    receipt["denied_keys"] = ["service-gateway/provider/token"]
    monkeypatch.setenv("STEGVERSE_TVC_DECISION_RECEIPT", json.dumps(receipt))
    monkeypatch.setenv("STEGVERSE_HIL_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_HIL_RECEIPT_KEY", "x" * 64)
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert "tvc_intake_scope_invalid" in response.text
