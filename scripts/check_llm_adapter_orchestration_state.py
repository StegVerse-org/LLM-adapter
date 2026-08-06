#!/usr/bin/env python3
"""Fail closed when LLM-adapter ownership, evidence, or released claim state drifts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "llm-adapter-orchestration-state.json"
OPEN_PR_INVENTORY_PATH = ROOT / "data" / "llm-adapter-open-pr-consolidation.json"
OPEN_PR_TASK_PATH = ROOT / "tasks" / "LLMA-STALE-ACTIVATION-PR-RECONCILIATION-016.json"
OPEN_PR_RECEIPT_PATH = ROOT / "receipts" / "llm-adapter-open-pr-consolidation.json"
PUBLICATION_TASK_PATH = ROOT / "tasks" / "LLMA-PUBLICATION-ACTIVATION-013.json"
SEQUENCE_TASK_PATH = ROOT / "tasks" / "LLMA-SEQUENCE-0001-RELEASE-015.json"
PUBLICATION_RECEIPT_PATH = ROOT / "receipts" / "stegdeploy-image-publication.json"
PUBLICATION_READINESS_PATH = ROOT / "status" / "stegdeploy-image-publication-readiness.json"
SERVICE_GATEWAY_RECEIPT_PATH = ROOT / "receipts" / "service-gateway-activation-proof.json"
PROVIDER_ACTIVATION_RECEIPT_PATH = ROOT / "receipts" / "ecosystem-chat-authorized-provider-activation.latest.json"
MONITOR_PATH = ROOT / "reports" / "ecosystem-chat-live-activation-monitor.json"
REPOSITORY_HANDOFF_PATH = ROOT / "docs" / "LLM_ADAPTER_MIRROR_HANDOFF.md"
OPEN_PR_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "llm-adapter-open-pr-consolidation.yml"
OPEN_PR_VALIDATOR_PATH = ROOT / "scripts" / "check_llm_adapter_open_pr_consolidation.py"

EXPECTED_DIGEST = "sha256:ae309681c4b1411c39860bcb349acc5cf727b70f8876a9e61fccfbb9e767a901"
EXPECTED_PUBLICATION_RECEIPT = "d70f19a0a3afd9a34f313b3e0a4959e3343b00194c86fd85e3cdec5b3c0a7d87"
EXPECTED_PUBLICATION_RUN = 30967973138
EXPECTED_HIL_RUN = 30966031698
EXPECTED_PROVIDER_RUN = 30966031661
EXPECTED_SERVICE_GATEWAY_RUN = 30967405348
EXPECTED_OPEN_PR_TASK = "LLMA-STALE-ACTIVATION-PR-RECONCILIATION-016"
EXPECTED_OPEN_PR_RUN = 31071026576
EXPECTED_OPEN_PR_ARTIFACT = 8955632464
EXPECTED_OPEN_PR_ARTIFACT_DIGEST = "sha256:ee62f843e7845d7b73979dbae2e7e799610375100639c08f56b13c579f9fffa0"
EXPECTED_OPEN_PR_RECEIPT = "07f7f2495d7d9b60a1593edd48c89b31ca516b865e0d153823a7224216255a26"
EXPECTED_OPEN_PR_MERGE = "a3f01b799173f65eff8b34d2e786372399ecc780"


def fail(message: str) -> None:
    raise SystemExit(f"LLM_ADAPTER_ORCHESTRATION_STATE_FAIL: {message}")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON at {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected object at {path.relative_to(ROOT)}")
    return value


def record(items: list[dict[str, Any]], identifier: str, key: str = "task_id") -> dict[str, Any]:
    matches = [item for item in items if item.get(key) == identifier]
    if len(matches) != 1:
        fail(f"expected exactly one {identifier}; found {len(matches)}")
    return matches[0]


def assert_false_authority(value: dict[str, Any], label: str) -> None:
    if not value or any(flag is not False for flag in value.values()):
        fail(f"{label} grants authority")


def verify_hash_bound_receipt(receipt: dict[str, Any], field: str = "receipt_sha256") -> None:
    material = dict(receipt)
    declared = material.pop(field, None)
    if not isinstance(declared, str) or not declared:
        fail(f"receipt missing {field}")
    actual = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if declared != actual:
        fail(f"invalid {field}")


def main() -> int:
    state = load_json(STATE_PATH)
    inventory = load_json(OPEN_PR_INVENTORY_PATH)
    open_pr_task = load_json(OPEN_PR_TASK_PATH)
    open_pr_receipt = load_json(OPEN_PR_RECEIPT_PATH)
    publication_task = load_json(PUBLICATION_TASK_PATH)
    sequence_task = load_json(SEQUENCE_TASK_PATH)
    publication_receipt = load_json(PUBLICATION_RECEIPT_PATH)
    readiness = load_json(PUBLICATION_READINESS_PATH)
    service_gateway = load_json(SERVICE_GATEWAY_RECEIPT_PATH)
    provider_activation = load_json(PROVIDER_ACTIVATION_RECEIPT_PATH)
    monitor = load_json(MONITOR_PATH)

    if state.get("schema_version") != "1.1.0" or state.get("repository") != "StegVerse-org/LLM-adapter":
        fail("orchestration identity mismatch")
    if state.get("status") != "ACTIVE_WITH_DECLARED_BLOCKERS":
        fail("repository blocker posture changed")
    if state.get("task_sequence") != 3:
        fail("unexpected task sequence")
    if state.get("task_sequence_label") != "current work task sequence 0003 complete":
        fail("task sequence label mismatch")
    if state.get("idle_terminal_statement") != "end of current work task sequence 0003, no tasks running":
        fail("sequence idle statement mismatch")
    if state.get("active_tasks") != []:
        fail("released sequence retains an active task claim")
    assert_false_authority(state.get("authority") or {}, "orchestration")

    consolidation = state.get("session_consolidation") or {}
    if consolidation.get("state") != "COMPLETE" or consolidation.get("archive_ready") is not True:
        fail("released session consolidation is not complete and archive-ready")
    if set(consolidation.get("canonical_continuation") or []) != {
        "StegVerse-org/LLM-adapter#18",
        "StegVerse-org/LLM-adapter#72",
        "StegVerse-Labs/TVC#6",
    }:
        fail("canonical continuation set mismatch")

    completed = state.get("completed_tasks") or []
    publication = record(completed, "LLMA-0001-IMAGE-PUBLICATION")
    if publication.get("state") != "COMPLETE" or publication.get("publication_run") != EXPECTED_PUBLICATION_RUN:
        fail("image publication evidence drifted")
    if publication.get("image_digest") != EXPECTED_DIGEST:
        fail("publication digest mismatch")
    if publication.get("publication_receipt_sha256") != EXPECTED_PUBLICATION_RECEIPT:
        fail("publication receipt mismatch")
    if publication.get("consumer_pull_verified") is not True or publication.get("readiness_state") != "READY":
        fail("publication consumer verification or readiness regressed")

    hil = record(completed, "LLMA-0001-HIL-CYCLE")
    if hil.get("state") != "COMPLETE" or hil.get("workflow_run") != EXPECTED_HIL_RUN:
        fail("HIL full-cycle evidence mismatch")
    if hil.get("persistent_deployment_proven") is not False:
        fail("HIL CI proof is misclassified as persistent deployment")

    provider_validation = record(completed, "LLMA-0001-GOAL8")
    if provider_validation.get("state") != "COMPLETE" or provider_validation.get("workflow_run") != EXPECTED_PROVIDER_RUN:
        fail("provider validation evidence mismatch")
    if provider_validation.get("authority_effect") is not False:
        fail("provider validation grants authority")

    sequence = record(completed, "LLMA-SEQUENCE-0001-RELEASE-015")
    if sequence.get("state") != "COMPLETE" or sequence.get("service_gateway_run") != EXPECTED_SERVICE_GATEWAY_RUN:
        fail("completed Service Gateway sequence drifted")
    if sequence.get("persistent_deployment_proven") is not False:
        fail("Service Gateway CI proof is misclassified as persistent deployment")

    reconciliation = record(completed, EXPECTED_OPEN_PR_TASK)
    expected_reconciliation = {
        "state": "COMPLETE",
        "owner": "completed-task-record",
        "pull_request": 118,
        "merge_commit": EXPECTED_OPEN_PR_MERGE,
        "main_workflow_run": EXPECTED_OPEN_PR_RUN,
        "artifact_id": EXPECTED_OPEN_PR_ARTIFACT,
        "artifact_digest": EXPECTED_OPEN_PR_ARTIFACT_DIGEST,
        "source_receipt_sha256": EXPECTED_OPEN_PR_RECEIPT,
        "authority_effect": False,
    }
    for key, expected in expected_reconciliation.items():
        if reconciliation.get(key) != expected:
            fail(f"completed open-PR reconciliation {key} mismatch")
    if reconciliation.get("closed_superseded_prs") != [10, 13, 27, 60]:
        fail("closed superseded PR set mismatch")
    if reconciliation.get("superseded_draft_controlled_prs") != [23]:
        fail("draft-controlled PR set mismatch")
    if reconciliation.get("review_required_unclaimed_prs") != [63]:
        fail("review-required PR set mismatch")
    if reconciliation.get("preserved_distinct_unclaimed_prs") != [36, 58, 85]:
        fail("preserved distinct PR set mismatch")

    live = record(state.get("queued_exclusive_tasks") or [], "LLMA-0002-LIVE-PROVIDER")
    if live.get("owner") != "issue/18" or live.get("state") != "BLOCKED" or live.get("execution_class") != "EXCLUSIVE":
        fail("live-provider owner or state mismatch")
    if live.get("blocked_until") != "all authority-bound blockers are cleared":
        fail("live-provider release condition mismatch")
    required_blockers = {
        "authorized provider configuration and scoped execution grant",
        "persistent endpoint",
        "authenticated Master Records custody configuration",
    }
    if set(live.get("external_blockers") or []) != required_blockers:
        fail("live-provider blocker set mismatch")

    if inventory.get("task_id") != EXPECTED_OPEN_PR_TASK or inventory.get("authority_effect") is not False:
        fail("open-PR consolidation inventory identity or authority mismatch")
    if open_pr_task.get("task_id") != EXPECTED_OPEN_PR_TASK:
        fail("open-PR task identity mismatch")
    if open_pr_task.get("state") != "COMPLETE" or open_pr_task.get("claimant") is not None:
        fail("open-PR task claim is not released")
    if open_pr_task.get("claim_release_condition") != "SATISFIED" or not open_pr_task.get("released_at"):
        fail("open-PR task release evidence missing")
    if (open_pr_task.get("validation") or {}).get("state") != "PASS":
        fail("open-PR task validation is not PASS")
    if open_pr_task.get("archive_dependency") != "SATISFIED; all unique reconciliation state and evidence are durably installed or transferred.":
        fail("open-PR task archive dependency is not satisfied")
    if open_pr_task.get("manual_user_action_required") is not False or open_pr_task.get("authority_effect") is not False:
        fail("open-PR task assigns manual work or authority")
    if not OPEN_PR_WORKFLOW_PATH.is_file() or not OPEN_PR_VALIDATOR_PATH.is_file():
        fail("open-PR automation path incomplete")

    if open_pr_receipt.get("schema") != "stegverse.llm_adapter.open_pr_consolidation_receipt.v1":
        fail("open-PR receipt schema mismatch")
    if open_pr_receipt.get("state") != "COMPLETE" or open_pr_receipt.get("task_id") != EXPECTED_OPEN_PR_TASK:
        fail("open-PR receipt state or identity mismatch")
    if open_pr_receipt.get("receipt_sha256") != EXPECTED_OPEN_PR_RECEIPT:
        fail("open-PR receipt hash value mismatch")
    verify_hash_bound_receipt(open_pr_receipt)
    workflow_evidence = open_pr_receipt.get("workflow_evidence") or {}
    for key, expected in {
        "pull_request": 118,
        "merge_commit": EXPECTED_OPEN_PR_MERGE,
        "main_run": EXPECTED_OPEN_PR_RUN,
        "artifact_id": EXPECTED_OPEN_PR_ARTIFACT,
        "artifact_digest": EXPECTED_OPEN_PR_ARTIFACT_DIGEST,
    }.items():
        if workflow_evidence.get(key) != expected:
            fail(f"open-PR receipt workflow evidence {key} mismatch")
    if open_pr_receipt.get("manual_user_action_required") is not False or open_pr_receipt.get("authority_effect") is not False:
        fail("open-PR receipt assigns manual work or authority")

    if publication_task.get("state") != "COMPLETE" or publication_task.get("claimant") is not None:
        fail("publication task claim is not released")
    if sequence_task.get("state") != "COMPLETE" or sequence_task.get("claimant") is not None:
        fail("prior sequence task claim is not released")

    if publication_receipt.get("schema") != "stegdeploy.image-publication.v2":
        fail("publication receipt schema mismatch")
    if publication_receipt.get("state") != "PUBLISHED" or publication_receipt.get("blockers") != []:
        fail("publication receipt is not zero-blocker PUBLISHED")
    if publication_receipt.get("digest") != EXPECTED_DIGEST:
        fail("publication receipt digest mismatch")
    if publication_receipt.get("receipt_sha256") != EXPECTED_PUBLICATION_RECEIPT:
        fail("publication receipt hash value mismatch")
    verify_hash_bound_receipt(publication_receipt)

    if readiness.get("state") != "READY" or readiness.get("blockers") != []:
        fail("publication readiness regressed")
    if readiness.get("observed_digest") != EXPECTED_DIGEST or readiness.get("consumer_pull_verified") is not True:
        fail("publication readiness evidence mismatch")
    assert_false_authority({
        "provider": readiness.get("provider_execution_authorized"),
        "deployment": readiness.get("persistent_deployment_authorized"),
        "custody": readiness.get("custody_authorized"),
        "site": readiness.get("site_activation_authorized"),
    }, "publication readiness")

    if service_gateway.get("schema") != "stegverse.service_gateway.activation_proof.v1":
        fail("Service Gateway proof schema mismatch")
    if service_gateway.get("result") != "PASS" or service_gateway.get("boundary") != "ephemeral GitHub-hosted activation proof; not persistent public hosting":
        fail("Service Gateway proof result or boundary mismatch")
    if (service_gateway.get("main_activation") or {}).get("workflow_run") != EXPECTED_SERVICE_GATEWAY_RUN:
        fail("Service Gateway main run mismatch")
    assert_false_authority(service_gateway.get("authority") or {}, "Service Gateway proof")

    if provider_activation.get("state") != "CONFIGURATION_REQUIRED":
        fail("provider activation unexpectedly changed without verified evidence")
    configuration = provider_activation.get("configuration") or {}
    if any(configuration.values()):
        fail("provider activation receipt reports partial binding without a new claim")
    if set(provider_activation.get("blockers") or []) != {
        "authorized_configuration_missing:STEGVERSE_MASTER_RECORDS_ENDPOINT",
        "authorized_configuration_missing:STEGVERSE_MASTER_RECORDS_TOKEN",
        "authorized_configuration_missing:STEGVERSE_PROVIDER_ENDPOINT",
        "authorized_configuration_missing:STEGVERSE_PROVIDER_MODEL",
        "authorized_configuration_missing:STEGVERSE_PROVIDER_TOKEN",
    }:
        fail("provider activation configuration blocker set mismatch")

    if monitor.get("semantic_state") != "PENDING":
        fail("live activation monitor unexpectedly changed")
    if monitor.get("semantic_blockers") != ["live_activation_observation_not_yet_recorded"]:
        fail("live activation monitor blocker mismatch")
    assert_false_authority(monitor.get("authority_boundary") or {}, "live activation monitor")

    handoff = REPOSITORY_HANDOFF_PATH.read_text(encoding="utf-8")
    for required in (
        "ARCHIVE THIS SESSION.",
        EXPECTED_OPEN_PR_TASK,
        "receipts/llm-adapter-open-pr-consolidation.json",
        "PR #63 is not declared complete or obsolete",
        "StegVerse-org/LLM-adapter#18",
    ):
        if required not in handoff:
            fail(f"canonical handoff missing {required}")

    print("LLM_ADAPTER_ORCHESTRATION_STATE_PASS")
    print("sequence=0003 active_tasks=0 session_archive_ready=true")
    print(f"completed_task={EXPECTED_OPEN_PR_TASK} live_provider_state={live['state']}")
    print(f"open_pr_run={EXPECTED_OPEN_PR_RUN} publication_run={EXPECTED_PUBLICATION_RUN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
