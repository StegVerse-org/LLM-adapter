from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import stegdeploy_native_gateway as mod


def test_child_env_binds_evaluator_to_same_host_loopback(tmp_path: Path) -> None:
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


def test_child_env_disables_evaluator_without_route(tmp_path: Path) -> None:
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


def test_hosted_runtime_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="hosted_runtime_forbidden"):
        mod.reject_hosted({"GITHUB_ACTIONS":"true"})


def test_start_receipt_is_local_only_and_docker_free(monkeypatch, tmp_path: Path) -> None:
    state = tmp_path / "state"
    data = tmp_path / "data"
    monkeypatch.setenv("STEGVERSE_SERVICE_GATEWAY_NATIVE_STATE_ROOT", str(state))
    monkeypatch.setattr(mod, "reject_hosted", lambda: None)
    monkeypatch.setattr(mod, "local_health", lambda port, tls: {"url":"http://127.0.0.1:8000/health","status":200,"body":{"status":"ok"}})

    class P:
        pid = 4242
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: P())
    monkeypatch.setattr(mod, "_pid_alive", lambda pid: False)

    receipt = mod.start(
        host="127.0.0.1",
        port=8000,
        durable_root=data,
        evaluator_enabled=True,
        evaluator_upstream="http://127.0.0.1:8765/intr/evaluator",
    )
    assert receipt["state"] == "LOCAL_NATIVE_GATEWAY_READY"
    assert receipt["runtime"] == "HOST_NATIVE_PYTHON_UVICORN"
    assert receipt["same_host_evaluator_loopback"] is True
    assert receipt["docker_required"] is False
    assert receipt["third_party_runtime_required"] is False
    assert receipt["production_public_route_observed"] is False
    assert receipt["public_certificate_hostname_verified"] is False
    assert receipt["credential_authority"] == "TV/TVC"
    assert receipt["github_token_runtime_authority"] == "NONE"


def test_native_tls_receipt_never_serializes_key_path(monkeypatch, tmp_path: Path) -> None:
    state = tmp_path / "state"
    data = tmp_path / "data"
    cert = tmp_path / "cert.pem"
    key = tmp_path / "private-key.pem"
    cert.write_text("cert", encoding="utf-8")
    key.write_text("key", encoding="utf-8")
    key.chmod(0o600)
    monkeypatch.setenv("STEGVERSE_SERVICE_GATEWAY_NATIVE_STATE_ROOT", str(state))
    monkeypatch.setattr(mod, "reject_hosted", lambda: None)
    monkeypatch.setattr(mod, "validate_tls", lambda c, k: "sha256:" + "a"*64)
    monkeypatch.setattr(mod, "local_health", lambda port, tls: {"url":"https://127.0.0.1:443/health","status":200,"body":{"status":"ok"}})

    class P:
        pid = 4243
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: P())
    monkeypatch.setattr(mod, "_pid_alive", lambda pid: False)

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


def test_source_has_no_docker_dependency() -> None:
    source = (Path(__file__).resolve().parents[1] / "scripts/stegdeploy_native_gateway.py").read_text(encoding="utf-8")
    assert '"docker"' not in source
    assert "docker compose" not in source.lower()
    assert "uvicorn.run(" in source
