#!/usr/bin/env python3
"""Fail-closed validation for the session provider-layer consolidation record."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data" / "session-provider-layer-consolidation.json"

ALLOWED_CLAIMS = {
    "UNCLAIMED",
    "CLAIMED_FOR_IMPLEMENTATION",
    "CLAIMED_FOR_VALIDATION",
    "CLAIMED_FOR_INTEGRATION",
    "MACHINE_OWNED",
    "BLOCKED",
    "COMPLETE",
    "SUPERSEDED",
    "MERGED_INTO_CANONICAL_WORKSTREAM",
}

REQUIRED_TASKS = {
    "LLMA-PROVIDER-BOUNDARY",
    "LLMA-AUTHORIZED-RUNTIME",
    "LLMA-PROVIDER-AUTHORITY-GATE",
    "LLMA-PROCESS-RESTART",
    "LLMA-INTERNAL-REFERENCE",
    "LLMA-HIL-FULL-CYCLE",
    "LLMA-IMAGE-PUBLICATION",
    "LLMA-SITE-PROPAGATION",
}


def fail(message: str) -> None:
    raise SystemExit(f"SESSION_PROVIDER_LAYER_CONSOLIDATION_FAIL: {message}")


def main() -> int:
    value = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if value.get("schema") != "stegverse.session-consolidation.v1":
        fail("unexpected schema")
    if value.get("canonical_handoff") != "docs/LLM_ADAPTER_MIRROR_HANDOFF.md":
        fail("canonical handoff mismatch")

    claim = value.get("claim") or {}
    if claim.get("state") not in ALLOWED_CLAIMS:
        fail("invalid top-level claim state")
    if not claim.get("release_condition"):
        fail("claim release condition missing")
    if not claim.get("surfaces"):
        fail("claim surfaces missing")

    inventory = value.get("inventory") or []
    task_ids = {item.get("task_id") for item in inventory}
    missing = sorted(REQUIRED_TASKS - task_ids)
    if missing:
        fail(f"missing required tasks: {', '.join(missing)}")
    duplicates = sorted(task_id for task_id in task_ids if sum(1 for item in inventory if item.get("task_id") == task_id) > 1)
    if duplicates:
        fail(f"duplicate task ids: {', '.join(duplicates)}")

    required_fields = {
        "task_id",
        "originating_session_goal",
        "destination",
        "branch",
        "location",
        "owner",
        "claim_state",
        "completion_state",
        "validation_state",
        "integration_state",
        "archival_dependency",
        "evidence",
        "next_action",
    }
    for item in inventory:
        absent = sorted(required_fields - set(item))
        if absent:
            fail(f"{item.get('task_id', '<unknown>')} missing fields: {', '.join(absent)}")
        if item["claim_state"] not in ALLOWED_CLAIMS:
            fail(f"{item['task_id']} has invalid claim state")
        if not item["next_action"]:
            fail(f"{item['task_id']} has no executable next action")
        if not item["evidence"]:
            fail(f"{item['task_id']} has no evidence location")

    consolidation = value.get("session_consolidation") or {}
    total = consolidation.get("total_session_goals")
    transferred = consolidation.get("transferred_or_complete")
    if total != len(REQUIRED_TASKS):
        fail("session-goal denominator does not match required inventory")
    if not isinstance(transferred, int) or transferred < 0 or transferred > total:
        fail("invalid transferred-or-complete count")
    if consolidation.get("unique_chat_only_requirements_remaining") != 0:
        fail("chat-only requirements remain")
    if not consolidation.get("canonical_continuation"):
        fail("canonical continuation missing")
    if consolidation.get("archive_state") == "COMPLETE_ARCHIVE" and transferred != total:
        fail("archive state cannot be complete with untransferred goals")

    print("SESSION_PROVIDER_LAYER_CONSOLIDATION_PASS")
    print(f"tasks={len(inventory)} transferred_or_complete={transferred}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
