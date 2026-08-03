#!/usr/bin/env python3
"""Fail closed unless the provider-layer session archive disposition is complete and bounded."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "data" / "session-provider-layer-archive-disposition.json"
INVENTORY = ROOT / "data" / "session-provider-layer-consolidation.json"
EXPECTED_RUNS = {
    "Session Provider Layer Consolidation": 30742501242,
    "Architecture Guard": 30742501247,
    "Validate Provider-Owned Usage Event": 30742501260,
    "validate": 30742501240,
}


def fail(message: str) -> None:
    raise SystemExit(f"SESSION_PROVIDER_LAYER_ARCHIVE_DISPOSITION_FAIL: {message}")


def main() -> int:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))

    if receipt.get("schema") != "stegverse.session-archive-disposition.v1":
        fail("unexpected schema")
    if receipt.get("task_id") != inventory.get("session_goal_id"):
        fail("task id does not match durable inventory")
    if receipt.get("repository") != "StegVerse-org/LLM-adapter":
        fail("repository mismatch")
    if receipt.get("pull_request") != 95:
        fail("canonical pull request mismatch")
    if receipt.get("posture") != "ARCHIVABLE":
        fail("posture is not ARCHIVABLE")
    if receipt.get("active_task_ownership") is not False:
        fail("session still claims active task ownership")
    if receipt.get("unique_unmerged_state") is not False:
        fail("unique unmerged session state remains")
    if receipt.get("safe_to_archive") is not True:
        fail("archive gate is not admitted")
    if inventory.get("session_consolidation", {}).get("transferred_or_complete") != 8:
        fail("not all session goals are transferred")
    if inventory.get("session_consolidation", {}).get("unique_chat_only_requirements_remaining") != 0:
        fail("chat-only requirements remain")

    evidence = receipt.get("validation_evidence") or []
    observed = {item.get("workflow"): item for item in evidence}
    if set(observed) != set(EXPECTED_RUNS):
        fail("hosted workflow evidence set is incomplete")
    for name, run_id in EXPECTED_RUNS.items():
        item = observed[name]
        if item.get("run_id") != run_id or item.get("conclusion") != "success":
            fail(f"workflow evidence mismatch for {name}")

    runtime = receipt.get("retained_runtime_state") or {}
    if runtime.get("state") != "DESTINATION_ACTIVATION_PENDING_EXTERNAL_EVIDENCE":
        fail("runtime state is overstated or missing")
    for field in (
        "live_receipt_present",
        "live_receipt_verified",
        "deployment_authorized",
        "execution_authorized",
        "custody_claimed",
        "publication_authorized",
    ):
        if runtime.get(field) is not False:
            fail(f"runtime authority boundary changed: {field}")

    remaining = receipt.get("remaining_work") or []
    if len(remaining) < 4:
        fail("remaining work is not fully assigned")
    for item in remaining:
        if not item.get("task") or not item.get("owner") or not item.get("release_condition"):
            fail("remaining work lacks task, owner, or release condition")

    boundaries = receipt.get("authority_boundary") or {}
    if not boundaries or any(value is not False for value in boundaries.values()):
        fail("archive receipt grants authority")

    print("SESSION_PROVIDER_LAYER_ARCHIVE_DISPOSITION_PASS")
    print("posture=ARCHIVABLE successor=PR#95 goals=8/8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
