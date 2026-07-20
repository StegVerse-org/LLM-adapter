#!/usr/bin/env python3
"""Discover and supervise portable-node capabilities without manual wiring."""
from __future__ import annotations

import json
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_DIR = ROOT / "runtime/capabilities"
STATE_PATH = ROOT / ".stegdeploy/node-state.json"


def discover() -> list[Path]:
    manifests: list[Path] = []
    for path in sorted(CAPABILITY_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("node", {}).get("auto_start", False):
            manifests.append(path)
    return manifests


def write_state(children: dict[str, subprocess.Popen[str]], state: str) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "stegverse.portable-node-state.v1",
        "state": state,
        "manual_capability_selection_required": False,
        "capabilities": {name: {"pid": proc.pid, "running": proc.poll() is None} for name, proc in children.items()},
    }
    STATE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    manifests = discover()
    if not manifests:
        raise SystemExit("no auto-start capabilities discovered")
    children: dict[str, subprocess.Popen[str]] = {}
    for manifest in manifests:
        capability_id = json.loads(manifest.read_text(encoding="utf-8"))["capability_id"]
        children[capability_id] = subprocess.Popen(
            [sys.executable, str(ROOT / "scripts/stegcap.py"), "supervise", "--manifest", str(manifest)],
            cwd=ROOT,
            text=True,
        )
    write_state(children, "RUNNING")
    stopping = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True
        for child in children.values():
            if child.poll() is None:
                child.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping:
        for capability_id, child in list(children.items()):
            if child.poll() is not None:
                manifest = next(path for path in manifests if json.loads(path.read_text(encoding="utf-8"))["capability_id"] == capability_id)
                children[capability_id] = subprocess.Popen(
                    [sys.executable, str(ROOT / "scripts/stegcap.py"), "supervise", "--manifest", str(manifest)],
                    cwd=ROOT,
                    text=True,
                )
        write_state(children, "RUNNING")
        time.sleep(3)
    for child in children.values():
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            child.kill()
    write_state(children, "DISSOLVED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
