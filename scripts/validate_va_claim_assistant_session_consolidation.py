#!/usr/bin/env python3
"""Fail closed unless the VA Claim Assistant session is durably archive-safe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data" / "va-claim-assistant-session-consolidation.json"
PRIVACY_RECEIPT = ROOT / "receipts" / "va-claim-assistant-privacy-runtime-validation.json"
PRIVACY_TASK = ROOT / "tasks" / "VACP-ADAPTER-PII-RUNTIME-006.json"
LEGACY_PROVIDER_TASK = ROOT / "tasks" / "VACP-ADAPTER-AUTHORIZED-EXECUTION-005.json"
SOVEREIGN_PROVIDER_TASK = ROOT / "tasks" / "VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json"
ARCHIVE_TASK = ROOT / "tasks" / "VACP-SESSION-CONSOLIDATION-007.json"
OUTPUT = ROOT / "receipts" / "va-claim-assistant-session-consolidation-validation.json"

REQUIRED_INVENTORY_FIELDS = {
    "task_id", "originating_session_goal", "destination_repository", "branch",
    "location", "owner", "claim_state", "completion_state", "validation_state",
    "integration_state", "archival_dependency", "evidence",
    "next_executable_action", "release_condition",
}
ALLOWED_CLAIM_STATES = {
    "COMPLETE", "COMPLETE_FOR_BASELINE", "RELEASED_COMPLETE", "BLOCKED",
    "MACHINE_OWNED", "MACHINE_OWNED_BLOCKED", "MERGED_INTO_CANONICAL_WORKSTREAM",
    "SUPERSEDED",
}
ALLOWED_SOVEREIGN_PROVIDER_STATES = {
    "MACHINE_OWNED_BLOCKED_ON_SOVEREIGN_ROUTE_ACTIVATION",
    "MACHINE_OWNED_READY_FOR_SOVEREIGN_OBSERVATION",
}


def fail(message: str) -> None:
    raise SystemExit(f"VA_SESSION_CONSOLIDATION_FAIL:{message}")


def canonical_hash(value: dict[str, Any]) -> str:
    material = {key: item for key, item in value.items() if key != "receipt_hash"}
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def require_nonempty(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field}_missing")


def main() -> int:
    value = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if value.get("schema") != "stegverse.va_claim_assistant.session_consolidation.v1":
        fail("schema_invalid")
    if value.get("posture") not in {"ARCHIVE_READY_PENDING_HOSTED_VALIDATION", "ARCHIVE_READY"}:
        fail("posture_invalid")
    if value.get("session_goal_groups") != 13:
        fail("goal_group_count_invalid")
    if value.get("session_requirements_transferred_or_complete") != value.get("session_requirements_total"):
        fail("session_requirements_not_fully_transferred")
    if value.get("active_chat_owned_claims") != 0 or value.get("unowned_tasks") != 0 or value.get("manual_user_tasks") != 0:
        fail("session_still_owns_work")
    if value.get("safe_to_archive_after_validation") is not True:
        fail("archive_safety_not_asserted")

    continuation = value.get("canonical_continuation")
    if not isinstance(continuation, list) or len(continuation) < 8 or len(set(continuation)) != len(continuation):
        fail("canonical_continuation_incomplete")

    inventory = value.get("inventory")
    if not isinstance(inventory, list) or len(inventory) != 13:
        fail("inventory_count_invalid")
    task_ids: set[str] = set()
    for index, item in enumerate(inventory):
        if not isinstance(item, dict) or set(item) != REQUIRED_INVENTORY_FIELDS:
            fail(f"inventory_fields_invalid:{index}")
        task_id = item.get("task_id")
        require_nonempty(task_id, f"inventory_{index}_task_id")
        if task_id in task_ids:
            fail(f"duplicate_task_id:{task_id}")
        task_ids.add(task_id)
        for field in REQUIRED_INVENTORY_FIELDS - {"archival_dependency"}:
            require_nonempty(item.get(field), f"{task_id}:{field}")
        if item.get("claim_state") not in ALLOWED_CLAIM_STATES:
            fail(f"claim_state_invalid:{task_id}")
        if item.get("archival_dependency") is not False:
            fail(f"chat_archive_dependency_remains:{task_id}")

    required_task_ids = {
        "VA-GUIDE-001", "VA-CHAT-001", "VA-DOCUMENT-WORKSPACE-001", "VA-FILING-001",
        "VA-FEDERAL-PLUS-001", "VA-PII-READINESS-001", "VACP-ADAPTER-PII-RUNTIME-006",
        "VA-TVC-CREDENTIAL-LINKAGE-001", "VA-MASTER-RECORDS-001",
        "VACP-ADAPTER-AUTHORIZED-EXECUTION-005", "VA-URGENT-SAFETY-001",
        "ECOSYSTEM-CHAT-ACTIVATION-001", "VA-DOWNSTREAM-PROPAGATION-001",
    }
    if task_ids != required_task_ids:
        fail("required_goal_inventory_mismatch")

    claims = value.get("session_claims") or {}
    if claims.get("active_chat_owned") != []:
        fail("session_claims_not_released")
    if set(claims.get("released") or []) != {
        "TVC-VA-EPHEMERAL-ADMISSION-003", "VACP-ADAPTER-EXECUTION-PREFLIGHT-004", "VACP-ADAPTER-PII-RUNTIME-006",
    }:
        fail("released_claim_inventory_invalid")
    # This is historical archive inventory. The listed blocked provider task has since
    # been superseded by the sovereign local-model continuation validated below.
    if claims.get("blocked_unclaimed") != ["VACP-ADAPTER-AUTHORIZED-EXECUTION-005"]:
        fail("historical_blocked_unclaimed_inventory_invalid")

    assertions = value.get("archive_assertions") or {}
    for field in {
        "every_goal_completed_superseded_or_transferred",
        "repository_mutations_verified_at_available_level",
        "no_unassigned_work",
        "no_conflicting_or_stale_chat_claims",
        "machine_owned_continuation_installed",
        "blocked_dependencies_have_release_conditions",
        "handoffs_sufficient_for_continuation",
        "unique_requirements_moved_from_chat",
        "canonical_continuation_recorded",
    }:
        if assertions.get(field) is not True:
            fail(f"archive_assertion_not_true:{field}")
    if assertions.get("deleting_chat_impairs_execution") is not False:
        fail("deleting_chat_still_impairs_execution")

    privacy_receipt = json.loads(PRIVACY_RECEIPT.read_text(encoding="utf-8"))
    if privacy_receipt.get("state") != "PASS":
        fail("privacy_runtime_receipt_not_pass")
    if privacy_receipt.get("receipt_hash") != "bcd39b3689ba0fbe7f18b99e114984543d784c80d3fd8ad5842cc551926df34c":
        fail("privacy_runtime_receipt_hash_changed")
    privacy_task = json.loads(PRIVACY_TASK.read_text(encoding="utf-8"))
    if privacy_task.get("state") != "RELEASED_COMPLETE":
        fail("privacy_task_claim_not_released")

    legacy = json.loads(LEGACY_PROVIDER_TASK.read_text(encoding="utf-8"))
    if legacy.get("state") != "SUPERSEDED" or legacy.get("claim_state") != "SUPERSEDED":
        fail("legacy_github_provider_route_not_superseded")
    if legacy.get("claimant") is not None:
        fail("legacy_provider_task_claimed")
    if legacy.get("superseded_by") != "tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json":
        fail("legacy_provider_supersession_target_invalid")

    sovereign = json.loads(SOVEREIGN_PROVIDER_TASK.read_text(encoding="utf-8"))
    if sovereign.get("claim_state") != "MACHINE_OWNED":
        fail("sovereign_provider_not_machine_owned")
    if sovereign.get("state") not in ALLOWED_SOVEREIGN_PROVIDER_STATES:
        fail("sovereign_provider_state_invalid")
    contract = sovereign.get("required_provider_contract") or {}
    expected = {
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "third_party_inference_required": False,
        "hosted_provider_fallback": "DISALLOWED",
        "model_output_authority": "NONE",
    }
    for key, expected_value in expected.items():
        if contract.get(key) != expected_value:
            fail(f"sovereign_provider_contract_invalid:{key}")
    gates = set(sovereign.get("preserved_vacc_gates") or [])
    if "privacy guarded dispatch before model input" not in gates or "Master Records custody" not in gates:
        fail("sovereign_provider_preserved_gates_incomplete")
    release_conditions = (
        sovereign.get("machine_observable_release_condition")
        or sovereign.get("remaining_activation_conditions")
        or []
    )
    if not isinstance(release_conditions, list) or len(release_conditions) < 8:
        fail("sovereign_provider_release_condition_missing")
    if sovereign.get("state") == "MACHINE_OWNED_READY_FOR_SOVEREIGN_OBSERVATION":
        owner = str(sovereign.get("execution_owner") or "")
        if "persistent VACC runtime" not in owner:
            fail("sovereign_provider_observation_owner_invalid")
    if sovereign.get("authority_effect") is not False or sovereign.get("activation_effect") is not False:
        fail("sovereign_provider_authority_boundary_invalid")

    archive_task = json.loads(ARCHIVE_TASK.read_text(encoding="utf-8"))
    if archive_task.get("state") != "RELEASED_COMPLETE":
        fail("consolidation_task_claim_not_released")
    completion = archive_task.get("completion_evidence") or {}
    if completion.get("archive_posture") != "ARCHIVE_READY":
        fail("consolidation_task_archive_posture_invalid")
    if completion.get("active_chat_owned_claims") != 0 or completion.get("unowned_tasks") != 0 or completion.get("manual_user_tasks") != 0:
        fail("consolidation_task_work_remains")
    if completion.get("deleting_chat_impairs_execution") is not False:
        fail("consolidation_task_chat_still_required")

    receipt: dict[str, Any] = {
        "schema": "stegverse.va_claim_assistant.session_consolidation_validation.v1",
        "state": "PASS",
        "posture": "ARCHIVE_READY",
        "inventory_task_count": len(inventory),
        "session_requirements_transferred_or_complete": value["session_requirements_transferred_or_complete"],
        "session_requirements_total": value["session_requirements_total"],
        "active_chat_owned_claims": value["active_chat_owned_claims"],
        "unowned_tasks": value["unowned_tasks"],
        "manual_user_tasks": value["manual_user_tasks"],
        "historical_blocked_unclaimed_tasks": claims["blocked_unclaimed"],
        "legacy_provider_task_state": legacy["state"],
        "sovereign_provider_task_state": sovereign["state"],
        "privacy_runtime_receipt_hash": privacy_receipt["receipt_hash"],
        "consolidation_task_state": archive_task["state"],
        "archive_safe": True,
        "deleting_chat_impairs_execution": False,
        "authority_effect": False,
        "activation_effect": False,
        "custody_claimed": False,
        "filing_authorized": False,
        "publication_authorized": False,
    }
    receipt["receipt_hash"] = canonical_hash(receipt)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"VA_SESSION_CONSOLIDATION_PASS:{receipt['receipt_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
