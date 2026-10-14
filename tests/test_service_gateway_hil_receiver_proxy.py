from __future__ import annotations

import importlib
import os
import shutil
import tempfile
import types
import unittest
from unittest import mock

from llm_adapter.web import FastAPI
from llm_adapter.web import JSONResponse
from llm_adapter.web.testclient import TestClient

mod = importlib.import_module("llm_adapter.service_gateway_hil_receiver_proxy")


def client(monkeypatch, *, enabled=True, upstream="http://127.0.0.1:8877"):
    monkeypatch.setenv(mod.ENABLED_ENV, "true" if enabled else "false")
    monkeypatch.setenv(mod.UPSTREAM_ENV, upstream)
    app = FastAPI()
    app.add_middleware(mod.HILMachineReceiverProxyMiddleware)

    @app.get("/api/hil/readiness")
    def local_readiness():
        return {"source": "local-copy"}

    return TestClient(app, base_url="https://stegverse.org")


_REDIRECT = []


def setUpModule():
    """As tests/conftest.py does under pytest: keep runs out of the deployed ledger and forward queue."""
    root = tempfile.mkdtemp(prefix="llm-adapter-test-ledger-")
    patcher = mock.patch.dict(os.environ, {
        "STEGVERSE_REPO_LEDGER_ROOT": root,
        "STEGVERSE_GATEWAY_FORWARD_DB": os.path.join(root, "gateway-forward.db"),
    })
    patcher.start()
    _REDIRECT[:] = [patcher, root]


def tearDownModule():
    patcher, root = _REDIRECT
    patcher.stop()
    shutil.rmtree(root, ignore_errors=True)


class ServiceGatewayHilReceiverProxyTests(unittest.TestCase):
    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _setenv(self, name, value):
        """monkeypatch.setenv equivalent: os.environ is restored after the test."""
        patcher = mock.patch.dict(os.environ, {name: str(value)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _monkeypatch(self):
        """The monkeypatch methods the module helpers call, each undone after the test."""
        return types.SimpleNamespace(setattr=self._setattr, setenv=self._setenv)

    def test_receiver_projection_uses_distinct_loopback_origin(self):
        self._setenv(mod.UPSTREAM_ENV, "http://127.0.0.1:8877")
        assert mod.upstream_base() == "http://127.0.0.1:8877"
        assert mod.target_url("/api/hil/submissions") == "http://127.0.0.1:8877/api/hil/submissions"

    def test_receiver_projection_rejects_intr_path_or_remote_origin(self):
        self._setenv(mod.UPSTREAM_ENV, "http://127.0.0.1:8877/intr/materialization")
        try:
            mod.upstream_base()
        except ValueError as exc:
            assert "origin without path" in str(exc)
        else:
            raise AssertionError("path-bearing HIL receiver upstream accepted")
        self._setenv(mod.UPSTREAM_ENV, "https://example.com")
        try:
            mod.upstream_base()
        except ValueError as exc:
            assert "loopback http" in str(exc)
        else:
            raise AssertionError("remote HIL receiver upstream accepted")

    def test_proxy_precedes_local_hil_copy_and_preserves_exact_multipart_bytes(self):
        monkeypatch = self._monkeypatch()
        observed = {}
        def fake_forward(method, target, body, headers):
            observed.update(method=method,target=target,body=body,headers=headers)
            return 201, b'{"schema_version":"HIL-RECEIVER-RECEIPT-v2","custody_state":"EXACT_BYTES_PERSISTED"}', "application/json", {}
        self._setattr(mod, "_forward", fake_forward)
        c = client(monkeypatch)
        body = b"--X\r\nContent-Disposition: form-data; name=\"response_pdf\"\r\n\r\n%PDF-exact\r\n--X--\r\n"
        response = c.post("/api/hil/submissions", content=body, headers={"Content-Type":"multipart/form-data; boundary=X","Origin":"https://stegverse.org"})
        assert response.status_code == 201
        assert response.json()["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
        assert observed["target"] == "http://127.0.0.1:8877/api/hil/submissions"
        assert observed["body"] == body
        assert observed["headers"]["content-type"] == "multipart/form-data; boundary=X"

    def test_proxy_preserves_reconstruction_header(self):
        monkeypatch = self._monkeypatch()
        def fake_forward(method, target, body, headers):
            return 200, b"%PDF-exact", "application/pdf", {"x-stegverse-hil-reconstruction-state":"EXACT_BYTES_HASH_VERIFIED"}
        self._setattr(mod, "_forward", fake_forward)
        c = client(monkeypatch)
        response = c.get("/api/hil/submissions/S1/exact-bytes", headers={"X-SteGVerse-HIL-Review-Token":"opaque"})
        assert response.status_code == 200
        assert response.content == b"%PDF-exact"
        assert response.headers["x-stegverse-hil-reconstruction-state"] == "EXACT_BYTES_HASH_VERIFIED"

    def test_disabled_projection_falls_through_to_local_route(self):
        monkeypatch = self._monkeypatch()
        c = client(monkeypatch, enabled=False)
        response = c.get("/api/hil/readiness")
        assert response.status_code == 200
        assert response.json() == {"source":"local-copy"}

    def test_browser_authorization_and_cookie_headers_fail_closed(self):
        monkeypatch = self._monkeypatch()
        c = client(monkeypatch)
        assert c.get("/api/hil/readiness", headers={"Authorization":"Bearer forbidden"}).status_code == 400
        assert c.get("/api/hil/readiness", headers={"Cookie":"x=y"}).status_code == 400


if __name__ == "__main__":
    unittest.main()
