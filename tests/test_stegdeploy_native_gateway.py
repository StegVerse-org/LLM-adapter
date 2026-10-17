from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import stegdeploy_native_gateway as mod


class StegdeployNativeGatewayTests(unittest.TestCase):
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

    def _setitem(self, mapping, key, value):
        """monkeypatch.setitem equivalent: the mapping is restored after the test."""
        patcher = mock.patch.dict(mapping, {key: value})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_child_env_binds_evaluator_to_same_host_loopback(self) -> None:
        tmp_path = self._tmp_path()
        env = mod.child_env(
            durable_root=tmp_path / "data",
            evaluator_enabled=True,
            evaluator_upstream="http://127.0.0.1:8765/intr/evaluator",
            tls_cert=None,
            tls_key=None,
            env={"PATH":"/bin"},
        )
        assert env["STEGVERSE_RUNTIME_PROFILE"] == "sovereign-carrier"
        assert env["STEGVERSE_EVALUATOR_INTR_ENABLED"] == "true"
        assert env["STEGVERSE_EVALUATOR_INTR_UPSTREAM"] == "http://127.0.0.1:8765/intr/evaluator"
        assert env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"

    def test_child_env_disables_evaluator_without_route(self) -> None:
        tmp_path = self._tmp_path()
        env = mod.child_env(
            durable_root=tmp_path / "data",
            evaluator_enabled=False,
            evaluator_upstream="http://127.0.0.1:8765/intr/evaluator",
            tls_cert=None,
            tls_key=None,
            env={},
        )
        assert env["STEGVERSE_EVALUATOR_INTR_ENABLED"] == "false"
        assert env["STEGVERSE_EVALUATOR_INTR_UPSTREAM"] == ""

    def test_hosted_runtime_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "hosted_runtime_forbidden"):
            mod.reject_hosted({"GITHUB_ACTIONS":"true"})

    def test_start_receipt_is_local_only_and_docker_free(self) -> None:
        tmp_path = self._tmp_path()
        state = tmp_path / "state"
        data = tmp_path / "data"
        self._setenv("STEGVERSE_SERVICE_GATEWAY_NATIVE_STATE_ROOT", str(state))
        self._setattr(mod, "reject_hosted", lambda: None)
        self._setattr(mod, "observe_health", lambda *a: (_ for _ in ()).throw(AssertionError("start must not wait on health")))

        class P:
            pid = 4242
        self._setattr(mod.subprocess, "Popen", lambda *a, **k: P())
        self._setattr(mod, "_pid_alive", lambda pid: False)

        receipt = mod.start(
            host="127.0.0.1",
            port=8000,
            durable_root=data,
            evaluator_enabled=True,
            evaluator_upstream="http://127.0.0.1:8765/intr/evaluator",
        )
        assert receipt["state"] == "LOCAL_NATIVE_GATEWAY_STARTED"
        assert receipt["destination_liveness_is_transition_predicate"] is False
        assert receipt["health"]["consequence_observation"] == "NOT_AUTHENTICALLY_OBSERVED"
        assert receipt["health"]["reconciliation_entrypoint"] == mod.RECONCILIATION_ENTRYPOINT
        assert receipt["health"]["gates_transition"] is False
        assert receipt["runtime"] == "HOST_NATIVE_PYTHON_STDLIB"
        assert receipt["same_host_evaluator_loopback"] is True
        assert receipt["docker_required"] is False
        assert receipt["third_party_runtime_required"] is False
        assert receipt["production_public_route_observed"] is False
        assert receipt["public_certificate_hostname_verified"] is False
        assert receipt["credential_authority"] == "TV/TVC"
        assert receipt["github_token_runtime_authority"] == "NONE"

    def test_native_tls_receipt_never_serializes_key_path(self) -> None:
        tmp_path = self._tmp_path()
        state = tmp_path / "state"
        data = tmp_path / "data"
        cert = tmp_path / "cert.pem"
        key = tmp_path / "private-key.pem"
        cert.write_text("cert", encoding="utf-8")
        key.write_text("key", encoding="utf-8")
        key.chmod(0o600)
        self._setenv("STEGVERSE_SERVICE_GATEWAY_NATIVE_STATE_ROOT", str(state))
        self._setattr(mod, "reject_hosted", lambda: None)
        self._setattr(mod, "validate_tls", lambda c, k: "sha256:" + "a"*64)
        self._setattr(mod, "observe_health", lambda *a: (_ for _ in ()).throw(AssertionError("start must not wait on health")))

        class P:
            pid = 4243
        self._setattr(mod.subprocess, "Popen", lambda *a, **k: P())
        self._setattr(mod, "_pid_alive", lambda pid: False)

        receipt = mod.start(
            host="0.0.0.0",
            port=443,
            durable_root=data,
            evaluator_enabled=True,
            evaluator_upstream="http://127.0.0.1:8765/intr/evaluator",
            tls_cert=cert,
            tls_key=key,
        )
        assert receipt["tls_enabled"] is True
        assert receipt["tls_private_key_material_recorded"] is False
        assert receipt["tls_private_key_path_recorded"] is False
        assert str(key) not in json.dumps(receipt)

    def test_source_has_no_docker_dependency(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "scripts/stegdeploy_native_gateway.py").read_text(encoding="utf-8")
        assert '"docker"' not in source
        assert "docker compose" not in source.lower()
        assert "web_server.run(" in source
        assert "uvicorn" not in source

    def test_health_observation_is_single_attempt_and_never_raises(self) -> None:
        calls = []

        def refuse(*args, **kwargs):
            calls.append(args)
            raise mod.urllib.error.URLError(ConnectionRefusedError(111, "refused"))

        self._setattr(mod.urllib.request, "urlopen", refuse)
        observed = mod.observe_health(8000, None)
        assert len(calls) == 1
        assert observed["consequence_observation"] == "NOT_AUTHENTICALLY_OBSERVED"
        assert observed["reason"] == "native_gateway_health_not_observed:ConnectionRefusedError"
        assert observed["reconciliation_entrypoint"] == mod.RECONCILIATION_ENTRYPOINT
        assert observed["gates_transition"] is False

    def test_source_has_no_unverified_tls_or_health_wait_loop(self) -> None:
        source = Path(mod.__file__).read_text(encoding="utf-8")
        assert "_create_unverified_context" not in source
        assert "native_gateway_health_failed" not in source

    def test_child_env_defaults_durable_stores_under_root_without_overriding(self) -> None:
        tmp_path = self._tmp_path()
        data = tmp_path / "data"
        env = mod.child_env(durable_root=data, evaluator_enabled=False, evaluator_upstream="",
                            tls_cert=None, tls_key=None, env={"STEGVERSE_TRANSITION_DB": "/srv/chat.db"})
        assert env["STEGVERSE_TRANSITION_DB"] == "/srv/chat.db"
        assert env["STEGVERSE_EXTERNAL_REVIEW_DB"] == str(data / "stegverse-external-review.db")
        assert env["STEGVERSE_HIL_DATA_DIR"] == str(data / "hil")
        assert env["STEGVERSE_GATEWAY_FORWARD_DB"] == str(data / "stegverse-gateway-forward.db")

    def test_serve_runs_startup_workers_once_then_gateway_without_raw_access_log(self) -> None:
        tmp_path = self._tmp_path()
        from llm_adapter import custody_worker, gateway_forward_queue

        order = []
        self._setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path / "hil"))
        self._delenv("STEGDEPLOY_NATIVE_TLS_CERT_FILE", raising=False)
        self._delenv("STEGDEPLOY_NATIVE_TLS_KEY_FILE", raising=False)
        self._setattr(custody_worker, "main", lambda: order.append("custody") or 0)
        self._setattr(gateway_forward_queue, "main", lambda: order.append("forward_queue") or 0)
        from llm_adapter.web import server as web_server
        self._setattr(web_server, "run", lambda app, **kw: order.append((app, kw)))

        mod.serve("127.0.0.1", 8000)

        assert order[:2] == ["custody", "forward_queue"]
        app, kwargs = order[2]
        assert app == "llm_adapter.deployed_gateway:app"
        assert kwargs["access_log"] is False
        assert (tmp_path / "hil").is_dir()


if __name__ == "__main__":
    unittest.main()
