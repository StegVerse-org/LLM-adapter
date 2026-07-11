#!/usr/bin/env python3
"""Run LLM-adapter return-path, AI Entry, free-tier trust, and transition-candidate checks."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]

COMMANDS: tuple[tuple[str, ...], ...] = (
    (sys.executable, "scripts/check_lightweight_package_init.py"),
    (sys.executable, "scripts/verify_micro_node_return_path.py"),
    (sys.executable, "scripts/verify_ai_entry_provider_boundary.py"),
    (sys.executable, "scripts/verify_ai_entry_backend_service.py"),
    (sys.executable, "scripts/verify_ai_entry_endpoint.py"),
    (sys.executable, "scripts/verify_ai_entry_service_wrapper.py"),
    (sys.executable, "scripts/check_ai_entry_no_manual_tasks.py"),
    (sys.executable, "scripts/verify_free_tier_quota.py"),
    (sys.executable, "scripts/verify_free_tier_limits.py"),
    (sys.executable, "scripts/verify_ai_entry_free_tier_metadata.py"),
    (sys.executable, "scripts/verify_free_tier_capability_manifest.py"),
    (sys.executable, "scripts/verify_llm_transition_candidate.py", "examples/llm_transition_candidate.json"),
    (sys.executable, "-m", "pytest", "tests/test_micro_node_return_path.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_ai_entry_provider_boundary.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_ai_entry_backend_service.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_ai_entry_backend_preview_marker.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_ai_entry_endpoint.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_ai_entry_service_wrapper.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_free_tier_quota.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_free_tier_limits.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_ai_entry_free_tier_trust_metadata.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_transition_candidate.py", "-v"),
)


def run_command(command: Sequence[str]) -> dict[str, object]:
    completed = subprocess.run(
        list(command), cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False,
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
        "goal": "AI Entry adapter, free-tier trust, and governed transition candidate checks",
        "repository": "StegVerse-org/LLM-adapter",
        "complete": passed,
        "results": results,
        "next_step": "review command output" if passed else "repair failing command output",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
