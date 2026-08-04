#!/usr/bin/env python3
"""Fail closed unless the Ecosystem/VA Chat session is durably transferable."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data" / "ecosystem-va-chat-session-consolidation.json"
PROFILE_RECEIPT = ROOT / "receipts" / "chat-llm-profiles-validation.json"
PROFILE_TASK = ROOT / "tasks" / "LLMA-CHAT-LLM-PROFILES-009.json"
SESSION_RECEIPT = ROOT / "receipts" / "chat-llm-session-binding-validation.json"
SESSION_TASK = ROOT / "tasks" / "LLMA-CHAT-SESSION-BINDING-010.json"
VA_PROVIDER_TASK = ROOT / "tasks" / "VACP-ADAPTER-AUTHORIZED-EXECUTION-005.json"
ECOSYSTEM_RECEIPT = ROOT / "receipts" / "ecosystem-chat-authorized-provider-activation.latest.json"
CONSOLIDATION_TASK = ROOT / "tasks" / "LLMA-ECOSYSTEM-VA-CHAT-CONSOLIDATION-011.json"
OUTPUT = ROOT / "receipts" / "ecosystem-va-chat-session-consolidation-validation.json"

REQUIRED_ITEM_FIELDS = {
    "task_id", "originating_session_goal", "destination_repository", "branch",
    "location", "owner", "claim_state", "completion_state", "validation_state",
    "integration_state", "archival_dependency", "evidence",
    "next_executable_action", "release_condition",
}

REQUIRED_TASK_IDS = {
    "CHAT-LLM-PROFILES-001",
    "CHAT-LLM-SESSION-BINDING-001",
    "ECOSYSTEM-CHAT-PRODUCT-IDENTITY-001",
    "VA-CLAIMS-PRODUCT-IDENTITY-001",
    "ECOSYSTEM-LIVE-ACTIVATION-001",
    "ECOSYSTEM-PACKAGE-HOSTING-001",
    "VA-ROUTES-AND-GENERATORS-001",
    "VA-PRIVACY-RUNTIME-001",
    "VA-TVC-ADMISSION-001",
    "VA-AUTHORIZED-EXECUTION-001",
    "VA-MASTER-RECORDS-001",
    "VA-SITE-PROJECTION-001",
    "VA-DOCUMENT-PRIVACY-001",
    "VA-URGENT-SAFETY-001",
    "VA-FILING-AND-DOWNSTREAM-001",
}

ALLOWED_CLAIM_STATES = {
    "COMPLETE", "RELEASED_COMPLETE", "MERGED_INTO_CANONICAL_WORKSTREAM",
    "MACHINE_OWNED", "MACHINE_OWNED_BLOCKED", "BLOCKED",
}


def fail(message: str) -> None:
    raise SystemExit(f"ECOSYSTEM_VA_CHAT_SESSION_CONSOLIDATION_FAIL:{message}")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"object_required:{path}")
    return value


def canonical_hash(value: dict[str, Any]) -> str:
    material = {key: item for key, item in value.items() if key != "receipt_hash"}
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def require_text(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        fail(f"text_required:{label}")


def main() -> int:
    inventory = load(INVENTORY)
    if inventory.get("schema") != "stegverse.ecosystem_va_chat.session_consolidation.v1":
        fail("inventory_schema_invalid")
    if inventory.get("session_goal_groups") != 15:
        fail("goal_group_count_invalid")
    if inventory.get("session_requirements_transferred_or_complete") != 18:
        fail("transferred_requirement_count_invalid")
    if inventory.get("session_requirements_total") != 18:
        fail("requirement_total_invalid")
    if inventory.get("unowned_tasks") != 0 or inventory.get("manual_user_tasks") != 0:
        fail("unowned_or_manual_tasks_remain")
    if inventory.get("safe_to_archive_after_validation_and_claim_release") is not True:
        fail("archive_safety_not_asserted")

    continuation = inventory.get("canonical_continuation")
    if not isinstance(continuation, list) or len(continuation) < 10:
        fail("canonical_continuation_incomplete")
    if len(continuation) != len(set(continuation)):
        fail("canonical_continuation_duplicate")

    items = inventory.get("inventory")
    if not isinstance(items, list) or len(items) != 15:
        fail("inventory_item_count_invalid")
    observed_ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict) or set(item) != REQUIRED_ITEM_FIELDS:
            fail(f"inventory_fields_invalid:{index}")
        task_id = item.get("task_id")
        require_text(task_id, f"item_{index}_task_id")
        if task_id in observed_ids:
            fail(f"duplicate_task_id:{task_id}")
        observed_ids.add(task_id)
        if item.get("claim_state") not in ALLOWED_CLAIM_STATES:
            fail(f"claim_state_invalid:{task_id}")
        if item.get("archival_dependency") is not False:
            fail(f"chat_dependency_remains:{task_id}")
        for field in REQUIRED_ITEM_FIELDS - {"archival_dependency"}:
            require_text(item.get(field), f"{task_id}:{field}")
        combined = " ".join(str(item.get(field, "")) for field in (
            "owner", "location", "next_executable_action", "release_condition"
        )).lower()
        for prohibited in ("unspecified external", "unknown owner", "tbd", "to be determined", "future manual"):
            if prohibited in combined:
                fail(f"vague_work_assignment:{task_id}:{prohibited}")
    if observed_ids != REQUIRED_TASK_IDS:
        fail("required_inventory_ids_mismatch")

    requirements = inventory.get("requirements_transferred")
    if not isinstance(requirements, list) or len(requirements) != 18 or len(set(requirements)) != 18:
        fail("transferred_requirements_invalid")

    assertions = inventory.get("archive_assertions")
    if not isinstance(assertions, dict):
        fail("archive_assertions_missing")
    for field in (
        "every_goal_completed_superseded_or_transferred",
        "repository_mutations_verified_at_available_level",
        "no_unassigned_work",
        "no_conflicting_or_stale_runtime_claims_created_by_this_session",
        "machine_owned_continuation_installed",
        "blocked_dependencies_have_release_conditions",
        "handoffs_sufficient_for_continuation",
        "unique_requirements_moved_from_chat",
        "canonical_continuation_recorded",
    ):
        if assertions.get(field) is not True:
            fail(f"archive_assertion_false:{field}")
    if assertions.get("deleting_chat_impairs_execution_after_validation_and_claim_release") is not False:
        fail("chat_still_required")
    for field in (
        "archive_disposition_is_execution_authority",
        "archive_disposition_is_provider_authority",
        "archive_disposition_is_custody",
        "archive_disposition_is_filing_authority",
        "archive_disposition_is_publication_authority",
        "archive_disposition_is_activation_authority",
    ):
        if assertions.get(field) is not False:
            fail(f"archive_authority_boundary_invalid:{field}")

    profile_receipt = load(PROFILE_RECEIPT)
    if profile_receipt.get("state") != "PASS":
        fail("profile_receipt_not_pass")
    if profile_receipt.get("receipt_sha256") != "85a98e57b3a8e50fa13de3d24e2fcd39aaff99ea7071f3318719519f78275287":
        fail("profile_receipt_hash_changed")
    profiles = profile_receipt.get("profiles") or {}
    if profiles.get("ecosystem-chat-llm", {}).get("feature_count") != 19:
        fail("ecosystem_feature_count_invalid")
    if profiles.get("va-claims-chat-llm", {}).get("feature_count") != 19:
        fail("claims_feature_count_invalid")
    if profiles.get("va-claims-chat-llm", {}).get("source_mode") != "OFFICIAL_VA_ONLY":
        fail("claims_source_mode_invalid")
    profile_task = load(PROFILE_TASK)
    if profile_task.get("state") != "RELEASED_COMPLETE" or profile_task.get("claimant") is not None:
        fail("profile_task_not_released")

    session_receipt = load(SESSION_RECEIPT)
    if session_receipt.get("state") != "PASS":
        fail("session_binding_receipt_not_pass")
    if session_receipt.get("receipt_sha256") != "b1f9f56e8dc087ee04c49a011d351855a762030e2886d484def025a29e2e09b0":
        fail("session_binding_receipt_hash_changed")
    if session_receipt.get("provider_call_performed") is not False:
        fail("session_binding_claims_provider_call")
    if session_receipt.get("claims_non_va_required_source", {}).get("provider_envelope_created") is not False:
        fail("claims_denied_source_created_envelope")
    session_task = load(SESSION_TASK)
    if session_task.get("state") != "RELEASED_COMPLETE" or session_task.get("claimant") is not None:
        fail("session_binding_task_not_released")

    provider_task = load(VA_PROVIDER_TASK)
    if provider_task.get("state") != "BLOCKED" or provider_task.get("claimant") is not None:
        fail("va_provider_task_not_blocked_unclaimed")
    release = provider_task.get("machine_observable_release_condition") or {}
    if release.get("required_privacy_receipt_hash") != "bcd39b3689ba0fbe7f18b99e114984543d784c80d3fd8ad5842cc551926df34c":
        fail("va_provider_privacy_dependency_changed")
    if not provider_task.get("current_blockers"):
        fail("va_provider_blockers_missing")

    ecosystem = load(ECOSYSTEM_RECEIPT)
    if ecosystem.get("schema") != "stegverse.ecosystem_chat.authorized_provider_activation.v1":
        fail("ecosystem_receipt_schema_invalid")
    if ecosystem.get("manual_user_action_required") is not False:
        fail("ecosystem_manual_user_action_assigned")
    if ecosystem.get("state") not in {"CONFIGURATION_REQUIRED", "READY", "COMPLETE", "VERIFIED"}:
        fail("ecosystem_state_invalid")
    if ecosystem.get("provider_output_is_authority") is not False:
        fail("ecosystem_provider_output_authority_invalid")
    if ecosystem.get("publication_authorized") is not False:
        fail("ecosystem_publication_authority_invalid")
    if ecosystem.get("repository_mutation_authorized") is not False:
        fail("ecosystem_repository_mutation_authority_invalid")
    expected_path = [
        "governed_provider_response", "provider_usage_persistence",
        "provider_usage_custody", "transition_custody", "transition_reconstruction",
    ]
    if ecosystem.get("runtime_path") != expected_path:
        fail("ecosystem_runtime_path_changed")

    consolidation_task = load(CONSOLIDATION_TASK)
    task_state = consolidation_task.get("state")
    claims = inventory.get("session_claims") or {}
    if task_state == "CLAIMED_FOR_IMPLEMENTATION":
        if inventory.get("posture") != "ARCHIVE_READY_PENDING_HOSTED_VALIDATION_AND_CLAIM_RELEASE":
            fail("pending_posture_invalid")
        if inventory.get("active_chat_owned_claims") != 1:
            fail("pending_active_claim_count_invalid")
        if claims.get("active_chat_owned") != ["LLMA-ECOSYSTEM-VA-CHAT-CONSOLIDATION-011"]:
            fail("pending_claim_inventory_invalid")
        result_state = "PASS_PENDING_CLAIM_RELEASE"
        archive_safe = False
    elif task_state == "RELEASED_COMPLETE":
        if inventory.get("posture") != "ARCHIVE_READY":
            fail("released_posture_invalid")
        if inventory.get("active_chat_owned_claims") != 0:
            fail("released_active_claims_remain")
        if claims.get("active_chat_owned") != []:
            fail("released_claim_inventory_invalid")
        if "LLMA-ECOSYSTEM-VA-CHAT-CONSOLIDATION-011" not in (claims.get("released") or []):
            fail("consolidation_claim_not_recorded_released")
        result_state = "PASS"
        archive_safe = True
    else:
        fail("consolidation_task_state_invalid")

    receipt: dict[str, Any] = {
        "schema": "stegverse.ecosystem_va_chat.session_consolidation_validation.v1",
        "state": result_state,
        "posture": "ARCHIVE_READY" if archive_safe else "PENDING_CLAIM_RELEASE",
        "inventory_task_count": len(items),
        "session_requirements_transferred_or_complete": 18,
        "session_requirements_total": 18,
        "active_chat_owned_claims": inventory.get("active_chat_owned_claims"),
        "unowned_tasks": 0,
        "manual_user_tasks": 0,
        "profile_receipt_sha256": profile_receipt["receipt_sha256"],
        "session_binding_receipt_sha256": session_receipt["receipt_sha256"],
        "ecosystem_runtime_state": ecosystem["state"],
        "ecosystem_result_sha256": ecosystem.get("result_sha256", ""),
        "va_provider_task_state": provider_task["state"],
        "va_provider_task_claimant": provider_task["claimant"],
        "archive_safe": archive_safe,
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
    print(f"ECOSYSTEM_VA_CHAT_SESSION_CONSOLIDATION_{result_state}:{receipt['receipt_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
