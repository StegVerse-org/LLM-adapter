from __future__ import annotations

from pathlib import Path

import pytest

from scripts import stegdeploy_native_gateway as mod


def test_tls_private_key_must_not_live_in_repo(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    cert.write_text("-----BEGIN CERTIFICATE-----\nAA==\n-----END CERTIFICATE-----\n")
    key.write_text("private")
    key.chmod(0o600)
    with pytest.raises(RuntimeError, match="must_not_be_stored_in_repository"):
        mod.validate_tls(cert, key)


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
        mod.validate_tls(cert, key)


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
    fingerprint = mod.validate_tls(cert, key)
    assert fingerprint.startswith("sha256:")
    assert len(fingerprint) == 71
