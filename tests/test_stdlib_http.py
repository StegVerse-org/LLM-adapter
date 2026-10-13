"""Standard-library HTTP client that replaced the requests dependency."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

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


@pytest.fixture(scope="module")
def base():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_post_json_round_trip(base):
    response = http.post(base + "/x", json={"a": 1}, timeout=5)
    response.raise_for_status()
    assert response.json() == {"echo": {"a": 1}, "ctype": "application/json"}


def test_error_status_is_a_response_until_raise_for_status(base):
    response = http.post(base + "/fail", json={}, timeout=5)
    assert response.status_code == 500 and not response.ok
    with pytest.raises(http.HTTPError) as caught:
        response.raise_for_status()
    assert isinstance(caught.value, http.RequestException)
    assert caught.value.response is response


def test_headers_are_case_insensitive(base):
    response = http.get(base + "/y", timeout=5)
    assert response.headers.get("x-custom") == "v"
    assert response.headers.get("X-CUSTOM") == "v"


def test_session_without_redirects_returns_the_redirect(base):
    session = http.Session()
    session.trust_env = False
    response = session.get(base + "/redirect", allow_redirects=False, timeout=5)
    assert response.status_code == 302
    assert response.headers.get("location") == "/elsewhere"


def test_session_trust_env_false_ignores_proxy_environment(base, monkeypatch):
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:1")
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.delenv("no_proxy", raising=False)
    monkeypatch.delenv("NO_PROXY", raising=False)
    session = http.Session()
    session.trust_env = False
    assert session.get(base + "/y", timeout=5).json() == {"ok": True}


def test_transport_failure_raises_request_exception():
    with pytest.raises(http.RequestException):
        http.post("http://127.0.0.1:1/unreachable", json={}, timeout=2)
    with pytest.raises(http.RequestException):
        http.get("file:///etc/passwd")


def test_no_module_imports_requests():
    for path in sorted((ROOT / "llm_adapter").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "\nimport requests" not in source, path
        assert "\nfrom requests" not in source, path
