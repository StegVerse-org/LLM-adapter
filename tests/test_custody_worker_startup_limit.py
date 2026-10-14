import collections
import io
import json
import os
import sys
import types
import unittest
from unittest import mock

from llm_adapter import custody_worker


_Captured = collections.namedtuple("CaptureResult", "out err")


class CustodyWorkerStartupLimitTests(unittest.TestCase):
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

    def test_configured_limit_accepts_zero(self):
        self._setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", "0")
        assert custody_worker.configured_limit() == 0

    def test_main_uses_configured_limit_without_inventing_custody(self):
        capsys = self._capsys()
        observed = {}

        self._setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", "0")

        def fake_run(limit=20):
            observed["limit"] = limit
            return {
                "worker": "master_records_organization_record",
                "enabled": True,
                "processed": 0,
                "recorded": 0,
                "retry": 0,
                "authority_effect": "NONE_DOWNSTREAM_RECORDING_ONLY",
            }

        self._setattr(custody_worker, "run", fake_run)
        assert custody_worker.main() == 0
        assert observed["limit"] == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["recorded"] == 0

    def test_configured_limit_rejects_invalid_values(self):
        for value in ("-1", "101", "not-an-int"):
            self._setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", value)
            try:
                custody_worker.configured_limit()
            except ValueError:
                pass
            else:
                raise AssertionError(f"invalid custody worker limit accepted: {value}")

    def test_worker_failure_never_blocks_service_startup(self):
        capsys = self._capsys()
        self._setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", "not-an-int")
        assert custody_worker.main() == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["gates_startup"] is False
        for field in ("failure_code", "failed_predicate", "required_evidence_or_repair",
                      "retry_entrypoint", "owning_existing_goal", "next_attempt"):
            assert payload[field]

        self._setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", "1")

        def unreachable(limit=20):
            raise ConnectionError("master records unreachable")

        self._setattr(custody_worker, "run", unreachable)
        assert custody_worker.main() == 0
        assert json.loads(capsys.readouterr().out)["disposition"] == "NOT_RECORDED"


if __name__ == "__main__":
    unittest.main()
