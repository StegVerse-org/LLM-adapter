#!/usr/bin/env python3
"""Run adapter Goal 4 aggregate plus final boundary checks."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]

COMMANDS: tuple[tuple[str, ...], ...] = (
    (sys.executable, "scripts/verify_goal4.py"),
    (sys.executable, "scripts/check_workflow_parity.py"),
    (sys.executable, "scripts/check_ai_entry_authority_boundary.py"),
    (sys.executable, "scripts/check_ai_entry_receipt_boundary.py"),
)


def run(command: Sequence[str]) -> None:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print("$ " + " ".join(command))
    print(completed.stdout.rstrip())
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    for command in COMMANDS:
        run(command)
    print("ADAPTER_GOAL4_FULL_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
