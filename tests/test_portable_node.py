from __future__ import annotations

import unittest
from unittest import mock
from llm_adapter import portable_node


class PortableNodeTests(unittest.TestCase):
    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_process_backend_is_selected_without_manual_action(self) -> None:
        self._setattr(portable_node.shutil, "which", lambda name: None)
        result = portable_node.resolve_backend(["process", "container"])
        assert result.backend == "process"
        assert result.manual_action_required is False
        assert result.profile.process_available is True

    def test_preferred_unavailable_backend_falls_back(self) -> None:
        self._setattr(portable_node.shutil, "which", lambda name: None)
        result = portable_node.resolve_backend(["wasm", "process"], preferred="wasm")
        assert result.backend == "process"

    def test_peer_backend_can_be_selected_from_environment(self) -> None:
        self._setattr(portable_node.shutil, "which", lambda name: None)
        result = portable_node.resolve_backend(
            ["peer"],
            env={"STEGVERSE_PEER_EXECUTOR_ENDPOINT": "https://peer.invalid/execute"},
        )
        assert result.backend == "peer"
        assert result.profile.peer_available is True

    def test_resolution_fails_closed_when_no_backend_exists(self) -> None:
        self._setattr(portable_node.shutil, "which", lambda name: None)
        with self.assertRaisesRegex(RuntimeError, "capability remains unconstructed"):
            portable_node.resolve_backend(["wasm", "container"], env={})


if __name__ == "__main__":
    unittest.main()
