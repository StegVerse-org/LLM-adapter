from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import stegnode


class PortableNodeBootstrapTests(unittest.TestCase):
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

    def test_discovers_profile_capabilities(self) -> None:
        tmp_path = self._tmp_path()
        manifest = tmp_path / "chat.json"
        manifest.write_text(json.dumps({"capability_id": "chat"}), encoding="utf-8")
        profile = tmp_path / "node-profile.json"
        profile.write_text(
            json.dumps(
                {
                    "schema": "stegverse.portable-node-profile.v1",
                    "capabilities": [
                        {"manifest": "chat.json", "auto_start": True},
                        {"manifest": "manual.json", "auto_start": False},
                    ],
                }
            ),
            encoding="utf-8",
        )
        self._setattr(stegnode, "ROOT", tmp_path)
        self._setattr(stegnode, "PROFILE_PATH", profile)
        assert stegnode.discover() == [manifest]

    def test_fallback_discovers_only_auto_start_capabilities(self) -> None:
        tmp_path = self._tmp_path()
        capability_dir = tmp_path / "capabilities"
        capability_dir.mkdir()
        (capability_dir / "chat.json").write_text(
            json.dumps({"capability_id": "chat", "node": {"auto_start": True}}),
            encoding="utf-8",
        )
        (capability_dir / "manual.json").write_text(
            json.dumps({"capability_id": "manual", "node": {"auto_start": False}}),
            encoding="utf-8",
        )
        self._setattr(stegnode, "PROFILE_PATH", tmp_path / "missing-profile.json")
        self._setattr(stegnode, "CAPABILITY_DIR", capability_dir)
        assert stegnode.discover() == [capability_dir / "chat.json"]

    def test_node_state_declares_no_manual_selection(self) -> None:
        tmp_path = self._tmp_path()
        state_path = tmp_path / "node-state.json"
        self._setattr(stegnode, "STATE_PATH", state_path)
        stegnode.write_state({}, "RUNNING")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["manual_capability_selection_required"] is False
        assert state["state"] == "RUNNING"


if __name__ == "__main__":
    unittest.main()
