from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from llm_adapter import service_gateway_kv_onboarding as kv_gateway
from llm_adapter.runtime_gateway import app


def sha256_uri(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def request_packet(operation: str = "CREATE_KV") -> dict:
    packet = {
        "schema": kv_gateway.REQUEST_SCHEMA,
        "request_id": "kv-onboarding-test-001",
        "operation": operation,
        "transport_protocol": "InTr",
        "account_ref_sha256": sha256_uri("account:test"),
        "identity_assertion_id": "assertion:test:001",
        "identity_assertion_hash": sha256_uri("assertion:test:001"),
        "kv_ref": None,
        "device_ref": None,
        "prior_transition_receipt_hash": None,
        "secret_plaintext_present": False,
        "credential_material_recorded": False,
        "authority_effect": "REQUEST_ONLY",
    }
    if operation == "ATTACH_KV":
        packet["kv_ref"] = "kv://existing/test-001"
    elif operation == "REGISTER_DEVICE":
        packet["kv_ref"] = "kv://existing/test-001"
        packet["device_ref"] = "device://test/iphone-001"
    elif operation == "INSTALL_KV":
        packet["kv_ref"] = "kv://existing/test-001"
        packet["device_ref"] = "device://test/iphone-001"
        packet["prior_transition_receipt_hash"] = sha256_uri("prior-owner-bound-receipt")
    return packet


def client(monkeypatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("STEGVERSE_KV_ONBOARDING_STORAGE_ROOT", str(tmp_path))
    return TestClient(app)


def headers() -> dict[str, str]:
    return {"Origin": "https://stegverse.org", "Content-Type": "application/json"}


def test_readiness_is_transport_only(monkeypatch, tmp_path):
    response = client(monkeypatch, tmp_path).get("/api/kv/onboarding/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "READY_FOR_STAGING"
    assert payload["transport_protocol"] == "InTr"
    assert payload["decision"] == "STAGED_FOR_CANONICAL_KV_AUTHORITY"
    assert payload["gateway_identity_authority"] is False
    assert payload["gateway_kv_authority"] is False
    assert payload["gateway_device_authority"] is False
    assert payload["gateway_execution_authority"] == "NONE"
    assert payload["canonical_ownership_admission_required"] is True


def test_create_request_stages_without_minting_ownership(monkeypatch, tmp_path):
    packet = request_packet("CREATE_KV")
    response = client(monkeypatch, tmp_path).post(
        "/api/kv/onboarding/transitions",
        headers=headers(),
        json=packet,
    )
    assert response.status_code == 202
    receipt = response.json()
    assert receipt["schema"] == kv_gateway.STAGE_RECEIPT_SCHEMA
    assert receipt["decision"] == "STAGED_FOR_CANONICAL_KV_AUTHORITY"
    assert receipt["completed_boundary"] == "DEVICE_TO_KV_STAGING"
    assert receipt["kv_ownership_established"] is False
    assert receipt["owner_binding_established"] is False
    assert receipt["device_registration_established"] is False
    assert receipt["installation_admitted"] is False
    assert receipt["kv_active"] is False
    assert receipt["skap_unlocked"] is False
    assert receipt["gateway_identity_authority"] is False
    assert receipt["gateway_kv_authority"] is False
    assert receipt["gateway_device_authority"] is False
    assert receipt["gateway_execution_authority"] == "NONE"
    assert receipt["authority_transfer"] is False
    assert receipt["secret_plaintext_present"] is False
    assert receipt["credential_material_recorded"] is False
    assert receipt["next_required_transition"] == "CANONICAL_KV_OWNERSHIP_ADMISSION"
    assert receipt["blind_retry_allowed"] is False
    assert receipt["staged_request_ref"] == "kv-onboarding-stage://kv-onboarding-test-001"

    stage = tmp_path / "kv-onboarding-staging" / "kv-onboarding-test-001.json"
    persisted = json.loads(stage.read_text(encoding="utf-8"))
    assert persisted == packet
    assert "KV_CREATED" not in json.dumps(receipt)
    assert "OWNER_BOUND" not in json.dumps(receipt)
    assert "KV_ACTIVE" not in json.dumps(receipt)


def test_replay_is_durably_denied(monkeypatch, tmp_path):
    packet = request_packet("CREATE_KV")
    first = client(monkeypatch, tmp_path).post(
        "/api/kv/onboarding/transitions", headers=headers(), json=packet
    )
    assert first.status_code == 202

    # A new client/process view over the same durable root must still fail closed.
    second = TestClient(app).post(
        "/api/kv/onboarding/transitions", headers=headers(), json=packet
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "kv_onboarding_replay_denied"


def test_operation_specific_ordering_is_enforced(monkeypatch, tmp_path):
    c = client(monkeypatch, tmp_path)

    install = request_packet("INSTALL_KV")
    install["prior_transition_receipt_hash"] = None
    response = c.post("/api/kv/onboarding/transitions", headers=headers(), json=install)
    assert response.status_code == 422
    assert "install_prior_receipt_required" in response.json()["detail"]

    create = request_packet("CREATE_KV")
    create["kv_ref"] = "kv://browser-minted/forbidden"
    create["request_id"] = "create-with-kv-ref"
    response = c.post("/api/kv/onboarding/transitions", headers=headers(), json=create)
    assert response.status_code == 422
    assert "create_kv_ref_must_be_unassigned" in response.json()["detail"]

    attach = request_packet("ATTACH_KV")
    attach["kv_ref"] = None
    attach["request_id"] = "attach-without-ref"
    response = c.post("/api/kv/onboarding/transitions", headers=headers(), json=attach)
    assert response.status_code == 422
    assert "attach_kv_ref_invalid" in response.json()["detail"]


def test_secret_and_authority_escalation_fields_fail_closed(monkeypatch, tmp_path):
    c = client(monkeypatch, tmp_path)

    packet = request_packet("CREATE_KV")
    packet["request_id"] = "secret-test"
    packet["password"] = "never-store-this"
    response = c.post("/api/kv/onboarding/transitions", headers=headers(), json=packet)
    assert response.status_code == 422
    assert "forbidden_field" in response.json()["detail"]

    packet = request_packet("CREATE_KV")
    packet["request_id"] = "authority-test"
    packet["authority_effect"] = "OWNER_BOUND"
    response = c.post("/api/kv/onboarding/transitions", headers=headers(), json=packet)
    assert response.status_code == 422
    assert "authority_effect_invalid" in response.json()["detail"]


def test_origin_authorization_cookie_and_content_type_boundaries(monkeypatch, tmp_path):
    c = client(monkeypatch, tmp_path)
    packet = request_packet("CREATE_KV")

    response = c.post(
        "/api/kv/onboarding/transitions",
        headers={"Origin": "https://evil.example", "Content-Type": "application/json"},
        json=packet,
    )
    assert response.status_code == 403

    response = c.post(
        "/api/kv/onboarding/transitions",
        headers={**headers(), "Authorization": "Bearer forbidden"},
        json=packet,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "authorization_header_forbidden"

    response = c.post(
        "/api/kv/onboarding/transitions",
        headers={**headers(), "Cookie": "session=forbidden"},
        json=packet,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "cookie_header_forbidden"

    response = c.post(
        "/api/kv/onboarding/transitions",
        headers={"Origin": "https://stegverse.org", "Content-Type": "text/plain"},
        content=json.dumps(packet),
    )
    assert response.status_code == 415
