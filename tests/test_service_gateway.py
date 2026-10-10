import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from llm_adapter import service_gateway
from llm_adapter.service_gateway import app

HIL_ROUTE = "stegverse.route.hil-intake.v1"


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


def _plant_env_credentials(monkeypatch, tmp_path):
    """What used to configure the gateway. It must now be ignored."""
    monkeypatch.setenv("STEGVERSE_TVC_DECISION_RECEIPT", json.dumps(_tvc_receipt()))
    monkeypatch.setenv("STEGVERSE_HIL_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_HIL_RECEIPT_KEY", "x" * 64)


def _bind_tvc_source(monkeypatch, tmp_path):
    """A TV/TVC-sourced credential binding, which this repository does not have."""
    monkeypatch.setattr(service_gateway, "_tvc_credentials", lambda: {
        "tvc": _tvc_receipt(), "key": b"x" * 64, "storage_root": str(tmp_path)})


def _no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("the HIL gateway must not open a network connection")
    monkeypatch.setattr("urllib.request.urlopen", refuse)


PDF = b"%PDF-1.7\nfixture\n%%EOF\n"


def _intake(client, pdf=PDF):
    metadata = {
        "packet_id": "research-packet-001",
        "document_hash": "sha256:" + hashlib.sha256(pdf).hexdigest(),
        "protocol": "HIL-RESPONSE-PACKET-v1",
    }
    return client.post("/v1/hil/intake", files={"document": ("experiment.pdf", pdf, "application/pdf")},
                       data={"metadata": json.dumps(metadata)})


def _site_submission(client, pdf=b"%PDF-1.7\nsite fixture\n%%EOF\n"):
    manifest = {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1.1",
        "primary_version": "v1.1",
        "primary_sha256": "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462",
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c",
        "response_sha256": hashlib.sha256(pdf).hexdigest(),
    }
    return client.post(
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
    ), manifest


def test_readiness_fails_closed_without_tvc_credential_source(monkeypatch, tmp_path):
    _plant_env_credentials(monkeypatch, tmp_path)
    client = TestClient(app)
    for path in ("/ready", "/api/hil/readiness"):
        response = client.get(path)
        assert response.status_code == 503
        assert response.json()["detail"] == "TVC_CREDENTIAL_SOURCE_NOT_BOUND"


@pytest.mark.parametrize("submit", ["intake", "site"])
def test_without_canonical_boundary_the_sdk_disposition_is_returned_and_nothing_persists(monkeypatch, tmp_path, submit):
    _plant_env_credentials(monkeypatch, tmp_path)
    _no_network(monkeypatch)
    client = TestClient(app)
    response = _intake(client) if submit == "intake" else _site_submission(client)[0]
    assert response.status_code == 503
    body = response.json()
    assert body["disposition"] == "FAIL_CLOSED"
    assert body["failure_code"] == "CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED"
    assert body["route_id"] == HIL_ROUTE
    assert body["handed_off"] is True
    assert body["canonical_entrypoint"] == "stegverse.manifest_execution.execute_manifest"
    assert body["credential_read_from_environment"] is False
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("submit", ["intake", "site"])
def test_admitted_manifest_still_fails_closed_without_tvc_credential_source(
        monkeypatch, tmp_path, organization_admits_manifests, submit):
    _plant_env_credentials(monkeypatch, tmp_path)
    _no_network(monkeypatch)
    client = TestClient(app)
    response = _intake(client) if submit == "intake" else _site_submission(client)[0]
    assert response.status_code == 503
    body = response.json()
    assert body["disposition"] == "FAIL_CLOSED"
    assert body["failure_code"] == "TVC_CREDENTIAL_SOURCE_NOT_BOUND"
    assert body["sdk_disposition"] == "ALLOW"
    assert "x" * 64 not in response.text
    assert list(tmp_path.iterdir()) == []
    [manifest] = organization_admits_manifests
    assert manifest["processing"]["route_id"] == HIL_ROUTE


def test_pdf_intake_is_durable_and_idempotent_once_admitted_and_tvc_bound(
        monkeypatch, tmp_path, organization_admits_manifests):
    _bind_tvc_source(monkeypatch, tmp_path)
    client = TestClient(app)
    first = _intake(client)
    assert first.status_code == 200
    receipt = first.json()
    assert receipt["status"] == "SUBMISSION_ACCEPTED"
    assert receipt["document_hash"] == "sha256:" + hashlib.sha256(PDF).hexdigest()
    assert receipt["signature"].startswith("hmac-sha256:")
    assert (tmp_path / "packets" / "research-packet-001" / "document.pdf").read_bytes() == PDF
    assert (tmp_path / "receipts" / "research-packet-001.json").exists()

    duplicate = _intake(client)
    assert duplicate.status_code == 200
    assert duplicate.json() == receipt
    assert len(organization_admits_manifests) == 2


def test_site_submission_contract_once_admitted_and_tvc_bound(monkeypatch, tmp_path, organization_admits_manifests):
    _bind_tvc_source(monkeypatch, tmp_path)
    response, manifest = _site_submission(TestClient(app))
    assert response.status_code == 200
    receipt = response.json()
    assert receipt["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
    assert receipt["submitted_file_sha256"] == manifest["response_sha256"]
    assert receipt["chain_validation_state"] == "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED"
    assert receipt["receiver_signature"].startswith("hmac-sha256:")
    material = dict(receipt)
    receipt_hash = material.pop("receipt_sha256")
    assert receipt_hash == hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_intake_scope_cannot_use_provider_keys():
    receipt = _tvc_receipt()
    receipt["allowed_keys"].append("service-gateway/provider/token")
    receipt["denied_keys"] = ["service-gateway/provider/token"]
    with pytest.raises(RuntimeError, match="tvc_intake_scope_invalid"):
        service_gateway._validate_tvc_receipt(receipt)
