"""Run the portable Ecosystem Chat node without manual runtime wiring."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

from llm_adapter.node_bootstrap import bootstrap, default_node_root


def _state_path(root: Path) -> Path:
    return root / "state" / "node-service.json"


def _read_state(root: Path) -> dict[str, Any]:
    path = _state_path(root)
    if not path.exists():
        return {"state": "STOPPED", "node_root": str(root), "manual_action_required": False}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_state(root: Path, payload: dict[str, Any]) -> None:
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _runtime_environment(root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    """Apply fail-closed defaults without overriding authorized runtime configuration."""
    env = os.environ.copy()
    for key, value in manifest.get("environment_defaults", {}).items():
        env.setdefault(str(key), str(value))
    env["STEGVERSE_NODE_ROOT"] = str(root)
    env.setdefault("STEGVERSE_DATA_DIR", str(root / "state"))
    return env


def start(root: Path) -> dict[str, Any]:
    bootstrap(root)
    current = _read_state(root)
    pid = int(current.get("pid", 0) or 0)
    if current.get("state") == "RUNNING" and _pid_alive(pid):
        return current

    command = [sys.executable, "-m", "llm_adapter.node_service", "daemon", "--root", str(root)]
    kwargs: dict[str, Any] = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "cwd": str(root),
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(command, **kwargs)
    payload = {
        "schema": "stegverse.portable-node-service-state.v1",
        "state": "RUNNING",
        "pid": process.pid,
        "node_root": str(root),
        "manual_action_required": False,
        "restart_policy": "reconstruct-on-failure",
    }
    _write_state(root, payload)
    return payload


def stop(root: Path) -> dict[str, Any]:
    current = _read_state(root)
    pid = int(current.get("pid", 0) or 0)
    if _pid_alive(pid):
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 15
        while _pid_alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
    payload = {
        "schema": "stegverse.portable-node-service-state.v1",
        "state": "DISSOLVED",
        "node_root": str(root),
        "manual_action_required": False,
    }
    _write_state(root, payload)
    return payload


def daemon(root: Path) -> int:
    bootstrap(root)
    manifest_path = root / "capabilities" / "ecosystem-chat-gateway.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    env = _runtime_environment(root, manifest)

    stopping = False
    child: subprocess.Popen[Any] | None = None

    def request_stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True
        if child is not None and child.poll() is None:
            child.terminate()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    while not stopping:
        for command in manifest.get("preflight", []):
            subprocess.run(command, cwd=root, env=env, check=True)
        entrypoint = [env.get(part[2:-1], part) if part.startswith("${") and part.endswith("}") else part for part in manifest["entrypoint"]]
        entrypoint[0] = sys.executable if entrypoint[0] == "python" else entrypoint[0]
        child = subprocess.Popen(entrypoint, cwd=root, env=env)
        _write_state(root, {
            "schema": "stegverse.portable-node-service-state.v1",
            "state": "RUNNING",
            "pid": os.getpid(),
            "capability_pid": child.pid,
            "node_root": str(root),
            "manual_action_required": False,
            "restart_policy": "reconstruct-on-failure",
            "host": env.get("HOST"),
            "port": env.get("PORT"),
            "provider_enabled": env.get("STEGVERSE_PROVIDER_ENABLED", "false").lower() == "true",
            "durable_storage": env.get("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "false").lower() == "true",
        })
        while not stopping and child.poll() is None:
            time.sleep(1)
        if not stopping:
            _write_state(root, {
                "schema": "stegverse.portable-node-service-state.v1",
                "state": "RECONSTRUCTING",
                "last_exit": child.returncode,
                "pid": os.getpid(),
                "node_root": str(root),
                "manual_action_required": False,
            })
            time.sleep(1)
    if child is not None and child.poll() is None:
        child.wait(timeout=15)
    _write_state(root, {
        "schema": "stegverse.portable-node-service-state.v1",
        "state": "DISSOLVED",
        "node_root": str(root),
        "manual_action_required": False,
    })
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous StegVerse portable-node service")
    parser.add_argument("command", nargs="?", default="start", choices=("start", "status", "stop", "daemon"))
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    root = (args.root or default_node_root()).resolve()
    if args.command == "daemon":
        return daemon(root)
    if args.command == "start":
        result = start(root)
    elif args.command == "stop":
        result = stop(root)
    else:
        result = _read_state(root)
        pid = int(result.get("pid", 0) or 0)
        if result.get("state") == "RUNNING" and not _pid_alive(pid):
            result = {**result, "state": "STALE", "running": False}
        else:
            result = {**result, "running": result.get("state") == "RUNNING" and _pid_alive(pid)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
