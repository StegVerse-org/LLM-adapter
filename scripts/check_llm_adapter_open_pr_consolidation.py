#!/usr/bin/env python3
"""Validate the LLM-adapter open-PR consolidation inventory and live snapshots."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "data" / "llm-adapter-open-pr-consolidation.json"
ALLOWED_CLASSIFICATIONS = {
    "SUPERSEDED",
    "SUPERSEDED_DRAFT_CONTROLLED",
    "REVIEW_REQUIRED",
    "PRESERVED_DISTINCT_UNCLAIMED",
}
EXPECTED_NUMBERS = {10, 13, 23, 27, 36, 58, 60, 63, 85}


def fail(message: str) -> None:
    raise SystemExit(f"LLM_ADAPTER_OPEN_PR_CONSOLIDATION_FAIL: {message}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON at {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected object at {path}")
    return value


def canonical_sha256(value: dict[str, Any]) -> str:
    material = dict(value)
    material.pop("receipt_sha256", None)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_inventory(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    if inventory.get("schema") != "stegverse.llm_adapter.open_pr_consolidation.v1":
        fail("schema mismatch")
    if inventory.get("task_id") != "LLMA-STALE-ACTIVATION-PR-RECONCILIATION-016":
        fail("task ID mismatch")
    if inventory.get("repository") != "StegVerse-org/LLM-adapter":
        fail("repository mismatch")
    if inventory.get("canonical_issue") != "StegVerse-org/LLM-adapter#18":
        fail("canonical issue mismatch")
    if inventory.get("manual_user_action_required") is not False:
        fail("inventory assigns manual user action")
    if inventory.get("authority_effect") is not False:
        fail("inventory grants authority")

    policy = inventory.get("policy")
    if not isinstance(policy, dict):
        fail("policy missing")
    for field in (
        "one_active_owner_per_capability",
        "completed_or_superseded_branches_must_not_remain_mergeable_execution_lanes",
        "review_required_is_not_complete",
        "draft_supersession_is_fail_closed_when_close_control_is_unavailable",
    ):
        if policy.get(field) is not True:
            fail(f"policy not enabled: {field}")
    if policy.get("authority_effect") is not False:
        fail("policy grants authority")

    records = inventory.get("pull_requests")
    if not isinstance(records, list):
        fail("pull_requests must be a list")
    numbers = [record.get("number") for record in records if isinstance(record, dict)]
    if len(records) != len(numbers) or len(numbers) != len(set(numbers)):
        fail("pull request records are invalid or duplicated")
    if set(numbers) != EXPECTED_NUMBERS:
        fail(f"pull request denominator drift: {sorted(numbers)}")

    by_number = {record["number"]: record for record in records}
    expected_classes = {
        10: "SUPERSEDED",
        13: "SUPERSEDED",
        23: "SUPERSEDED_DRAFT_CONTROLLED",
        27: "SUPERSEDED",
        36: "PRESERVED_DISTINCT_UNCLAIMED",
        58: "PRESERVED_DISTINCT_UNCLAIMED",
        60: "SUPERSEDED",
        63: "REVIEW_REQUIRED",
        85: "PRESERVED_DISTINCT_UNCLAIMED",
    }
    for number, classification in expected_classes.items():
        record = by_number[number]
        if record.get("classification") != classification:
            fail(f"PR #{number} classification mismatch")
        if classification not in ALLOWED_CLASSIFICATIONS:
            fail(f"PR #{number} has unsupported classification")
        if not isinstance(record.get("next_action"), str) or not record["next_action"].strip():
            fail(f"PR #{number} next action missing")
        if record.get("expected_merged") is not False:
            fail(f"PR #{number} unexpectedly permits merged state")

    for number in (10, 13, 27, 60):
        if by_number[number].get("expected_github_state") != "closed":
            fail(f"PR #{number} is not required closed")
    if by_number[23].get("expected_github_state") != "open" or by_number[23].get("expected_draft") is not True:
        fail("PR #23 is not fail-closed as an open draft")
    if by_number[23].get("close_control_state") != "BLOCKED_BY_PLATFORM_SAFETY_LAYER":
        fail("PR #23 close-control blocker not recorded")
    for number in (36, 58, 63, 85):
        if by_number[number].get("expected_github_state") != "open":
            fail(f"PR #{number} expected open state missing")
        if by_number[number].get("active_claim") is not False:
            fail(f"PR #{number} is incorrectly actively claimed")

    mutations = inventory.get("completed_mutations") or {}
    if mutations.get("closed_superseded_prs") != [10, 13, 27, 60]:
        fail("closed PR mutation set mismatch")
    if mutations.get("draft_controlled_prs") != [23]:
        fail("draft-controlled PR mutation set mismatch")
    if mutations.get("review_required_prs") != [63]:
        fail("review-required PR set mismatch")
    if mutations.get("preserved_distinct_prs") != [36, 58, 85]:
        fail("preserved-distinct PR set mismatch")

    blockers = inventory.get("remaining_full_goal_blockers")
    if blockers != [
        "authorized provider configuration and scoped execution grant",
        "authorized persistent endpoint/runtime",
        "authenticated Master Records custody configuration",
    ]:
        fail("full-goal blocker set drifted")
    return records


def load_snapshots(directory: Path) -> dict[int, dict[str, Any]]:
    snapshots: dict[int, dict[str, Any]] = {}
    for path in directory.glob("*.json"):
        payload = load_json(path)
        number = payload.get("number")
        if not isinstance(number, int):
            fail(f"snapshot lacks integer number: {path}")
        snapshots[number] = payload
    return snapshots


def validate_snapshots(records: list[dict[str, Any]], snapshots: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    if set(snapshots) != EXPECTED_NUMBERS:
        fail(f"snapshot denominator drift: {sorted(snapshots)}")
    observations: list[dict[str, Any]] = []
    for record in records:
        number = record["number"]
        snapshot = snapshots[number]
        state = snapshot.get("state")
        draft = snapshot.get("draft") is True
        merged = snapshot.get("merged_at") is not None or snapshot.get("merged") is True
        if state != record.get("expected_github_state"):
            fail(f"PR #{number} state mismatch: {state}")
        if merged is not record.get("expected_merged"):
            fail(f"PR #{number} merged-state mismatch")
        if "expected_draft" in record and draft is not record["expected_draft"]:
            fail(f"PR #{number} draft-state mismatch")
        observations.append({
            "number": number,
            "state": state,
            "draft": draft,
            "merged": merged,
            "head_sha": (snapshot.get("head") or {}).get("sha"),
            "classification": record["classification"],
        })
    return observations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshots", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    inventory = load_json(INVENTORY_PATH)
    records = validate_inventory(inventory)
    observations: list[dict[str, Any]] = []
    if args.snapshots:
        observations = validate_snapshots(records, load_snapshots(args.snapshots))

    receipt = {
        "schema": "stegverse.llm_adapter.open_pr_consolidation_receipt.v1",
        "task_id": inventory["task_id"],
        "repository": inventory["repository"],
        "state": "COMPLETE" if observations else "INVENTORY_VALID",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "inventory_sha256": hashlib.sha256(
            json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "observations": observations,
        "closed_superseded_count": 4,
        "draft_controlled_count": 1,
        "review_required_count": 1,
        "preserved_distinct_count": 3,
        "remaining_full_goal_owner": inventory["remaining_full_goal_owner"],
        "remaining_full_goal_blockers": inventory["remaining_full_goal_blockers"],
        "manual_user_action_required": False,
        "authority_effect": False,
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("LLM_ADAPTER_OPEN_PR_CONSOLIDATION_PASS")
    print(f"state={receipt['state']} receipt_sha256={receipt['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
