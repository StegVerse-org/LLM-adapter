from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from llm_adapter import node_service


def test_node_service_is_invocation_scoped_with_no_resident_surface() -> None:
    for retired in ("start", "daemon", "_daemon_owned", "_claim_daemon", "_release_daemon",
                    "_lock_path", "_restart_delay", "_wait_for_health", "_health_url"):
        assert not hasattr(node_service, retired), retired
    assert not hasattr(node_service, "subprocess")


def test_cli_offers_only_invocation_scoped_commands(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["stegnode", "daemon", "--root", str(tmp_path)])
    with pytest.raises(SystemExit):
        node_service.main()
    capsys.readouterr()
    monkeypatch.setattr("sys.argv", ["stegnode", "--root", str(tmp_path)])
    assert node_service.main() == 0
    assert json.loads(capsys.readouterr().out)["state"] == "STOPPED"


def test_status_reports_leftover_resident_state_as_stale(tmp_path: Path, monkeypatch, capsys) -> None:
    node_service._write_state(tmp_path, {"state": "RUNNING", "pid": 55})
    monkeypatch.setattr(node_service, "_pid_alive", lambda _pid: False)
    monkeypatch.setattr("sys.argv", ["stegnode", "status", "--root", str(tmp_path)])
    assert node_service.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "STALE"
    assert result["running"] is False


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
