#!/usr/bin/env python3
"""Verify LLM-adapter canonical and iOS-safe workflow mirrors stay aligned."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / ".github" / "workflows" / "validate.yml"
MIRROR = ROOT / "iosnoperiod" / "github" / "workflows" / "validate.yml"
SUPPORTED_GOAL4_COMMANDS = (
    "python scripts/verify_goal4_full.py",
    "$PYTHON_BIN scripts/verify_goal4_full.py",
)


def fail(message: str) -> None:
    raise SystemExit(f"ADAPTER_WORKFLOW_PARITY_FAIL: {message}")


def normalized_text(path: Path) -> str:
    """Compare workflow semantics without platform newline or BOM drift."""
    text = path.read_text(encoding="utf-8-sig")
    return "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"


def main() -> int:
    if not CANONICAL.exists():
        fail("missing canonical workflow")
    if not MIRROR.exists():
        fail("missing iOS workflow mirror")
    canonical = normalized_text(CANONICAL)
    mirror = normalized_text(MIRROR)
    if canonical != mirror:
        fail("canonical workflow and iOS mirror differ")
    for marker in ("push:", "pull_request:", "workflow_dispatch:"):
        if marker not in canonical:
            fail(f"workflow missing marker: {marker}")
    if not any(command in canonical for command in SUPPORTED_GOAL4_COMMANDS):
        fail("workflow missing supported Goal 4 full verification command")
    print("ADAPTER_WORKFLOW_PARITY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
