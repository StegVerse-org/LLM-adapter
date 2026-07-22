from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app
from llm_adapter import stegwallet_siwe_api

ORIGIN = "https://stegverse.org"
WALLET = "0x1111111111111111111111111111111111111111"
SIGNATURE = "0x" + "a" * 130


class FakePolicy:
    def __init__(self, **values):
        self.values = values


class FakeStore:
    issued = None
    authenticated = None
    verified = None
    revoked = None

    def __init__(self, path):
        self.path = path

    def issue(self, *, policy, address):
        self.__class__.issued = (policy, address)
        return {
            "schema": "stegwallet.siwe_challenge.v1",
            "request_id": "siwe:test",
            "address": address,
            "normalized_address": address.lower(),
            "domain": "stegverse.org",
            "uri": ORIGIN,
            "chain_id": 8453,
            "nonce": "ABCDEFGH12345678",
            "issued_at": "2026-07-22T16:00:00Z",
            "expires_at": "2026-07-22T16:05:00Z",
            "message": "stegverse.org wants you to sign in with your Ethereum account:\n" + address,
            "message_sha256": "sha256:" + "1" * 64,
            "wallet_authenticated": False,
            "transaction_authority": False,
            "execution_authority": False,
            "custody_recorded": False,
            "challenge_sha256": "sha256:" + "2" * 64,
        }

    def authenticate(self, *, policy, challenge, signature, recover_address):
        self.__class__.authenticated = (policy, challenge, signature, recover_address)
        return {
            "schema": "stegwallet.siwe_session_receipt.v1",
            "session_id": "session:siwe:test",
            "wallet_address": WALLET,
            "domain": "stegverse.org",
            "uri": ORIGIN,
            "chain_id": 8453,
            "challenge_sha256": challenge["challenge_sha256"],
            "message_sha256": challenge["message_sha256"],
            "signature_sha256": "sha256:" + "3" * 64,
            "authenticated_at": "2026-07-22T16:00:01Z",
            "expires_at": "2026-07-22T16:30:01Z",
            "wallet_authenticated": True,
            "transaction_authority": False,
            "execution_authority": False,
            "delegation_authority": False,
            "custody_recorded": False,
            "session_sha256": "sha256:" + "4" * 64,
        }

    def verify_session(self, receipt):
        self.__class__.verified = receipt
        return {
            "status": "AUTHENTICATED",
            "session_id": receipt["session_id"],
            "wallet_address": receipt["wallet_address"],
            "session_sha256": receipt["session_sha256"],
            "transaction_authority": False,
            "execution_authority": False,
        }

    def revoke(self, session_id):
        self.__class__.revoked = session_id
        return {
            "schema": "stegwallet.siwe_revocation_receipt.v1",
            "session_id": session_id,
            "session_sha256": "sha256:" + "4" * 64,
            "revoked_at": "2026-07-22T16:01:00Z",
            "transaction_authority": False,
            "execution_authority": False,
            "custody_recorded": False,
            "revocation_sha256": "sha256:" + "5" * 64,
        }


def fake_owner():
    return SimpleNamespace(
        SiwePolicy=FakePolicy,
        SiweStore=FakeStore,
        recover_with_eth_account=lambda message, signature: WALLET,
    )


def configure(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_SIWE_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_SIWE_CANONICAL_ORIGIN", ORIGIN)
    monkeypatch.setenv("STEGVERSE_SIWE_DB", str(tmp_path / "siwe.db"))
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
    monkeypatch.setattr(stegwallet_siwe_api, "_OWNER", fake_owner())


def test_readiness_fails_closed_when_disabled(monkeypatch):
    monkeypatch.setenv("STEGVERSE_SIWE_ENABLED", "false")
    monkeypatch.setattr(stegwallet_siwe_api, "_OWNER", fake_owner())
    client = TestClient(app, base_url=ORIGIN)
    response = client.get("/api/stegwallet/siwe/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "CONFIGURATION_REQUIRED"
    assert "stegwallet_siwe_disabled" in payload["blockers"]
    assert payload["transaction_authority"] is False
    assert payload["execution_authority"] is False


def test_challenge_verify_session_and_revoke(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    client = TestClient(app, base_url=ORIGIN)
    headers = {"Origin": ORIGIN}

    readiness = client.get("/api/stegwallet/siwe/readiness").json()
    assert readiness["state"] == "READY"
    assert readiness["wallet_authentication_enabled"] is True

    challenge_response = client.post(
        "/api/stegwallet/siwe/challenge",
        headers=headers,
        json={
            "schema": "stegwallet.siwe_challenge_request.v1",
            "wallet_address": WALLET,
            "chain_id": 8453,
            "origin": ORIGIN,
            "transaction_authority": False,
            "execution_authority": False,
        },
    )
    assert challenge_response.status_code == 200, challenge_response.text
    challenge = challenge_response.json()
    assert challenge["wallet_authenticated"] is False

    verify_response = client.post(
        "/api/stegwallet/siwe/verify",
        headers=headers,
        json={
            "schema": "stegwallet.siwe_verification_request.v1",
            "challenge": challenge,
            "signature": SIGNATURE,
            "transaction_authority": False,
            "execution_authority": False,
        },
    )
    assert verify_response.status_code == 200, verify_response.text
    receipt = verify_response.json()
    assert receipt["wallet_authenticated"] is True
    assert receipt["transaction_authority"] is False
    cookie = verify_response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=strict" in cookie

    session_response = client.post(
        "/api/stegwallet/siwe/session",
        headers=headers,
        json={"schema": "stegwallet.siwe_session_verification_request.v1", "receipt": receipt},
    )
    assert session_response.status_code == 200
    assert session_response.json()["status"] == "AUTHENTICATED"

    revoke_response = client.post(
        "/api/stegwallet/siwe/revoke",
        headers=headers,
        cookies={"stegwallet_siwe_session": receipt["session_id"]},
        json={"schema": "stegwallet.siwe_revocation_request.v1", "session_id": receipt["session_id"]},
    )
    assert revoke_response.status_code == 200, revoke_response.text
    assert revoke_response.json()["execution_authority"] is False


def test_wrong_origin_and_authority_claim_fail_closed(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    client = TestClient(app, base_url=ORIGIN)
    body = {
        "schema": "stegwallet.siwe_challenge_request.v1",
        "wallet_address": WALLET,
        "chain_id": 8453,
        "origin": ORIGIN,
        "transaction_authority": False,
        "execution_authority": False,
    }
    wrong_origin = client.post(
        "/api/stegwallet/siwe/challenge",
        headers={"Origin": "https://evil.example"},
        json=body,
    )
    assert wrong_origin.status_code == 403
    authority = client.post(
        "/api/stegwallet/siwe/challenge",
        headers={"Origin": ORIGIN},
        json={**body, "transaction_authority": True},
    )
    assert authority.status_code == 400


def test_adapter_contains_no_siwe_cryptography_or_nonce_implementation():
    source = __import__("pathlib").Path(stegwallet_siwe_api.__file__).read_text()
    for prohibited in (
        "CREATE TABLE",
        "secp256k1",
        "recover_message",
        "encode_defunct",
        "Nonce:",
        "wants you to sign in with your Ethereum account",
    ):
        assert prohibited not in source
    assert "from stegwallet import SiwePolicy, SiweStore, recover_with_eth_account" in source
