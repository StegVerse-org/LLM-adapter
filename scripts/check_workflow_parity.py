#!/usr/bin/env python3
"""Verify LLM-adapter canonical and iOS-safe workflow mirrors stay aligned."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / ".github" / "workflows" / "validate.yml"
MIRROR = ROOT / "iosnoperiod" / "github" / "workflows" / "validate.yml"
REQUIRED_COMMAND = "python scripts/verify_goal4_full.py"


def fail(message: str) -> None:
    raise SystemExit(f"ADAPTER_WORKFLOW_PARITY_FAIL: {message}")


def main() -> int:
    if not CANONICAL.exists():
        fail("missing canonical workflow")
    if not MIRROR.exists():
        fail("missing iOS workflow mirror")
    canonical = CANONICAL.read_text(encoding="utf-8")
    mirror = MIRROR.read_text(encoding="utf-8")
    if canonical != mirror:
        fail("canonical workflow and iOS mirror differ")
    for marker in ("push:", "pull_request:", "workflow_dispatch:", REQUIRED_COMMAND):
        if marker not in canonical:
            fail(f"workflow missing marker: {marker}")
    print("ADAPTER_WORKFLOW_PARITY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
