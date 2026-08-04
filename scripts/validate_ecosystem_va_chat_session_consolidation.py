#!/usr/bin/env python3
"""Fail closed unless the combined Chat session has a durable continuation path."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data" / "ecosystem-va-chat-session-consolidation.json"
RELEASE = ROOT / "data" / "ecosystem-va-chat-session-consolidation-release.json"
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
    "CHAT-LLM-PROFILES-001", "CHAT-LLM-SESSION-BINDING-001",
    "ECOSYSTEM-CHAT-PRODUCT-IDENTITY-001", "VA-CLAIMS-PRODUCT-IDENTITY-001",
    "ECOSYSTEM-LIVE-ACTIVATION-001", "ECOSYSTEM-PACKAGE-HOSTING-001",
    "VA-ROUTES-AND-GENERATORS-001", "VA-PRIVACY-RUNTIME-001",
    "VA-TVC-ADMISSION-001", "VA-AUTHORIZED-EXECUTION-001",
    "VA-MASTER-RECORDS-001", "VA-SITE-PROJECTION-001",
    "VA-DOCUMENT-PRIVACY-001", "VA-URGENT-SAFETY-001",
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


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def require_text(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        fail(f"text_required:{label}")


def validate_inventory(value: dict[str, Any]) -> list[dict[str, Any]]:
    if value.get("schema") != "stegverse.ecosystem_va_chat.session_consolidation.v1":
        fail("inventory_schema_invalid")
    if value.get("session_goal_groups") != 15:
        fail("goal_group_count_invalid")
    if value.get("session_requirements_transferred_or_complete") != 18:
        fail("transferred_requirement_count_invalid")
    if value.get("session_requirements_total") != 18:
        fail("requirement_total_invalid")
    if value.get("unowned_tasks") != 0 or value.get("manual_user_tasks") != 0:
        fail("historical_inventory_unowned_or_manual_tasks")
    if value.get("active_chat_owned_claims") != 1:
        fail("historical_claim_creation_count_invalid")
    continuation = value.get("canonical_continuation")
    if not isinstance(continuation, list) or len(continuation) < 10:
        fail("canonical_continuation_incomplete")
    if len(continuation) != len(set(continuation)):
        fail("canonical_continuation_duplicate")

    items = value.get("inventory")
    if not isinstance(items, list) or len(items) != 15:
        fail("inventory_item_count_invalid")
    observed: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict) or set(item) != REQUIRED_ITEM_FIELDS:
            fail(f"inventory_fields_invalid:{index}")
        task_id = item.get("task_id")
        require_text(task_id, f"item_{index}_task_id")
        if task_id in observed:
            fail(f"duplicate_task_id:{task_id}")
        observed.add(task_id)
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
    if observed != REQUIRED_TASK_IDS:
        fail("required_inventory_ids_mismatch")

    requirements = value.get("requirements_transferred")
    if not isinstance(requirements, list) or len(requirements) != 18 or len(set(requirements)) != 18:
        fail("transferred_requirements_invalid")
    assertions = value.get("archive_assertions")
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
    return items


def validate_release(value: dict[str, Any]) -> tuple[str, bool]:
    if value.get("schema") != "stegverse.ecosystem_va_chat.session_consolidation_release.v1":
        fail("release_schema_invalid")
    if value.get("base_inventory") != "data/ecosystem-va-chat-session-consolidation.json":
        fail("release_base_inventory_invalid")
    if value.get("base_inventory_blob_sha") != git_blob_sha(INVENTORY):
        fail("release_inventory_blob_binding_invalid")
    if value.get("active_chat_owned_claims") != 0:
        fail("active_chat_owned_claims_remain")
    if value.get("unowned_tasks") != 0 or value.get("manual_user_tasks") != 0:
        fail("release_unowned_or_manual_tasks")
    if value.get("session_requirements_transferred_or_complete") != 18 or value.get("session_requirements_total") != 18:
        fail("release_requirement_count_invalid")
    if "LLMA-ECOSYSTEM-VA-CHAT-CONSOLIDATION-011" not in (value.get("released_claims") or []):
        fail("consolidation_claim_not_released")
    if value.get("blocked_unclaimed") != ["VACP-ADAPTER-AUTHORIZED-EXECUTION-005"]:
        fail("blocked_unclaimed_inventory_invalid")
    assertions = value.get("archive_assertions") or {}
    for field in (
        "no_unique_requirement_remains_only_in_chat",
        "no_active_chat_owned_claim_remains",
        "no_unowned_or_manual_task_remains",
        "all_incomplete_project_work_has_named_durable_owners",
    ):
        if assertions.get(field) is not True:
            fail(f"release_assertion_false:{field}")
    for field in (
        "release_projection_grants_execution_authority",
        "release_projection_grants_provider_authority",
        "release_projection_grants_custody",
        "release_projection_grants_filing_authority",
        "release_projection_grants_publication_authority",
        "release_projection_grants_activation_authority",
    ):
        if assertions.get(field) is not False:
            fail(f"release_authority_boundary_invalid:{field}")

    posture = value.get("posture")
    integration = value.get("mainline_integration") or {}
    if posture == "ARCHIVE_READY_PENDING_MERGE_AND_FINAL_HOSTED_VALIDATION":
        if integration.get("merged") is not False or integration.get("merge_commit") is not None:
            fail("pending_merge_projection_invalid")
        return "PASS_PENDING_MERGE", False
    if posture == "ARCHIVE_READY":
        if integration.get("merged") is not True:
            fail("archive_ready_without_merge")
        require_text(integration.get("merge_commit"), "release_merge_commit")
        return "PASS", True
    fail("release_posture_invalid")
    raise AssertionError("unreachable")


def main() -> int:
    inventory = load(INVENTORY)
    items = validate_inventory(inventory)
    release = load(RELEASE)
    result_state, archive_safe = validate_release(release)

    profile_receipt = load(PROFILE_RECEIPT)
    if profile_receipt.get("state") != "PASS" or profile_receipt.get("receipt_sha256") != "85a98e57b3a8e50fa13de3d24e2fcd39aaff99ea7071f3318719519f78275287":
        fail("profile_receipt_invalid")
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
    if session_receipt.get("state") != "PASS" or session_receipt.get("receipt_sha256") != "b1f9f56e8dc087ee04c49a011d351855a762030e2886d484def025a29e2e09b0":
        fail("session_binding_receipt_invalid")
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
    release_condition = provider_task.get("machine_observable_release_condition") or {}
    if release_condition.get("required_privacy_receipt_hash") != "bcd39b3689ba0fbe7f18b99e114984543d784c80d3fd8ad5842cc551926df34c":
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
    if any(ecosystem.get(field) is not False for field in (
        "provider_output_is_authority", "publication_authorized", "repository_mutation_authorized"
    )):
        fail("ecosystem_authority_projection_invalid")
    if ecosystem.get("runtime_path") != [
        "governed_provider_response", "provider_usage_persistence",
        "provider_usage_custody", "transition_custody", "transition_reconstruction",
    ]:
        fail("ecosystem_runtime_path_changed")

    consolidation_task = load(CONSOLIDATION_TASK)
    if consolidation_task.get("state") != "RELEASED_COMPLETE" or consolidation_task.get("claimant") is not None:
        fail("consolidation_task_not_released")
    completion = consolidation_task.get("completion_evidence") or {}
    if completion.get("active_chat_owned_runtime_claims") != 0:
        fail("task_active_claims_remain")
    if completion.get("unowned_tasks") != 0 or completion.get("manual_user_tasks") != 0:
        fail("task_unowned_or_manual_work")

    receipt: dict[str, Any] = {
        "schema": "stegverse.ecosystem_va_chat.session_consolidation_validation.v1",
        "state": result_state,
        "posture": "ARCHIVE_READY" if archive_safe else "PENDING_MAINLINE_MERGE",
        "inventory_task_count": len(items),
        "session_requirements_transferred_or_complete": 18,
        "session_requirements_total": 18,
        "active_chat_owned_claims": 0,
        "unowned_tasks": 0,
        "manual_user_tasks": 0,
        "profile_receipt_sha256": profile_receipt["receipt_sha256"],
        "session_binding_receipt_sha256": session_receipt["receipt_sha256"],
        "ecosystem_runtime_state": ecosystem["state"],
        "ecosystem_result_sha256": ecosystem.get("result_sha256", ""),
        "va_provider_task_state": provider_task["state"],
        "va_provider_task_claimant": provider_task["claimant"],
        "consolidation_task_state": consolidation_task["state"],
        "mainline_merge_complete": (release.get("mainline_integration") or {}).get("merged"),
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
