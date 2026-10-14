"""Standard-library HTTP client that replaced the requests dependency."""
from __future__ import annotations

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

from llm_adapter import _stdlib_http as http

ROOT = Path(__file__).resolve().parents[1]


class _Handler(BaseHTTPRequestHandler):
    def _reply(self, status, body=b"{}", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.path == "/fail":
            return self._reply(500, b'{"detail":"boom"}')
        self._reply(200, json.dumps({"echo": json.loads(raw), "ctype": self.headers["Content-Type"]}).encode())

    def do_GET(self):
        if self.path == "/redirect":
            return self._reply(302, b"", {"Location": "/elsewhere"})
        self._reply(200, b'{"ok":true}', {"X-Custom": "v"})

    def log_message(self, *_args):
        return


def _serve():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


class StdlibHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """The module-scoped server the tests share, shut down after the last one."""
        cls._server = _serve()
        cls.base = next(cls._server)

    @classmethod
    def tearDownClass(cls):
        next(cls._server, None)

    def _setenv(self, name, value):
        """monkeypatch.setenv equivalent: os.environ is restored after the test."""
        patcher = mock.patch.dict(os.environ, {name: str(value)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _delenv(self, name, raising=True):
        """monkeypatch.delenv equivalent: os.environ is restored after the test."""
        if raising and name not in os.environ:
            raise KeyError(name)
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(name, None)

    def test_post_json_round_trip(self):
        base = self.base
        response = http.post(base + "/x", json={"a": 1}, timeout=5)
        response.raise_for_status()
        assert response.json() == {"echo": {"a": 1}, "ctype": "application/json"}

    def test_error_status_is_a_response_until_raise_for_status(self):
        base = self.base
        response = http.post(base + "/fail", json={}, timeout=5)
        assert response.status_code == 500 and not response.ok
        with self.assertRaises(http.HTTPError) as caught:
            response.raise_for_status()
        assert isinstance(caught.exception, http.RequestException)
        assert caught.exception.response is response

    def test_headers_are_case_insensitive(self):
        base = self.base
        response = http.get(base + "/y", timeout=5)
        assert response.headers.get("x-custom") == "v"
        assert response.headers.get("X-CUSTOM") == "v"

    def test_session_without_redirects_returns_the_redirect(self):
        base = self.base
        session = http.Session()
        session.trust_env = False
        response = session.get(base + "/redirect", allow_redirects=False, timeout=5)
        assert response.status_code == 302
        assert response.headers.get("location") == "/elsewhere"

    def test_session_trust_env_false_ignores_proxy_environment(self):
        base = self.base
        self._setenv("http_proxy", "http://127.0.0.1:1")
        self._setenv("HTTP_PROXY", "http://127.0.0.1:1")
        self._delenv("no_proxy", raising=False)
        self._delenv("NO_PROXY", raising=False)
        session = http.Session()
        session.trust_env = False
        assert session.get(base + "/y", timeout=5).json() == {"ok": True}

    def test_transport_failure_raises_request_exception(self):
        with self.assertRaises(http.RequestException):
            http.post("http://127.0.0.1:1/unreachable", json={}, timeout=2)
        with self.assertRaises(http.RequestException):
            http.get("file:///etc/passwd")

    def test_no_module_imports_requests(self):
        for path in sorted((ROOT / "llm_adapter").rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            assert "\nimport requests" not in source, path
            assert "\nfrom requests" not in source, path


if __name__ == "__main__":
    unittest.main()
