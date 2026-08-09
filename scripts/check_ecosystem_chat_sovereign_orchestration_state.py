#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/ecosystem-chat-sovereign-orchestration-state.json"
TASK = ROOT / "tasks/LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019.json"
LOCAL_TASK = ROOT / "tasks/LLMA-LOCAL-RUNTIME-MODEL-017.json"
LOCAL_RECEIPT = ROOT / "receipts/local-runtime-model-proof.latest.json"


def fail(message: str) -> None:
    raise SystemExit(f"ECOSYSTEM_CHAT_SOVEREIGN_ORCHESTRATION_FAIL: {message}")


def load(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        fail(f"not object: {path.relative_to(ROOT)}")
    return value


def main() -> int:
    state = load(STATE)
    task = load(TASK)
    local_task = load(LOCAL_TASK)
    local_receipt = load(LOCAL_RECEIPT)

    if state.get("schema_version") != "1.0.0" or state.get("state_type") != "ecosystem_chat_sovereign_orchestration_state":
        fail("state identity mismatch")
    if state.get("repository") != "StegVerse-org/LLM-adapter" or state.get("goal_id") != "ECOSYSTEM-CHAT-SOVEREIGN-ACTIVATION":
        fail("repository or goal mismatch")

    active = state.get("active_task") or {}
    if active.get("task_id") != "LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019" or active.get("state") != "CLAIMED_FOR_VALIDATION":
        fail("active binding claim mismatch")
    if task.get("state") != "CLAIMED_FOR_VALIDATION" or task.get("canonical_issue") != 18:
        fail("durable task claim mismatch")

    local = state.get("completed_local_runtime") or {}
    if local.get("task_id") != "LLMA-LOCAL-RUNTIME-MODEL-017" or local.get("state") != "RELEASED_COMPLETE":
        fail("local runtime completion mismatch")
    if local_task.get("state") != "RELEASED_COMPLETE" or local_task.get("evidence", {}).get("workflow_run") != 31341784892:
        fail("released local runtime claim drift")
    if local_receipt.get("state") != "COMPLETE" or local_receipt.get("schema_version") != "stegverse.local-runtime-model-proof.v1":
        fail("released local runtime receipt drift")
    if local_receipt.get("real_local_inference_observed") is not True or local_receipt.get("external_provider_used") is not False:
        fail("local runtime proof lost sovereign predicates")

    superseded = set(state.get("superseded_production_blockers") or [])
    for prohibited in ("GitHub Models approval", "Render availability", "Cloudflare availability"):
        if prohibited not in superseded:
            fail(f"missing supersession: {prohibited}")

    blocker = state.get("current_product_blocker") or {}
    if blocker.get("class") != "SOVEREIGN_PRODUCTION_LLM_AND_SAME_EXECUTION_RECONSTRUCTION_NOT_YET_OBSERVED":
        fail("current product blocker mismatch")
    conditions = set(blocker.get("release_conditions") or [])
    required = {
        "production-scale sovereign local model process observed on StegVerse-owned/federated carrier",
        "private provider execution traverses E1 -> model worker -> E2",
        "provider/model usage is MEASURED in that execution",
        "provider-usage Master Records reconstruction PASS",
        "transition Master Records reconstruction PASS for the same execution",
        "immutable zero-blocker ecosystem-chat-live-activation.verified.json exists",
    }
    if conditions != required:
        fail("release condition set mismatch")

    observer = state.get("machine_owned_observer") or {}
    if observer.get("task_id") != "SHWP-ECOSYSTEM-CHAT-INFERENCE-001" or observer.get("owner") != "StegVerse-Labs/.github#60":
        fail("heartbeat observer owner mismatch")
    if observer.get("state") != "ACTIVE_BLOCKED_RECHECKING":
        fail("heartbeat observer state mismatch")

    owners = state.get("authority_owners") or {}
    expected = {
        "production_model_runtime": "StegVerse-002/micro-node-runtime#16/#22",
        "local_provider_transport_and_usage": "StegVerse-org/LLM-adapter#18",
        "inference_observation_recheck": "StegVerse-Labs/.github#60",
        "heartbeat_authority": "StegVerse-Labs/.github#12",
        "custody_and_reconstruction": "master-records/orchestration",
        "site_activation": "StegVerse-Labs/Site",
    }
    for key, value in expected.items():
        if owners.get(key) != value:
            fail(f"owner mismatch: {key}")

    invariants = state.get("invariants") or {}
    if invariants.get("reference_model_is_not_production_scale") is not True:
        fail("reference model production boundary lost")
    if invariants.get("missing_custody_or_reconstruction_is_not_success") is not True:
        fail("custody fail-closed invariant lost")
    for key in ("provider_output_grants_authority", "runtime_proof_grants_authority", "session_archive_grants_activation"):
        if invariants.get(key) is not False:
            fail(f"authority escalation: {key}")

    consolidation = state.get("session_consolidation") or {}
    if consolidation.get("archive_ready") is not False or consolidation.get("state") != "IN_PROGRESS_UNTIL_019_RELEASE":
        fail("session consolidation incorrectly marked complete")

    print("ECOSYSTEM_CHAT_SOVEREIGN_ORCHESTRATION_PASS")
    print("active=LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019 observer=SHWP-ECOSYSTEM-CHAT-INFERENCE-001")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
