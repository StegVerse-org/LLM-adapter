from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import stegdeploy_native_gateway as mod


class StegdeployNativeTlsTests(unittest.TestCase):
    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_tls_private_key_must_not_live_in_repo(self) -> None:
        tmp_path = self._tmp_path()
        self._setattr(mod, "ROOT", tmp_path)
        cert = tmp_path / "cert.pem"
        key = tmp_path / "key.pem"
        cert.write_text("-----BEGIN CERTIFICATE-----\nAA==\n-----END CERTIFICATE-----\n")
        key.write_text("private")
        key.chmod(0o600)
        with self.assertRaisesRegex(RuntimeError, "must_not_be_stored_in_repository"):
            mod.validate_tls(cert, key)

    def test_tls_private_key_permissions_must_be_owner_only(self) -> None:
        tmp_path = self._tmp_path()
        repo = tmp_path / "repo"
        repo.mkdir()
        outside = tmp_path / "runtime"
        outside.mkdir()
        self._setattr(mod, "ROOT", repo)
        cert = outside / "cert.pem"
        key = outside / "key.pem"
        cert.write_text("-----BEGIN CERTIFICATE-----\nAA==\n-----END CERTIFICATE-----\n")
        key.write_text("private")
        key.chmod(0o644)
        with self.assertRaisesRegex(RuntimeError, "owner_only"):
            mod.validate_tls(cert, key)

    def test_tls_material_fingerprint_and_pair_validation(self) -> None:
        tmp_path = self._tmp_path()
        repo = tmp_path / "repo"
        repo.mkdir()
        outside = tmp_path / "runtime"
        outside.mkdir()
        self._setattr(mod, "ROOT", repo)

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

        self._setattr(mod.ssl, "SSLContext", FakeContext)
        self._setattr(mod.ssl, "PEM_cert_to_DER_cert", lambda pem: b"certificate-der")
        fingerprint = mod.validate_tls(cert, key)
        assert fingerprint.startswith("sha256:")
        assert len(fingerprint) == 71


if __name__ == "__main__":
    unittest.main()
