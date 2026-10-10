"""Invocation-scoped portable-node state: status, dissolve and environment.

Existing owner: LLMA-DECLARED-PATH-CONFORMANCE-368 (StegVerse-org/.github#98,
step 6). Ecosystem Chat, HIL and VA-scoped chat are manifest-bound transport
through `llm_adapter.collab_ingress`; a turn is processed when an admitted
manifest arrives, not by a resident node. This module therefore no longer
launches a detached daemon, supervises or restarts a capability, or holds a
singleton lock. Every command does its work and returns.

`stop` remains so a node root left by an earlier resident daemon can be
dissolved deterministically; `status` reports such state as STALE when its
process is gone.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import time
from typing import Any

from llm_adapter.node_bootstrap import default_node_root


def _state_path(root: Path) -> Path:
    return root / "state" / "node-service.json"


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


def _runtime_environment(root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    """Apply fail-closed defaults without overriding authorized runtime configuration."""
    env = os.environ.copy()
    for key, value in manifest.get("environment_defaults", {}).items():
        env.setdefault(str(key), str(value))
    env["STEGVERSE_NODE_ROOT"] = str(root)
    env.setdefault("STEGVERSE_DATA_DIR", str(root / "state"))
    return env


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Invocation-scoped StegVerse portable-node state")
    parser.add_argument("command", nargs="?", default="status", choices=("status", "stop"))
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    root = (args.root or default_node_root()).resolve()
    if args.command == "stop":
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
