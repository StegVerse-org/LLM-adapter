from __future__ import annotations

import json
from types import SimpleNamespace

from scripts import user_llm_smoke_test


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def test_smoke_test_succeeds_for_ready_activated_endpoint(monkeypatch, capsys):
    payloads = {
        "/healthz": {"status": "OK"},
        "/readyz": {"state": "READY"},
        "/v1/user-llm/activation-proof": {
            "state": "ACTIVATED",
            "proof_hash": "abc123",
            "authority_attached": False,
        },
    }

    def fake_urlopen(request, timeout):
        assert timeout == 10
        path = request.full_url.removeprefix("https://adapter.example")
        return _Response(payloads[path])

    monkeypatch.setenv("STEGVERSE_USER_LLM_BASE_URL", "https://adapter.example")
    monkeypatch.setattr(user_llm_smoke_test, "urlopen", fake_urlopen)

    assert user_llm_smoke_test.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["health"] == "OK"
    assert output["readiness"] == "READY"
    assert output["activation"] == "ACTIVATED"
    assert output["authority_attached"] is False


def test_smoke_test_fails_closed_when_not_ready(monkeypatch):
    payloads = {
        "/healthz": {"status": "OK"},
        "/readyz": {"state": "DEFERRED"},
        "/v1/user-llm/activation-proof": {
            "state": "DEFERRED",
            "proof_hash": "abc123",
            "authority_attached": False,
        },
    }

    def fake_urlopen(request, timeout):
        path = request.full_url.removeprefix("https://adapter.example")
        return _Response(payloads[path])

    monkeypatch.setenv("STEGVERSE_USER_LLM_BASE_URL", "https://adapter.example")
    monkeypatch.setattr(user_llm_smoke_test, "urlopen", fake_urlopen)

    assert user_llm_smoke_test.main() == 1
