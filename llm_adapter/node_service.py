"""Run the portable Ecosystem Chat node without manual runtime wiring."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from llm_adapter.node_bootstrap import bootstrap, default_node_root


def _state_path(root: Path) -> Path:
    return root / "state" / "node-service.json"


def _lock_path(root: Path) -> Path:
    return root / "state" / "node-service.lock"


def _read_state(root: Path) -> dict[str, Any]:
    path = _state_path(root)
    if not path.exists():
        return {"state": "STOPPED", "node_root": str(root), "manual_action_required": False}
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _write_state(root: Path, payload: dict[str, Any]) -> None:
    _atomic_json_write(_state_path(root), payload)


def _write_receipt(root: Path, event: str, payload: dict[str, Any]) -> None:
    receipt = {
        "schema": "stegverse.portable-node-runtime-receipt.v1",
        "event": event,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "manual_action_required": False,
        **payload,
    }
    receipt_dir = root / "receipts" / "node-runtime"
    _atomic_json_write(receipt_dir / f"{event}.latest.json", receipt)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _claim_daemon(root: Path) -> bool:
    """Atomically claim singleton ownership, repairing stale ownership automatically."""
    path = _lock_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                owner = int(path.read_text(encoding="utf-8").strip() or "0")
            except (OSError, ValueError):
                owner = 0
            if _pid_alive(owner):
                return False
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(f"{os.getpid()}\n")
        return True
    return False


def _release_daemon(root: Path) -> None:
    path = _lock_path(root)
    try:
        owner = int(path.read_text(encoding="utf-8").strip() or "0")
    except (FileNotFoundError, OSError, ValueError):
        return
    if owner == os.getpid():
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _runtime_environment(root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    """Apply fail-closed defaults without overriding authorized runtime configuration."""
    env = os.environ.copy()
    for key, value in manifest.get("environment_defaults", {}).items():
        env.setdefault(str(key), str(value))
    env["STEGVERSE_NODE_ROOT"] = str(root)
    env.setdefault("STEGVERSE_DATA_DIR", str(root / "state"))
    return env


def _health_url(env: dict[str, str], manifest: dict[str, Any]) -> str:
    host = env.get("HOST", "127.0.0.1")
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    port = env.get("PORT", "8000")
    path = str(manifest.get("health", {}).get("path", "/health"))
    return f"http://{host}:{port}{path}"


def _wait_for_health(env: dict[str, str], manifest: dict[str, Any], child: subprocess.Popen[Any]) -> bool:
    health = manifest.get("health", {})
    attempts = max(1, int(health.get("attempts", 30)))
    timeout = max(0.1, float(health.get("timeout_seconds", 3)))
    url = _health_url(env, manifest)
    for _ in range(attempts):
        if child.poll() is not None:
            return False
        try:
            with urlopen(url, timeout=timeout) as response:
                if 200 <= int(response.status) < 300:
                    return True
        except (OSError, URLError, TimeoutError):
            pass
        time.sleep(min(1.0, timeout))
    return False


def _restart_delay(failures: int, base: float = 1.0, maximum: float = 60.0) -> float:
    return min(maximum, base * (2 ** max(0, failures - 1)))


def start(root: Path) -> dict[str, Any]:
    bootstrap(root)
    current = _read_state(root)
    pid = int(current.get("pid", 0) or 0)
    if current.get("state") in {"STARTING", "RUNNING", "RECONSTRUCTING"} and _pid_alive(pid):
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
        "state": "STARTING",
        "pid": process.pid,
        "node_root": str(root),
        "manual_action_required": False,
        "restart_policy": "reconstruct-on-failure",
    }
    _write_state(root, payload)
    _write_receipt(root, "service-start", payload)
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
    _write_receipt(root, "service-stop", payload)
    return payload


def daemon(root: Path) -> int:
    bootstrap(root)
    if not _claim_daemon(root):
        _write_receipt(root, "duplicate-daemon-refused", {
            "state": "REFUSED",
            "node_root": str(root),
            "pid": os.getpid(),
        })
        return 0
    try:
        return _daemon_owned(root)
    finally:
        _release_daemon(root)


def _daemon_owned(root: Path) -> int:
    manifest_path = root / "capabilities" / "ecosystem-chat-gateway.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    env = _runtime_environment(root, manifest)

    stopping = False
    child: subprocess.Popen[Any] | None = None
    failures = 0

    def request_stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True
        if child is not None and child.poll() is None:
            child.terminate()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    while not stopping:
        launch_started = time.monotonic()
        try:
            for command in manifest.get("preflight", []):
                subprocess.run(command, cwd=root, env=env, check=True)
            entrypoint = [env.get(part[2:-1], part) if part.startswith("${") and part.endswith("}") else part for part in manifest["entrypoint"]]
            entrypoint[0] = sys.executable if entrypoint[0] == "python" else entrypoint[0]
            child = subprocess.Popen(entrypoint, cwd=root, env=env)
            healthy = _wait_for_health(env, manifest, child)
            if not healthy:
                if child.poll() is None:
                    child.terminate()
                raise RuntimeError("capability failed health verification")
            failures = 0
            running = {
                "schema": "stegverse.portable-node-service-state.v1",
                "state": "RUNNING",
                "pid": os.getpid(),
                "capability_pid": child.pid,
                "node_root": str(root),
                "manual_action_required": False,
                "restart_policy": "reconstruct-on-failure",
                "health_url": _health_url(env, manifest),
                "host": env.get("HOST"),
                "port": env.get("PORT"),
                "provider_enabled": env.get("STEGVERSE_PROVIDER_ENABLED", "false").lower() == "true",
                "durable_storage": env.get("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "false").lower() == "true",
            }
            _write_state(root, running)
            _write_receipt(root, "capability-ready", running)
            while not stopping and child.poll() is None:
                time.sleep(1)
            if stopping:
                break
            exit_code = child.returncode
            reason = "capability-exit"
        except Exception as exc:
            exit_code = None if child is None else child.poll()
            reason = f"{type(exc).__name__}: {exc}"

        failures += 1
        delay = _restart_delay(failures)
        reconstructing = {
            "schema": "stegverse.portable-node-service-state.v1",
            "state": "RECONSTRUCTING",
            "last_exit": exit_code,
            "failure_reason": reason,
            "consecutive_failures": failures,
            "restart_delay_seconds": delay,
            "runtime_seconds": round(time.monotonic() - launch_started, 3),
            "pid": os.getpid(),
            "node_root": str(root),
            "manual_action_required": False,
        }
        _write_state(root, reconstructing)
        _write_receipt(root, "capability-reconstructing", reconstructing)
        deadline = time.monotonic() + delay
        while not stopping and time.monotonic() < deadline:
            time.sleep(min(0.25, deadline - time.monotonic()))

    if child is not None and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)
    dissolved = {
        "schema": "stegverse.portable-node-service-state.v1",
        "state": "DISSOLVED",
        "node_root": str(root),
        "manual_action_required": False,
    }
    _write_state(root, dissolved)
    _write_receipt(root, "service-dissolved", dissolved)
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
        active_states = {"STARTING", "RUNNING", "RECONSTRUCTING"}
        if result.get("state") in active_states and not _pid_alive(pid):
            result = {**result, "state": "STALE", "running": False}
        else:
            result = {**result, "running": result.get("state") in active_states and _pid_alive(pid)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
