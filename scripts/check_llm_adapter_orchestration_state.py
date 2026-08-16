#!/usr/bin/env python3
"""Fail closed when LLM-adapter ownership, evidence, or released claim state drifts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/llm-adapter-orchestration-state.json"
INVENTORY = ROOT / "data/llm-adapter-open-pr-consolidation.json"
TASK = ROOT / "tasks/LLMA-STALE-ACTIVATION-PR-RECONCILIATION-016.json"
RECEIPT = ROOT / "receipts/llm-adapter-open-pr-consolidation.json"
PUBLICATION = ROOT / "receipts/stegdeploy-image-publication.json"
READINESS = ROOT / "status/stegdeploy-image-publication-readiness.json"
SERVICE_GATEWAY = ROOT / "receipts/service-gateway-activation-proof.json"
PROVIDER_ACTIVATION = ROOT / "receipts/ecosystem-chat-authorized-provider-activation.latest.json"
MONITOR = ROOT / "reports/ecosystem-chat-live-activation-monitor.json"
HANDOFF = ROOT / "docs/LLM_ADAPTER_MIRROR_HANDOFF.md"
WORKFLOW = ROOT / ".github/workflows/llm-adapter-open-pr-consolidation.yml"
VALIDATOR = ROOT / "scripts/check_llm_adapter_open_pr_consolidation.py"

TASK_ID = "LLMA-STALE-ACTIVATION-PR-RECONCILIATION-016"
MERGE = "a3f01b799173f65eff8b34d2e786372399ecc780"
RUN = 31071026576
ARTIFACT = 8955632464
ARTIFACT_DIGEST = "sha256:ee62f843e7845d7b73979dbae2e7e799610375100639c08f56b13c579f9fffa0"
SOURCE_RECEIPT = "07f7f2495d7d9b60a1593edd48c89b31ca516b865e0d153823a7224216255a26"
COMMITTED_RECEIPT = "a04c192cbc89933d02dcb51517fbb56de88c0ab4bb4384df296519516f1dddf2"
# Publication is a mutable evidence projection: the latest committed, self-hashed
# v2 receipt and READY projection supersede the older Aug-4 digest snapshot.
IMAGE_DIGEST = "sha256:a599fc154f4bde14ab9adc140feb1285b43af3da4ea9214804b007fb9ff38f19"
IMAGE_RECEIPT = "67feb640e7be9489ca52438c9c7c609eeeae90c8e1e5409ea5c8fac6a38ef122"
BLOCKERS = {"authorized provider configuration and scoped execution grant", "persistent endpoint", "authenticated Master Records custody configuration"}


def fail(message: str) -> None:
    raise SystemExit(f"LLM_ADAPTER_ORCHESTRATION_STATE_FAIL: {message}")


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON at {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected object at {path.relative_to(ROOT)}")
    return value


def one(items: list[dict[str, Any]], value: str, key: str = "task_id") -> dict[str, Any]:
    matches = [item for item in items if item.get(key) == value]
    if len(matches) != 1:
        fail(f"expected exactly one {value}; found {len(matches)}")
    return matches[0]


def verify_hash(receipt: dict[str, Any]) -> None:
    material = dict(receipt)
    declared = material.pop("receipt_sha256", None)
    actual = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if declared != actual:
        fail(f"receipt hash mismatch: {declared} != {actual}")


def false_authority(value: dict[str, Any], label: str) -> None:
    if not value or any(flag is not False for flag in value.values()):
        fail(f"{label} grants authority")


def main() -> int:
    state = load(STATE)
    inventory = load(INVENTORY)
    task = load(TASK)
    receipt = load(RECEIPT)
    publication = load(PUBLICATION)
    readiness = load(READINESS)
    service_gateway = load(SERVICE_GATEWAY)
    provider_activation = load(PROVIDER_ACTIVATION)
    monitor = load(MONITOR)

    if state.get("schema_version") != "1.1.0" or state.get("repository") != "StegVerse-org/LLM-adapter":
        fail("orchestration identity mismatch")
    if state.get("task_sequence") != 3 or state.get("task_sequence_label") != "current work task sequence 0003 complete":
        fail("sequence 0003 is not complete")
    if state.get("active_tasks") != []:
        fail("released sequence retains active claims")
    if state.get("idle_terminal_statement") != "end of current work task sequence 0003, no tasks running":
        fail("idle statement mismatch")
    false_authority(state.get("authority") or {}, "orchestration")

    consolidation = state.get("session_consolidation") or {}
    if consolidation.get("state") != "COMPLETE" or consolidation.get("archive_ready") is not True:
        fail("session is not archive-ready")
    if set(consolidation.get("canonical_continuation") or []) != {"StegVerse-org/LLM-adapter#18", "StegVerse-org/LLM-adapter#72", "StegVerse-Labs/TVC#6"}:
        fail("canonical continuation drift")

    completed = state.get("completed_tasks") or []
    reconciled = one(completed, TASK_ID)
    for key, value in {
        "state":"COMPLETE", "pull_request":118, "merge_commit":MERGE,
        "main_workflow_run":RUN, "artifact_id":ARTIFACT, "artifact_digest":ARTIFACT_DIGEST,
        "source_receipt_sha256":SOURCE_RECEIPT, "committed_receipt_sha256":COMMITTED_RECEIPT,
        "authority_effect":False,
    }.items():
        if reconciled.get(key) != value:
            fail(f"completed reconciliation {key} mismatch")
    if reconciled.get("closed_superseded_prs") != [10,13,27,60] or reconciled.get("superseded_draft_controlled_prs") != [23]:
        fail("superseded PR sets mismatch")
    if reconciled.get("review_required_unclaimed_prs") != [63] or reconciled.get("preserved_distinct_unclaimed_prs") != [36,58,85]:
        fail("preserved or review-required PR sets mismatch")

    live = one(state.get("queued_exclusive_tasks") or [], "LLMA-0002-LIVE-PROVIDER")
    if live.get("owner") != "issue/18" or live.get("state") != "BLOCKED" or live.get("execution_class") != "EXCLUSIVE":
        fail("live-provider ownership or state mismatch")
    if live.get("blocked_until") != "all authority-bound blockers are cleared" or set(live.get("external_blockers") or []) != BLOCKERS:
        fail("live-provider release condition mismatch")
    if str(RUN) not in "\n".join(live.get("completed_dependency_evidence") or []):
        fail("reconciliation dependency missing from live-provider task")

    observer = one(state.get("machine_owned_observers") or [], "LLMA-OPEN-PR-CONSOLIDATION", "observer_id")
    if observer.get("state") != "COMPLETE" or observer.get("observed_result") != "PASS" or observer.get("latest_run") != RUN or observer.get("artifact_id") != ARTIFACT:
        fail("open-PR observer evidence mismatch")
    if observer.get("authority_effect") is not False:
        fail("open-PR observer grants authority")

    if inventory.get("task_id") != TASK_ID or inventory.get("authority_effect") is not False:
        fail("inventory identity or authority mismatch")
    if task.get("state") != "COMPLETE" or task.get("claimant") is not None:
        fail("task claim is not released")
    if task.get("claim_release_condition") != "SATISFIED" or not str(task.get("archive_dependency", "")).startswith("SATISFIED"):
        fail("task release or archive dependency mismatch")
    if task.get("manual_user_action_required") is not False or task.get("authority_effect") is not False:
        fail("task assigns manual action or authority")

    if receipt.get("schema") != "stegverse.llm_adapter.open_pr_consolidation_receipt.v1" or receipt.get("state") != "COMPLETE":
        fail("committed receipt schema or state mismatch")
    if receipt.get("receipt_sha256") != COMMITTED_RECEIPT or receipt.get("source_receipt_sha256") != SOURCE_RECEIPT:
        fail("committed or source receipt hash mismatch")
    verify_hash(receipt)
    rows = receipt.get("observations") or []
    if len(rows) != 9 or {row.get("number") for row in rows} != {10,13,23,27,36,58,60,63,85}:
        fail("receipt observation denominator mismatch")
    workflow = receipt.get("workflow_evidence") or {}
    for key, value in (("pull_request",118),("merge_commit",MERGE),("main_run",RUN),("artifact_id",ARTIFACT),("artifact_digest",ARTIFACT_DIGEST)):
        if workflow.get(key) != value:
            fail(f"receipt workflow {key} mismatch")

    if not WORKFLOW.is_file() or not VALIDATOR.is_file():
        fail("open-PR automation incomplete")
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    for token in ("pull_request:", "push:", "workflow_dispatch:", "gh api", "retention-days: 90"):
        if token not in workflow_text:
            fail(f"workflow missing {token}")

    if publication.get("state") != "PUBLISHED" or publication.get("blockers") != [] or publication.get("digest") != IMAGE_DIGEST or publication.get("receipt_sha256") != IMAGE_RECEIPT:
        fail("publication evidence regressed")
    verify_hash(publication)
    if readiness.get("state") != "READY" or readiness.get("blockers") != []:
        fail("publication readiness regressed")
    if readiness.get("observed_digest") != publication.get("digest") or readiness.get("observed_receipt_state") != publication.get("state"):
        fail("publication readiness does not match current receipt")
    false_authority({"provider":readiness.get("provider_execution_authorized"),"deployment":readiness.get("persistent_deployment_authorized"),"custody":readiness.get("custody_authorized"),"site":readiness.get("site_activation_authorized")}, "publication readiness")

    if service_gateway.get("result") != "PASS" or (service_gateway.get("main_activation") or {}).get("workflow_run") != 30967405348:
        fail("Service Gateway proof mismatch")
    false_authority(service_gateway.get("authority") or {}, "Service Gateway proof")

    if provider_activation.get("state") != "CONFIGURATION_REQUIRED" or any((provider_activation.get("configuration") or {}).values()):
        fail("provider activation changed without verified authority")
    if monitor.get("semantic_state") != "PENDING" or monitor.get("semantic_blockers") != ["live_activation_observation_not_yet_recorded"]:
        fail("live activation monitor posture mismatch")
    false_authority(monitor.get("authority_boundary") or {}, "live activation monitor")

    handoff = HANDOFF.read_text(encoding="utf-8")
    for token in ("ARCHIVE THIS SESSION", "active_repository_claims: 0", TASK_ID, "PR #63 remains REVIEW_REQUIRED and unclaimed", "StegVerse-org/LLM-adapter#18"):
        if token not in handoff:
            fail(f"handoff missing {token}")

    print("LLM_ADAPTER_ORCHESTRATION_STATE_PASS")
    print("sequence=0003 active_tasks=0 archive_ready=true")
    print(f"open_pr_run={RUN} artifact={ARTIFACT} live_provider={live['state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
