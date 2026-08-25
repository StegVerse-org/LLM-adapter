import json

from fastapi.testclient import TestClient

from llm_adapter.runtime_gateway import app
from llm_adapter.service_gateway_coinbase_skap import BROWSER_SEALED_FORMAT, digest


def _tvc_receipt():
    return {
        "role": "service_gateway_coinbase_skap_ciphertext_intake",
        "admissible": True,
        "binding_matched": True,
        "allowed_keys": [],
        "denied_keys": [],
        "credential_values_available": False,
        "decision_id": "sha256:coinbase-stage-decision",
        "policy_hash": "sha256:coinbase-stage-policy",
    }


def _configure(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT", json.dumps(_tvc_receipt()))
    monkeypatch.setenv("STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT", str(tmp_path))


def _packet(ingress_id="coinbase-http-stage-1"):
    sealed = {
        "format": BROWSER_SEALED_FORMAT,
        "object_id": "skap://APIs/coinbase/owner/1",
        "credential_version": 1,
        "wrapping_policy_ref": "policy://skap/coinbase/browser-ingress",
        "purpose": "coinbase.permission_observation",
        "endpoint_ref": "https://api.coinbase.com",
        "recipient_key_id": "tvc://skap/browser-ingress/coinbase/v1",
        "ephemeral_public_jwk": {"kty": "EC", "crv": "P-256", "x": "x" * 43, "y": "y" * 43},
        "kdf_salt_b64": "s" * 43,
        "nonce_b64": "n" * 16,
        "aad_hash": "sha256:" + "a" * 64,
        "ciphertext_b64": "c" * 64,
        "plaintext_persisted": False,
        "device_private_key_persisted": False,
        "skap_private_key_exported": False,
        "authority_transfer": False,
    }
    body = {
        "schema": "stegverse.tvc.coinbase_iphone_skap_ingress/v1",
        "ingress_id": ingress_id,
        "owner_authorization": {
            "method": "WEBAUTHN",
            "rp_id": "stegverse.org",
            "assertion_digest": "sha256:" + "b" * 64,
            "device_admission_digest": "sha256:" + "d" * 64,
            "identity_continuity_digest": "sha256:" + "e" * 64,
            "user_verification": "REQUIRED",
            "verified": True,
        },
        "physical_execution_surface": "CURRENT_USER_IPHONE",
        "transport": "STEGVERSE_BROWSER_CAPSULE",
        "provider": "coinbase_advanced",
        "endpoint_origin": "https://api.coinbase.com",
        "purpose": "coinbase.permission_observation",
        "credential_ref": "skap://APIs/coinbase/owner/1",
        "credential_version": 1,
        "sealed_material": sealed,
        "plaintext_present": False,
        "device_secret_custody_authority": False,
        "kv_secret_resolution_authority": False,
        "github_environment_secret_access": False,
        "credential_authority": "TV/TVC",
    }
    return {**body, "ingress_digest": digest(body)}


def test_readiness_proves_no_value_no_authority_scope(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    response = TestClient(app).get("/api/coinbase/skap/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "READY"
    assert body["adapter"] == "coinbase-skap-ciphertext-staging"
    assert body["gateway_credential_value_access"] is False
    assert body["gateway_decryption_authority"] is False
    assert body["gateway_execution_authority"] == "NONE"
    assert body["tvc_admission_completed"] is False


def test_http_stage_persists_exact_body_and_returns_non_authorizing_receipt(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    packet = _packet()
    raw = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
    response = TestClient(app).post(
        "/api/coinbase/skap/ingress",
        content=raw,
        headers={"Origin": "https://stegverse.org", "Content-Type": "application/json"},
    )
    assert response.status_code == 202
    receipt = response.json()
    assert receipt["decision"] == "STAGED_FOR_TVC"
    assert receipt["gateway_execution_authority"] == "NONE"
    assert receipt["tvc_admission_completed"] is False
    assert receipt["browser_ciphertext_mutated"] is False
    assert (tmp_path / "coinbase-skap-staging" / "coinbase-http-stage-1.json").read_bytes() == raw
    assert "ciphertext_b64" not in json.dumps(receipt)


def test_origin_auth_cookie_plaintext_and_replay_fail_closed(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    client = TestClient(app)
    packet = _packet("deny-cases")
    raw = json.dumps(packet).encode()

    response = client.post("/api/coinbase/skap/ingress", content=raw, headers={"Origin": "https://example.com", "Content-Type": "application/json"})
    assert response.status_code == 403

    response = client.post("/api/coinbase/skap/ingress", content=raw, headers={"Origin": "https://stegverse.org", "Content-Type": "application/json", "Authorization": "forbidden"})
    assert response.status_code == 400

    response = client.post("/api/coinbase/skap/ingress", content=raw, headers={"Origin": "https://stegverse.org", "Content-Type": "application/json", "Cookie": "forbidden=1"})
    assert response.status_code == 400

    bad = _packet("plaintext-denied")
    bad["api_private_key"] = "must-never-stage"
    bad["ingress_digest"] = digest({k: v for k, v in bad.items() if k != "ingress_digest"})
    response = client.post("/api/coinbase/skap/ingress", content=json.dumps(bad).encode(), headers={"Origin": "https://stegverse.org", "Content-Type": "application/json"})
    assert response.status_code == 422
    assert "plaintext_field_forbidden" in response.text

    replay_packet = _packet("replay-denied")
    replay_raw = json.dumps(replay_packet).encode()
    headers = {"Origin": "https://stegverse.org", "Content-Type": "application/json"}
    assert client.post("/api/coinbase/skap/ingress", content=replay_raw, headers=headers).status_code == 202
    assert client.post("/api/coinbase/skap/ingress", content=replay_raw, headers=headers).status_code == 409


def test_no_value_tvc_scope_is_mandatory(monkeypatch, tmp_path):
    receipt = _tvc_receipt()
    receipt["allowed_keys"] = ["coinbase/private-key"]
    monkeypatch.setenv("STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT", json.dumps(receipt))
    monkeypatch.setenv("STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT", str(tmp_path))
    response = TestClient(app).get("/api/coinbase/skap/readiness")
    assert response.status_code == 503
    assert "no_value_scope_invalid" in response.text
