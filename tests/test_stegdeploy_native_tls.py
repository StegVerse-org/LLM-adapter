from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from scripts import stegdeploy_bootstrap as mod


def test_tls_public_bind_rejects_loopback_and_invalid_ports() -> None:
    with pytest.raises(RuntimeError, match="must_not_be_loopback"):
        mod._validate_public_bind("127.0.0.1", 443)
    with pytest.raises(RuntimeError, match="port_invalid"):
        mod._validate_public_bind("0.0.0.0", 0)
    mod._validate_public_bind("0.0.0.0", 443)


def test_tls_private_key_must_not_live_in_repo(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    cert.write_text("-----BEGIN CERTIFICATE-----\nAA==\n-----END CERTIFICATE-----\n")
    key.write_text("private")
    key.chmod(0o600)
    with pytest.raises(RuntimeError, match="must_not_be_stored_in_repository"):
        mod._validate_tls_material(cert, key)


def test_tls_private_key_permissions_must_be_owner_only(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "runtime"
    outside.mkdir()
    monkeypatch.setattr(mod, "ROOT", repo)
    cert = outside / "cert.pem"
    key = outside / "key.pem"
    cert.write_text("-----BEGIN CERTIFICATE-----\nAA==\n-----END CERTIFICATE-----\n")
    key.write_text("private")
    key.chmod(0o644)
    with pytest.raises(RuntimeError, match="owner_only"):
        mod._validate_tls_material(cert, key)


def test_tls_material_fingerprint_and_pair_validation(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "runtime"
    outside.mkdir()
    monkeypatch.setattr(mod, "ROOT", repo)

    cert = outside / "cert.pem"
    key = outside / "key.pem"
    cert.write_text("-----BEGIN CERTIFICATE-----\nAA==\n-----END CERTIFICATE-----\n")
    key.write_text("private")
    key.chmod(0o600)

    class FakeContext:
        def __init__(self, protocol):
            assert protocol == mod.ssl.PROTOCOL_TLS_SERVER

        def load_cert_chain(self, *, certfile: str, keyfile: str) -> None:
            assert certfile == str(cert)
            assert keyfile == str(key)

    monkeypatch.setattr(mod.ssl, "SSLContext", FakeContext)
    monkeypatch.setattr(mod.ssl, "PEM_cert_to_DER_cert", lambda pem: b"certificate-der")
    fingerprint = mod._validate_tls_material(cert, key)
    assert fingerprint.startswith("sha256:")
    assert len(fingerprint) == 71


def test_tls_compose_override_uses_runtime_secrets_and_native_uvicorn() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "compose.stegdeploy.tls.yaml").read_text(encoding="utf-8")
    assert "STEGDEPLOY_TLS_CERT_FILE" in source
    assert "STEGDEPLOY_TLS_KEY_FILE" in source
    assert "/run/secrets/stegverse_tls_cert" in source
    assert "/run/secrets/stegverse_tls_key" in source
    assert "--ssl-certfile" in source
    assert "--ssl-keyfile" in source
    assert "llm_adapter.deployed_gateway:app" in source
    assert "cloudflared" not in source.lower()
    assert "caddy" not in source.lower()
    assert "nginx" not in source.lower()


def test_tls_deployment_receipt_never_records_private_key(monkeypatch, tmp_path: Path) -> None:
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    cert.write_text("cert")
    key.write_text("key")
    key.chmod(0o600)

    monkeypatch.setattr(mod, "_prepare_env_file", lambda: None)
    monkeypatch.setattr(mod, "_validate_public_bind", lambda bind, port: None)
    monkeypatch.setattr(
        mod,
        "_validate_tls_material",
        lambda cert_file, key_file: "sha256:" + "a" * 64,
    )
    monkeypatch.setattr(
        mod,
        "_health",
        lambda url, local_tls_probe=False: {"status": 200, "body": {"status": "ok"}},
    )
    monkeypatch.setattr(mod, "_source_commit", lambda: "f" * 40)
    monkeypatch.setattr(mod, "_protected_values_present", lambda: [])

    def fake_compose(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="image-id\n", stderr="")

    monkeypatch.setattr(mod, "_compose", fake_compose)

    captured: dict = {}
    monkeypatch.setattr(mod, "_write_receipt", lambda receipt: captured.update(receipt))

    mod.deploy_tls(
        cert_file=cert,
        key_file=key,
        bind_address="0.0.0.0",
        port=443,
    )

    assert captured["schema"] == "stegdeploy.deployment-receipt.v3"
    assert captured["tls_enabled"] is True
    assert captured["tls_termination"] == "UVICORN_NATIVE"
    assert captured["tls_private_key_material_recorded"] is False
    assert captured["tls_private_key_path_recorded"] is False
    assert captured["production_public_route_observed"] is False
    assert captured["public_certificate_hostname_verified"] is False
    assert captured["gateway_execution_authority"] == "NONE"
    serialized = repr(captured)
    assert str(key) not in serialized
    assert "key" not in str(captured.get("tls_certificate_sha256", ""))
