from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app
from llm_adapter.hil_intake_v1_1_api import (
    _build_transport_intent,
    _digest_uri,
    _hil_payload_binding,
    _validate_manifest,
)

PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"


def _manifest(pdf: bytes, prompt_sha256: str = PROMPT) -> bytes:
    return json.dumps({
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1.1",
        "primary_version": "v1.1",
        "primary_sha256": PRIMARY,
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": prompt_sha256,
        "response_sha256": hashlib.sha256(pdf).hexdigest(),
        "model": "test-model",
        "provider": "test-provider",
        "generated_at": "2026-07-23T00:00:00Z",
        "producer_signature": {
            "state": "UNAVAILABLE",
            "scheme": None,
            "value": None,
            "key_id": None,
        },
    }).encode("utf-8")


def _transport_intent(pdf: bytes, manifest: dict) -> dict:
    response_sha = hashlib.sha256(pdf).hexdigest()
    normalized = _validate_manifest(dict(manifest), response_sha)
    provenance_sha = _digest_uri(normalized)
    payload_hash = _digest_uri(_hil_payload_binding(response_sha, provenance_sha))
    return _build_transport_intent(
        operation_id="HIL-TEST-" + response_sha[:16],
        payload_hash=payload_hash,
        source_boundary="DEVICE_SYSTEM",
        source_subsystem="Site:HIL",
        destination_boundary="STEGOS_ECOSYSTEM",
        destination_subsystem="HIL:Ingress",
        prior_transport_receipt_hash=None,
    )


def _post(client: TestClient, pdf: bytes, manifest: bytes):
    manifest_obj = json.loads(manifest.decode("utf-8"))
    try:
        transport_intent = _transport_intent(pdf, manifest_obj)
    except Exception:
        transport_intent = _build_transport_intent(
            operation_id="HIL-TEST-INVALID-MANIFEST",
            payload_hash="sha256:" + "0" * 64,
            source_boundary="DEVICE_SYSTEM",
            source_subsystem="Site:HIL",
            destination_boundary="STEGOS_ECOSYSTEM",
            destination_subsystem="HIL:Ingress",
            prior_transport_receipt_hash=None,
        )
    return client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", pdf, "application/pdf"),
            "provenance_manifest": ("response.provenance.json", manifest, "application/json"),
            "intr_transport_intent": ("response.intr.json", json.dumps(transport_intent).encode("utf-8"), "application/json"),
        },
        data={
            "participant_identifier": "tester",
            "publication_consent": "anonymous",
            "primary_sha256": PRIMARY,
            "model_response_declared_unedited": "true",
            "participant_consent_authority_acknowledged": "true",
        },
    )


def test_hil_chain_receipt_and_exact_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
    client = TestClient(app)
    pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
    response = _post(client, pdf, _manifest(pdf))
    assert response.status_code == 200, response.text
    receipt = response.json()
    assert receipt["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
    assert receipt["chain_validation_state"] == "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED"
    assert receipt["authority"]["publication"] is False
    assert list((tmp_path / "originals").glob("*.pdf"))[0].read_bytes() == pdf
    assert len(list((tmp_path / "provenance").glob("*.json"))) == 1


def test_hil_chain_rejects_wrong_prompt(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
    client = TestClient(app)
    pdf = b"%PDF-1.7\n%%EOF\n"
    response = _post(client, pdf, _manifest(pdf, prompt_sha256="incorrect"))
    assert response.status_code == 400
    assert response.json()["detail"] == "provenance_prompt_sha256_mismatch"
