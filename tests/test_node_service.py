from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from llm_adapter import node_service


def test_start_bootstraps_and_records_detached_service(tmp_path: Path, monkeypatch) -> None:
    launched: dict[str, object] = {}

    def fake_popen(command: list[str], **kwargs: object) -> SimpleNamespace:
        launched["command"] = command
        launched["kwargs"] = kwargs
        return SimpleNamespace(pid=4321)

    monkeypatch.setattr(node_service.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(node_service, "_pid_alive", lambda _pid: False)

    state = node_service.start(tmp_path)

    assert (tmp_path / "node-profile.json").exists()
    assert state["state"] == "STARTING"
    assert state["pid"] == 4321
    assert state["manual_action_required"] is False
    assert launched["command"][-3:] == ["daemon", "--root", str(tmp_path.resolve())]
    receipt = json.loads((tmp_path / "receipts" / "node-runtime" / "service-start.latest.json").read_text(encoding="utf-8"))
    assert receipt["event"] == "service-start"


def test_start_is_idempotent_for_live_service(tmp_path: Path, monkeypatch) -> None:
    node_service._write_state(tmp_path, {
        "state": "RUNNING",
        "pid": 99,
        "node_root": str(tmp_path),
        "manual_action_required": False,
    })
    monkeypatch.setattr(node_service, "_pid_alive", lambda pid: pid == 99)
    monkeypatch.setattr(node_service.subprocess, "Popen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not relaunch")))

    state = node_service.start(tmp_path)
    assert state["pid"] == 99


def test_stop_writes_dissolved_state_and_receipt(tmp_path: Path, monkeypatch) -> None:
    node_service._write_state(tmp_path, {"state": "RUNNING", "pid": 88})
    monkeypatch.setattr(node_service, "_pid_alive", lambda _pid: False)

    state = node_service.stop(tmp_path)
    stored = json.loads((tmp_path / "state" / "node-service.json").read_text(encoding="utf-8"))
    receipt = json.loads((tmp_path / "receipts" / "node-runtime" / "service-stop.latest.json").read_text(encoding="utf-8"))

    assert state["state"] == "DISSOLVED"
    assert stored["manual_action_required"] is False
    assert receipt["event"] == "service-stop"


def test_unstarted_status_requires_no_manual_selection(tmp_path: Path) -> None:
    state = node_service._read_state(tmp_path)
    assert state == {
        "state": "STOPPED",
        "node_root": str(tmp_path),
        "manual_action_required": False,
    }


def test_atomic_state_write_leaves_no_temporary_file(tmp_path: Path) -> None:
    node_service._write_state(tmp_path, {"state": "RUNNING", "pid": 7})
    assert json.loads((tmp_path / "state" / "node-service.json").read_text(encoding="utf-8"))["pid"] == 7
    assert list((tmp_path / "state").glob("*.tmp")) == []
    assert list((tmp_path / "state").glob(".*.tmp")) == []


def test_restart_delay_is_bounded_exponential() -> None:
    assert node_service._restart_delay(1) == 1.0
    assert node_service._restart_delay(4) == 8.0
    assert node_service._restart_delay(20) == 60.0


def test_health_url_uses_loopback_for_wildcard_host() -> None:
    manifest = {"health": {"path": "/healthz"}}
    assert node_service._health_url({"HOST": "0.0.0.0", "PORT": "8123"}, manifest) == "http://127.0.0.1:8123/healthz"
