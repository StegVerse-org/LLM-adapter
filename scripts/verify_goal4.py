#!/usr/bin/env python3
"""Run Goal 4 micro-node return-path verification without network access."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]

COMMANDS: tuple[tuple[str, ...], ...] = (
    (sys.executable, "scripts/verify_micro_node_return_path.py"),
    (sys.executable, "-m", "pytest", "tests/test_micro_node_return_path.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/", "-v"),
)


def run_command(command: Sequence[str]) -> dict[str, object]:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "output": completed.stdout,
    }


def main() -> int:
    results = [run_command(command) for command in COMMANDS]
    passed = all(bool(result["passed"]) for result in results)
    report = {
        "goal": "Goal 4 micro-node governed return-path proof",
        "repository": "StegVerse-org/LLM-adapter",
        "complete": passed,
        "results": results,
        "next_step": "sync SDK and Site proof state" if passed else "repair failing command output",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
