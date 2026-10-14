from __future__ import annotations

import collections
import io
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from llm_adapter import node_service


_Captured = collections.namedtuple("CaptureResult", "out err")


class NodeServiceTests(unittest.TestCase):
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

    def test_node_service_is_invocation_scoped_with_no_resident_surface(self) -> None:
        for retired in ("start", "daemon", "_daemon_owned", "_claim_daemon", "_release_daemon",
                        "_lock_path", "_restart_delay", "_wait_for_health", "_health_url"):
            assert not hasattr(node_service, retired), retired
        assert not hasattr(node_service, "subprocess")

    def test_cli_offers_only_invocation_scoped_commands(self) -> None:
        tmp_path = self._tmp_path()
        capsys = self._capsys()
        self._setattr("sys.argv", ["stegnode", "daemon", "--root", str(tmp_path)])
        with self.assertRaises(SystemExit):
            node_service.main()
        capsys.readouterr()
        self._setattr("sys.argv", ["stegnode", "--root", str(tmp_path)])
        assert node_service.main() == 0
        assert json.loads(capsys.readouterr().out)["state"] == "STOPPED"

    def test_status_reports_leftover_resident_state_as_stale(self) -> None:
        tmp_path = self._tmp_path()
        capsys = self._capsys()
        node_service._write_state(tmp_path, {"state": "RUNNING", "pid": 55})
        self._setattr(node_service, "_pid_alive", lambda _pid: False)
        self._setattr("sys.argv", ["stegnode", "status", "--root", str(tmp_path)])
        assert node_service.main() == 0
        result = json.loads(capsys.readouterr().out)
        assert result["state"] == "STALE"
        assert result["running"] is False

    def test_stop_writes_dissolved_state_and_receipt(self) -> None:
        tmp_path = self._tmp_path()
        node_service._write_state(tmp_path, {"state": "RUNNING", "pid": 88})
        self._setattr(node_service, "_pid_alive", lambda _pid: False)

        state = node_service.stop(tmp_path)
        stored = json.loads((tmp_path / "state" / "node-service.json").read_text(encoding="utf-8"))
        receipt = json.loads((tmp_path / "receipts" / "node-runtime" / "service-stop.latest.json").read_text(encoding="utf-8"))

        assert state["state"] == "DISSOLVED"
        assert stored["manual_action_required"] is False
        assert receipt["event"] == "service-stop"

    def test_unstarted_status_requires_no_manual_selection(self) -> None:
        tmp_path = self._tmp_path()
        state = node_service._read_state(tmp_path)
        assert state == {
            "state": "STOPPED",
            "node_root": str(tmp_path),
            "manual_action_required": False,
        }

    def test_atomic_state_write_leaves_no_temporary_file(self) -> None:
        tmp_path = self._tmp_path()
        node_service._write_state(tmp_path, {"state": "RUNNING", "pid": 7})
        assert json.loads((tmp_path / "state" / "node-service.json").read_text(encoding="utf-8"))["pid"] == 7
        assert list((tmp_path / "state").glob("*.tmp")) == []
        assert list((tmp_path / "state").glob(".*.tmp")) == []


if __name__ == "__main__":
    unittest.main()
