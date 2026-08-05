#!/usr/bin/env python3
"""Fail closed when LLM-adapter task ownership or publication activation drifts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "llm-adapter-orchestration-state.json"
TASK_PATH = ROOT / "tasks" / "LLMA-PUBLICATION-ACTIVATION-013.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "stegdeploy-image.yml"
HANDOFF_PATH = ROOT / "docs" / "STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md"


def fail(message: str) -> None:
    raise SystemExit(f"LLM_ADAPTER_ORCHESTRATION_STATE_FAIL: {message}")


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON at {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected object at {path.relative_to(ROOT)}")
    return value


def task_by_id(items: list[dict], task_id: str) -> dict:
    matches = [item for item in items if item.get("task_id") == task_id]
    if len(matches) != 1:
        fail(f"expected exactly one {task_id}; found {len(matches)}")
    return matches[0]


def main() -> int:
    state = load_json(STATE_PATH)
    task = load_json(TASK_PATH)

    if state.get("schema_version") != "1.1.0":
        fail("unexpected orchestration schema version")
    if state.get("repository") != "StegVerse-org/LLM-adapter":
        fail("repository mismatch")
    if state.get("status") != "ACTIVE_WITH_DECLARED_BLOCKERS":
        fail("unexpected repository status")

    active = state.get("active_tasks") or []
    if not isinstance(active, list) or not active:
        fail("active task registry missing")
    task_ids = [item.get("task_id") for item in active]
    if len(task_ids) != len(set(task_ids)):
        fail("duplicate active task IDs")
    if any(item.get("owner") == "pull/44" for item in active):
        fail("closed PR #44 remains an active owner")

    hil = task_by_id(active, "LLMA-0001-HIL-CYCLE")
    if hil.get("owner") != "pull/56" or hil.get("superseded_owner") != "pull/44":
        fail("HIL owner reconciliation is incomplete")

    publication = task_by_id(active, "LLMA-0001-IMAGE-PUBLICATION")
    if publication.get("owner") != "issue/18":
        fail("publication evidence must remain owned by issue #18")
    if publication.get("task_record") != "tasks/LLMA-PUBLICATION-ACTIVATION-013.json":
        fail("publication task record mismatch")

    completed = state.get("completed_tasks") or []
    merged = task_by_id(completed, "LLMA-SESSION-PROVIDER-LAYER-2026-08-02")
    if merged.get("state") != "MERGED_INTO_CANONICAL_WORKSTREAM":
        fail("merged PR #95 claim is not released")
    if merged.get("merge_commit") != "1505aac0073bc6466769ca84c6ae28d887abdefd":
        fail("PR #95 merge evidence mismatch")

    queued = state.get("queued_exclusive_tasks") or []
    live = task_by_id(queued, "LLMA-0002-LIVE-PROVIDER")
    if live.get("owner") != "issue/18" or live.get("execution_class") != "EXCLUSIVE":
        fail("live provider task ownership or class changed")
    blockers = set(live.get("external_blockers") or [])
    required_blockers = {
        "authorized provider configuration",
        "persistent endpoint",
        "published-package consumer access evidence",
        "authenticated Master Records custody configuration",
    }
    if not required_blockers <= blockers:
        fail("exclusive provider blockers were weakened")

    authority = state.get("authority") or {}
    if not authority or any(value is not False for value in authority.values()):
        fail("orchestration state grants authority")

    if task.get("task_id") != "LLMA-PUBLICATION-ACTIVATION-013":
        fail("activation task ID mismatch")
    if task.get("state") != "CLAIMED_FOR_IMPLEMENTATION_AND_INTEGRATION":
        fail("activation task is not actively claimed")
    if task.get("canonical_issue") != "StegVerse-org/LLM-adapter#18":
        fail("activation task canonical owner mismatch")
    if task.get("authority_effect") is not False:
        fail("activation task grants authority")

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    if "schedule:" not in workflow or 'cron: "17 * * * *"' not in workflow:
        fail("hourly publication observer is not activated")
    if "workflow_dispatch:" not in workflow:
        fail("explicit publication dispatch trigger missing")

    handoff = HANDOFF_PATH.read_text(encoding="utf-8")
    for required in (
        "LLMA-PUBLICATION-ACTIVATION-013",
        "PR #56",
        "PR #95",
        'cron: "17 * * * *"',
    ):
        if required not in handoff:
            fail(f"publication handoff missing {required}")

    print("LLM_ADAPTER_ORCHESTRATION_STATE_PASS")
    print(f"active_tasks={len(active)} completed_tasks={len(completed)} queued_exclusive={len(queued)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
