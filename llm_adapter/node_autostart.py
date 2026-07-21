"""Register the portable node to reconstruct automatically at user login."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import subprocess
import sys
from typing import Any, Callable

from llm_adapter.node_bootstrap import bootstrap, default_node_root
from llm_adapter.node_service import start

Runner = Callable[..., subprocess.CompletedProcess[Any]]


def _command(root: Path) -> list[str]:
    return [sys.executable, "-m", "llm_adapter.node_service", "daemon", "--root", str(root)]


def _user_id(values: dict[str, str]) -> int:
    getter = getattr(os, "getuid", None)
    if callable(getter):
        return int(getter())
    return int(values.get("UID", "0"))


def materialize(root: Path, system: str | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    bootstrap(root)
    name = (system or platform.system()).lower()
    values = dict(os.environ if env is None else env)
    command = _command(root)
    if name == "linux":
        config_home = Path(values.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        path = config_home / "systemd" / "user" / "stegverse-portable-node.service"
        content = "\n".join([
            "[Unit]", "Description=StegVerse Portable Node", "After=network-online.target", "",
            "[Service]", "Type=simple",
            "ExecStart=" + " ".join(f'"{part}"' for part in command),
            "Restart=always", "RestartSec=2", f'Environment=STEGVERSE_NODE_ROOT={root}', "",
            "[Install]", "WantedBy=default.target", "",
        ])
        activate = [["systemctl", "--user", "daemon-reload"], ["systemctl", "--user", "enable", "--now", path.name]]
        kind = "systemd-user"
    elif name == "darwin":
        path = Path.home() / "Library" / "LaunchAgents" / "org.stegverse.portable-node.plist"
        payload = {
            "Label": "org.stegverse.portable-node", "ProgramArguments": command,
            "RunAtLoad": True, "KeepAlive": True,
            "EnvironmentVariables": {"STEGVERSE_NODE_ROOT": str(root)},
            "StandardOutPath": str(root / "state" / "node-service.stdout.log"),
            "StandardErrorPath": str(root / "state" / "node-service.stderr.log"),
        }
        content = plistlib.dumps(payload).decode("utf-8")
        domain = f"gui/{_user_id(values)}"
        activate = [["launchctl", "bootout", domain, str(path)], ["launchctl", "bootstrap", domain, str(path)]]
        kind = "launch-agent"
    elif name == "windows":
        appdata = Path(values.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        path = appdata / "StegVerse" / "portable-node-start.cmd"
        content = "@echo off\r\n" + subprocess.list2cmdline(command) + "\r\n"
        activate = [["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", "StegVerse Portable Node", "/TR", str(path)]]
        kind = "scheduled-task"
    else:
        raise RuntimeError(f"unsupported autostart platform: {name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    receipt = {
        "schema": "stegverse.portable-node-autostart.v1", "platform": name,
        "registration_kind": kind, "registration_path": str(path),
        "activation_commands": activate, "manual_action_required": False,
    }
    receipt_path = root / "receipts" / "autostart.latest.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def install(root: Path, runner: Runner = subprocess.run, system: str | None = None) -> dict[str, Any]:
    receipt = materialize(root, system=system)
    results: list[dict[str, Any]] = []
    for command in receipt["activation_commands"]:
        completed = runner(command, check=False, capture_output=True, text=True)
        results.append({"command": command, "returncode": completed.returncode})
    receipt["activation_results"] = results
    receipt["active"] = bool(results) and results[-1]["returncode"] == 0
    if not receipt["active"]:
        fallback = start(root)
        receipt["fallback_detached_start"] = fallback
        receipt["active"] = fallback.get("state") in {"STARTING", "RUNNING", "RECONSTRUCTING"}
    receipt["manual_action_required"] = False
    path = root / "receipts" / "autostart.latest.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Register and activate StegVerse portable-node autostart")
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    root = (args.root or default_node_root()).resolve()
    print(json.dumps(install(root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
