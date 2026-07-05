#!/usr/bin/env python3
"""Verify AI Entry adapter validation is wired so no manual verification task is required."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / ".github" / "workflows" / "validate.yml"
MIRROR = ROOT / "iosnoperiod" / "github" / "workflows" / "validate.yml"
AGGREGATE = ROOT / "scripts" / "verify_goal4.py"
STATUS = ROOT / "docs" / "AI_ENTRY_ADAPTER_RUN_STATUS.md"
WORKFLOW_STATUS = ROOT / "docs" / "AI_ENTRY_WORKFLOW_STATUS.md"
HANDOFF = ROOT / "LLM_ADAPTER_MIRROR_HANDOFF.md"

REQUIRED = "python scripts/verify_goal4.py"


def fail(message: str) -> None:
    raise SystemExit(f"AI_ENTRY_ADAPTER_NO_MANUAL_TASKS_FAIL: {message}")


def require_text(path: Path, markers: tuple[str, ...]) -> None:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            fail(f"{path.relative_to(ROOT)} missing {marker}")


def main() -> int:
    require_text(AGGREGATE, ("verify_ai_entry_service_wrapper.py", "tests/test_ai_entry_service_wrapper.py"))
    require_text(CANONICAL, (REQUIRED, "workflow_dispatch"))
    require_text(MIRROR, (REQUIRED, "workflow_dispatch"))
    require_text(STATUS, ("installation_complete == true", "workflow_run_confirmed == false"))
    require_text(WORKFLOW_STATUS, ("Canonical: .github/workflows/validate.yml", "Mirror: iosnoperiod/github/workflows/validate.yml"))
    require_text(HANDOFF, ("None for the adapter-side preview/service-wrapper boundary", "complete thread can be archived"))
    print("AI_ENTRY_ADAPTER_NO_MANUAL_TASKS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
