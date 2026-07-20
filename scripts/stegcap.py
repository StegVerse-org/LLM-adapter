#!/usr/bin/env python3
"""Construct, verify, supervise, and dissolve a StegVerse capability."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import sys
import time

from llm_adapter.capability_runtime import ROOT, load_manifest, reconstruct_process

DEFAULT_MANIFEST = ROOT / "runtime/capabilities/ecosystem-chat-gateway.json"
STATE_FILE = ROOT / ".stegdeploy/capability-state.json"


def _write_state(payload: dict[str, object]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(manifest_path: Path, supervise: bool) -> int:
    manifest = load_manifest(manifest_path)
    process = reconstruct_process(manifest_path)
    _write_state({"capability_id": manifest["capability_id"], "pid": process.pid, "state": "RUNNING"})
    if not supervise:
        print(json.dumps({"capability_id": manifest["capability_id"], "pid": process.pid, "state": "RUNNING"}))
        return 0

    stopping = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True
        process.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping:
        result = process.poll()
        if result is None:
            time.sleep(2)
            continue
        _write_state({"capability_id": manifest["capability_id"], "state": "RECONSTRUCTING", "last_exit": result})
        process = reconstruct_process(manifest_path)
        _write_state({"capability_id": manifest["capability_id"], "pid": process.pid, "state": "RUNNING"})
    process.wait(timeout=15)
    _write_state({"capability_id": manifest["capability_id"], "state": "DISSOLVED"})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "supervise", "show-manifest"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    if args.command == "show-manifest":
        print(json.dumps(load_manifest(args.manifest), indent=2, sort_keys=True))
        return 0
    return run(args.manifest, supervise=args.command == "supervise")


if __name__ == "__main__":
    raise SystemExit(main())
