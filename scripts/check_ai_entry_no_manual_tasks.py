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

SUPPORTED_WORKFLOW_COMMANDS = (
    "python scripts/verify_goal4.py",
    "python scripts/verify_goal4_full.py",
)


def fail(message: str) -> None:
    raise SystemExit(f"AI_ENTRY_ADAPTER_NO_MANUAL_TASKS_FAIL: {message}")


def require_text(path: Path, markers: tuple[str, ...]) -> str:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            fail(f"{path.relative_to(ROOT)} missing {marker}")
    return text


def require_supported_workflow(path: Path) -> None:
    text = require_text(path, ("workflow_dispatch",))
    if not any(command in text for command in SUPPORTED_WORKFLOW_COMMANDS):
        fail(f"{path.relative_to(ROOT)} missing supported Goal 4 validation command")


def main() -> int:
    require_text(AGGREGATE, ("verify_ai_entry_service_wrapper.py", "tests/test_ai_entry_service_wrapper.py"))
    require_supported_workflow(CANONICAL)
    require_supported_workflow(MIRROR)
    require_text(STATUS, ("installation_complete == true", "workflow_run_confirmed == false"))
    require_text(WORKFLOW_STATUS, ("Canonical: .github/workflows/validate.yml", "Mirror: iosnoperiod/github/workflows/validate.yml"))
    require_text(
        HANDOFF,
        (
            "This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.",
            "LOCAL_IMPLEMENTATION_INSTALLED_DEPLOYMENT_VALIDATION_PENDING",
            "provider usage event != authority",
            "SQLite usage persistence != Master-Records custody",
            "## Next task",
            "Observe and inspect the current-main validate run",
        ),
    )
    print("AI_ENTRY_ADAPTER_NO_MANUAL_TASKS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
