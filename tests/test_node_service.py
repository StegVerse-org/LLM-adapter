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
    assert state["state"] == "RUNNING"
    assert state["pid"] == 4321
    assert state["manual_action_required"] is False
    assert launched["command"][-3:] == ["daemon", "--root", str(tmp_path.resolve())]


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


def test_stop_writes_dissolved_state(tmp_path: Path, monkeypatch) -> None:
    node_service._write_state(tmp_path, {"state": "RUNNING", "pid": 88})
    monkeypatch.setattr(node_service, "_pid_alive", lambda _pid: False)

    state = node_service.stop(tmp_path)
    stored = json.loads((tmp_path / "state" / "node-service.json").read_text(encoding="utf-8"))

    assert state["state"] == "DISSOLVED"
    assert stored["manual_action_required"] is False


def test_unstarted_status_requires_no_manual_selection(tmp_path: Path) -> None:
    state = node_service._read_state(tmp_path)
    assert state == {
        "state": "STOPPED",
        "node_root": str(tmp_path),
        "manual_action_required": False,
    }
