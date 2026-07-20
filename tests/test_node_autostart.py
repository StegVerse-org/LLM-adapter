from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from llm_adapter import node_autostart


def test_linux_materialization_uses_user_service(tmp_path: Path) -> None:
    receipt = node_autostart.materialize(
        tmp_path / "node",
        system="linux",
        env={"XDG_CONFIG_HOME": str(tmp_path / "config")},
    )
    path = Path(receipt["registration_path"])
    text = path.read_text(encoding="utf-8")
    assert receipt["registration_kind"] == "systemd-user"
    assert "Restart=always" in text
    assert "llm_adapter.node_service" in text
    assert receipt["manual_action_required"] is False


def test_macos_materialization_uses_launch_agent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(node_autostart.Path, "home", classmethod(lambda cls: tmp_path))
    receipt = node_autostart.materialize(tmp_path / "node", system="darwin")
    assert receipt["registration_kind"] == "launch-agent"
    assert Path(receipt["registration_path"]).suffix == ".plist"


def test_windows_materialization_uses_logon_task(tmp_path: Path) -> None:
    receipt = node_autostart.materialize(
        tmp_path / "node",
        system="windows",
        env={"APPDATA": str(tmp_path / "appdata")},
    )
    assert receipt["registration_kind"] == "scheduled-task"
    assert receipt["activation_commands"][0][0].lower() == "schtasks"


def test_failed_registration_falls_back_to_detached_start(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(node_autostart, "start", lambda root: {"state": "RUNNING", "node_root": str(root)})

    def runner(*_args, **_kwargs):
        return SimpleNamespace(returncode=1)

    receipt = node_autostart.install(tmp_path / "node", runner=runner, system="linux")
    assert receipt["active"] is True
    assert receipt["fallback_detached_start"]["state"] == "RUNNING"
    assert receipt["manual_action_required"] is False
