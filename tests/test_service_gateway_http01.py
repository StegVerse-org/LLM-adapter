from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from llm_adapter.deployed_gateway import app
from llm_adapter.service_gateway_http01 import HTTP01ProjectionError, read_http01_challenge


class ServiceGatewayHttp01Tests(unittest.TestCase):
    @contextlib.contextmanager
    def _case(self):
        """A fresh tmp_path and cleanups for each parametrized case."""
        with contextlib.ExitStack() as stack:
            self._stack, self._tmp = stack, None
            try:
                yield
            finally:
                self._stack, self._tmp = None, None

    def _cleanup(self, function, *args, **kwargs):
        stack = getattr(self, "_stack", None)
        if stack is not None:
            stack.callback(function, *args, **kwargs)
        else:
            self.addCleanup(function, *args, **kwargs)

    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self._cleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

    def _setenv(self, name, value):
        """monkeypatch.setenv equivalent: os.environ is restored after the test."""
        patcher = mock.patch.dict(os.environ, {name: str(value)})
        patcher.start()
        self._cleanup(patcher.stop)

    def test_deployed_gateway_serves_tvc_projected_public_http01(self) -> None:
        tmp_path = self._tmp_path()
        root=tmp_path/"http01"
        root.mkdir()
        (root/"token_ABC-123").write_text("token_ABC-123.thumbprint_public\n",encoding="ascii")
        self._setenv("STEGVERSE_TVC_HTTP01_CHALLENGE_ROOT",str(root))
        response=TestClient(app).get("/.well-known/acme-challenge/token_ABC-123")
        assert response.status_code==200
        assert response.text=="token_ABC-123.thumbprint_public"
        assert response.headers["x-stegverse-credential-authority"]=="TV/TVC"
        assert response.headers["x-stegverse-authority-effect"]=="NONE"
        assert response.headers["cache-control"]=="no-store"

    def test_missing_challenge_is_404(self) -> None:
        tmp_path = self._tmp_path()
        root=tmp_path/"http01"
        root.mkdir()
        self._setenv("STEGVERSE_TVC_HTTP01_CHALLENGE_ROOT",str(root))
        response=TestClient(app).get("/.well-known/acme-challenge/missing")
        assert response.status_code==404

    def test_invalid_tokens_fail_closed(self) -> None:
        for token in ["../escape","a/b","", "token space", "."*129]:
            with self.subTest(token=token), self._case():
                tmp_path = self._tmp_path()
                with self.assertRaises(HTTP01ProjectionError):
                    read_http01_challenge(token,root=tmp_path)

    def test_symlink_and_oversize_challenges_fail_closed(self) -> None:
        tmp_path = self._tmp_path()
        outside=tmp_path/"outside"
        outside.write_text("public",encoding="ascii")
        root=tmp_path/"root"
        root.mkdir()
        link=root/"link"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(HTTP01ProjectionError,"symlink"):
            read_http01_challenge("link",root=root)
        (root/"big").write_text("x"*513,encoding="ascii")
        with self.assertRaisesRegex(HTTP01ProjectionError,"size"):
            read_http01_challenge("big",root=root)

    def test_route_registration_is_public_read_only(self) -> None:
        routes=[r for r in app.routes if getattr(r,"path","") == "/.well-known/acme-challenge/{token}"]
        assert len(routes)==1
        assert routes[0].methods=={"GET"}


if __name__ == "__main__":
    unittest.main()
