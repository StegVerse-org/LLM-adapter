from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from llm_adapter.node_bootstrap import bootstrap
from llm_adapter.node_service import _runtime_environment


class PortableNodeRuntimeContractTests(unittest.TestCase):
    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

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

    def test_bootstrap_defaults_fail_closed_and_supports_authorized_host_binding(self) -> None:
        tmp_path = self._tmp_path()
        receipt = bootstrap(tmp_path)
        manifest_path = Path(receipt["capability_manifest"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest["capability_id"] == "ecosystem-chat-gateway"
        assert manifest["version"] == "1.4.0"
        assert manifest["entrypoint"][-4:] == ["--host", "${HOST}", "--port", "${PORT}"]
        assert manifest["environment_defaults"]["HOST"] == "127.0.0.1"
        assert manifest["environment_defaults"]["STEGVERSE_PROVIDER_ENABLED"] == "false"
        assert manifest["environment_defaults"]["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"
        assert manifest["portability"]["authorized_host_binding_supported"] is True
        assert receipt["manual_action_required"] is False

    def test_runtime_environment_preserves_authorized_configuration(self) -> None:
        tmp_path = self._tmp_path()
        receipt = bootstrap(tmp_path)
        manifest = json.loads(Path(receipt["capability_manifest"]).read_text(encoding="utf-8"))

        self._setenv("HOST", "0.0.0.0")
        self._setenv("PORT", "9010")
        self._setenv("STEGVERSE_PROVIDER_ENABLED", "true")
        self._setenv("STEGVERSE_PROVIDER_ENDPOINT", "https://provider.example/v1/chat")
        self._setenv("STEGVERSE_MASTER_RECORDS_ENDPOINT", "https://records.example/v1")

        env = _runtime_environment(tmp_path, manifest)

        assert env["HOST"] == "0.0.0.0"
        assert env["PORT"] == "9010"
        assert env["STEGVERSE_PROVIDER_ENABLED"] == "true"
        assert env["STEGVERSE_PROVIDER_ENDPOINT"] == "https://provider.example/v1/chat"
        assert env["STEGVERSE_MASTER_RECORDS_ENDPOINT"] == "https://records.example/v1"
        assert env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"
        assert env["STEGVERSE_NODE_ROOT"] == str(tmp_path)

    def test_runtime_environment_uses_fail_closed_defaults_without_authorized_configuration(self) -> None:
        tmp_path = self._tmp_path()
        for key in (
            "HOST",
            "PORT",
            "STEGVERSE_PROVIDER_ENABLED",
            "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS",
            "STEGVERSE_DATA_DIR",
        ):
            self._delenv(key, raising=False)

        receipt = bootstrap(tmp_path)
        manifest = json.loads(Path(receipt["capability_manifest"]).read_text(encoding="utf-8"))
        env = _runtime_environment(tmp_path, manifest)

        assert env["HOST"] == "127.0.0.1"
        assert env["PORT"] == "8000"
        assert env["STEGVERSE_PROVIDER_ENABLED"] == "false"
        assert env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"
        assert env["STEGVERSE_DATA_DIR"] == str(tmp_path / "state")


if __name__ == "__main__":
    unittest.main()
