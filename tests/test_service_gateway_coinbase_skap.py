import copy
import json

import pytest

from llm_adapter.service_gateway_coinbase_skap import (
    BROWSER_SEALED_FORMAT,
    CoinbaseSkapStageError,
    CoinbaseSkapStageRuntime,
    digest,
    stage_packet,
    validate_browser_packet,
)


def browser_packet(ingress_id="coinbase-stage-test-1"):
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


def runtime(tmp_path):
    return CoinbaseSkapStageRuntime(tmp_path, "sha256:test-decision", "sha256:test-policy")


def raw(packet):
    return json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()


def redigest(packet):
    packet["ingress_digest"] = digest({k: v for k, v in packet.items() if k != "ingress_digest"})
    return packet


def test_valid_packet_stages_exact_bytes_without_authority(tmp_path):
    packet = browser_packet()
    body = raw(packet)
    receipt = stage_packet(raw_body=body, packet=packet, runtime=runtime(tmp_path))
    stored = (tmp_path / "coinbase-skap-staging" / "coinbase-stage-test-1.json").read_bytes()
    assert stored == body
    assert receipt["decision"] == "STAGED_FOR_TVC"
    assert receipt["gateway_credential_value_access"] is False
    assert receipt["gateway_decryption_authority"] is False
    assert receipt["gateway_execution_authority"] == "NONE"
    assert receipt["browser_ciphertext_mutated"] is False
    assert receipt["decryption_performed"] is False
    assert receipt["rewrap_performed"] is False
    assert receipt["tvc_admission_completed"] is False
    assert receipt["next_required_transition"] == "TVC_SKAP_CIPHERTEXT_CUSTODY_ADMISSION"
    assert receipt["blind_retry_allowed"] is False
    assert "ciphertext_b64" not in json.dumps(receipt)


def test_replay_is_denied(tmp_path):
    packet = browser_packet()
    body = raw(packet)
    stage_packet(raw_body=body, packet=packet, runtime=runtime(tmp_path))
    with pytest.raises(CoinbaseSkapStageError, match="ingress_replay_denied"):
        stage_packet(raw_body=body, packet=packet, runtime=runtime(tmp_path))


def test_plaintext_and_private_jwk_are_denied(tmp_path):
    packet = browser_packet("plaintext")
    packet["api_private_key"] = "must-not-stage"
    redigest(packet)
    assert any(x.startswith("plaintext_field_forbidden") for x in validate_browser_packet(packet))
    with pytest.raises(CoinbaseSkapStageError, match="browser_packet_denied"):
        stage_packet(raw_body=raw(packet), packet=packet, runtime=runtime(tmp_path))

    packet = browser_packet("private-jwk")
    packet["sealed_material"]["ephemeral_public_jwk"]["d"] = "private"
    redigest(packet)
    assert "ephemeral_private_jwk_forbidden" in validate_browser_packet(packet)


def test_owner_endpoint_and_authority_substitution_fail_closed():
    cases = (
        (lambda p: p["owner_authorization"].update(verified=False), "owner_verification_not_proven"),
        (lambda p: p["owner_authorization"].update(rp_id="example.com"), "owner_rp_invalid"),
        (lambda p: p.update(endpoint_origin="https://attacker.example"), "endpoint_origin_invalid"),
        (lambda p: p.update(device_secret_custody_authority=True), "device_secret_custody_forbidden"),
        (lambda p: p.update(kv_secret_resolution_authority=True), "kv_secret_resolution_forbidden"),
        (lambda p: p.update(github_environment_secret_access=True), "github_secret_access_forbidden"),
        (lambda p: p.update(credential_authority="GITHUB"), "credential_authority_invalid"),
    )
    for mutate, expected in cases:
        packet = browser_packet()
        mutate(packet)
        redigest(packet)
        with pytest.subtests.test(expected=expected) if hasattr(pytest, "subtests") else _nullcontext():
            assert expected in validate_browser_packet(packet)


def test_ciphertext_binding_substitution_fails_closed():
    for field, value, expected in (
        ("object_id", "skap://APIs/coinbase/other/1", "browser_object_binding_mismatch"),
        ("credential_version", 2, "browser_version_binding_mismatch"),
        ("purpose", "coinbase.advanced_trade", "browser_purpose_binding_mismatch"),
        ("endpoint_ref", "https://attacker.example", "browser_endpoint_binding_mismatch"),
    ):
        packet = browser_packet()
        packet["sealed_material"][field] = value
        redigest(packet)
        assert expected in validate_browser_packet(packet)


class _nullcontext:
    def __enter__(self):
        return None
    def __exit__(self, *args):
        return False
