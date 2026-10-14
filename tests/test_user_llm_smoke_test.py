from __future__ import annotations

import collections
import io
import json
import os
import sys
import types
import unittest
from unittest import mock

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


_Captured = collections.namedtuple("CaptureResult", "out err")


class UserLlmSmokeTestTests(unittest.TestCase):
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

    def _capsys(self):
        """capsys equivalent: sys.stdout and sys.stderr are captured for the rest of the test."""
        streams = {"stdout": io.StringIO(), "stderr": io.StringIO()}
        for name, stream in streams.items():
            patcher = mock.patch.object(sys, name, stream)
            patcher.start()
            self.addCleanup(patcher.stop)

        def readouterr():
            captured = _Captured(streams["stdout"].getvalue(), streams["stderr"].getvalue())
            for stream in streams.values():
                stream.seek(0)
                stream.truncate()
            return captured

        return types.SimpleNamespace(readouterr=readouterr)

    def test_smoke_test_succeeds_for_ready_activated_endpoint(self):
        capsys = self._capsys()
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

        self._setenv("STEGVERSE_USER_LLM_BASE_URL", "https://adapter.example")
        self._setattr(user_llm_smoke_test, "urlopen", fake_urlopen)

        assert user_llm_smoke_test.main() == 0
        output = json.loads(capsys.readouterr().out)
        assert output["health"] == "OK"
        assert output["readiness"] == "READY"
        assert output["activation"] == "ACTIVATED"
        assert output["authority_attached"] is False

    def test_smoke_test_fails_closed_when_not_ready(self):
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

        self._setenv("STEGVERSE_USER_LLM_BASE_URL", "https://adapter.example")
        self._setattr(user_llm_smoke_test, "urlopen", fake_urlopen)

        assert user_llm_smoke_test.main() == 1


if __name__ == "__main__":
    unittest.main()
