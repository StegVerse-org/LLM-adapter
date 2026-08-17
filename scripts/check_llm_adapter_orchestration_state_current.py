#!/usr/bin/env python3
"""Validate current LLM-adapter orchestration after retiring the completed PR observer."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "LLMA-STALE-ACTIVATION-PR-RECONCILIATION-016"
HISTORICAL_WORKFLOW = ROOT / ".github/workflows/llm-adapter-open-pr-consolidation.yml"
HISTORICAL_VALIDATOR = ROOT / "scripts/check_llm_adapter_open_pr_consolidation.py"
INVENTORY = ROOT / "data/llm-adapter-open-pr-consolidation.json"
TASK = ROOT / "tasks/LLMA-STALE-ACTIVATION-PR-RECONCILIATION-016.json"
RECEIPT = ROOT / "receipts/llm-adapter-open-pr-consolidation.json"
HANDOFF = ROOT / "docs/LLM_ADAPTER_MIRROR_HANDOFF.md"
CANONICAL = ROOT / "docs/WORKFLOW_CONSOLIDATION_MIRROR_HANDOFF.md"


def fail(message: str) -> None:
    raise SystemExit(f"LLM_ADAPTER_CURRENT_ORCHESTRATION_FAIL:{message}")


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing:{path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"not_object:{path.relative_to(ROOT)}")
    return value


def verify_hash(value: dict[str, Any]) -> None:
    material = dict(value)
    declared = material.pop("receipt_sha256", None)
    actual = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if declared != actual:
        fail("historical_receipt_hash_mismatch")


def main() -> int:
    inventory = load(INVENTORY)
    task = load(TASK)
    receipt = load(RECEIPT)

    if inventory.get("task_id") != TASK_ID or inventory.get("authority_effect") is not False:
        fail("historical_inventory_identity_or_authority")
    if task.get("task_id") != TASK_ID or task.get("state") != "COMPLETE" or task.get("claimant") is not None:
        fail("historical_task_not_released_complete")
    if task.get("claim_release_condition") != "SATISFIED":
        fail("historical_task_release_condition")
    if not str(task.get("archive_dependency", "")).startswith("SATISFIED"):
        fail("historical_task_archive_dependency")
    if task.get("authority_effect") is not False:
        fail("historical_task_authority")

    if receipt.get("schema") != "stegverse.llm_adapter.open_pr_consolidation_receipt.v1":
        fail("historical_receipt_schema")
    if receipt.get("state") != "COMPLETE" or receipt.get("authority_effect") is not False:
        fail("historical_receipt_state_or_authority")
    verify_hash(receipt)
    observations = receipt.get("observations") or []
    if len(observations) != 9 or {row.get("number") for row in observations} != {10, 13, 23, 27, 36, 58, 60, 63, 85}:
        fail("historical_receipt_denominator")

    if HISTORICAL_WORKFLOW.exists():
        fail("completed_token_bearing_observer_still_present")
    if not HISTORICAL_VALIDATOR.is_file():
        fail("historical_validator_not_preserved")

    handoff = HANDOFF.read_text(encoding="utf-8")
    required_handoff = (
        "historical_bounded_task_state: COMPLETE",
        "historical_archive_dependency: SATISFIED",
        "github_token_coordination_authority: NONE",
        "Render production dependency: NONE",
        "StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md",
        "tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json",
        "New PR collisions or changes require a fresh bounded task/claim",
    )
    for marker in required_handoff:
        if marker not in handoff:
            fail(f"specialized_handoff_missing:{marker}")

    canonical = CANONICAL.read_text(encoding="utf-8")
    required_canonical = (
        "credential_authority: TV/TVC",
        "github_token_runtime_authority: NONE",
        "resident carrier owns continuity",
        "formal local model development: COMPLETE_RELEASED",
        "local runtime discovery/launch/inference/proof: COMPLETE_RELEASED",
    )
    for marker in required_canonical:
        if marker not in canonical:
            fail(f"canonical_handoff_missing:{marker}")

    print("LLM_ADAPTER_CURRENT_ORCHESTRATION_PASS")
    print("historical_task_016=COMPLETE observer_workflow=RETIRED github_token_coordination_authority=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
