#!/usr/bin/env python3
"""Fail closed when LLM-adapter task ownership or publication evidence drifts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "llm-adapter-orchestration-state.json"
TASK_PATH = ROOT / "tasks" / "LLMA-PUBLICATION-ACTIVATION-013.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "stegdeploy-image.yml"
HANDOFF_PATH = ROOT / "docs" / "STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md"
RECEIPT_PATH = ROOT / "receipts" / "stegdeploy-image-publication.json"
READINESS_PATH = ROOT / "status" / "stegdeploy-image-publication-readiness.json"
PULL_LOG_PATH = ROOT / "receipts" / "stegdeploy-image-verification-pull.log"

EXPECTED_DIGEST = "sha256:e465d52b3f41db9563fecaef5c5952c09c87d1777b85aafe566e187ffefcba55"
EXPECTED_RECEIPT = "2ebacb9f5efc426a38bbbb58492b70575b9408127f5f57a34f066b51a43ba7a9"
EXPECTED_RUN = "30964767464"


def fail(message: str) -> None:
    raise SystemExit(f"LLM_ADAPTER_ORCHESTRATION_STATE_FAIL: {message}")


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON at {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected object at {path.relative_to(ROOT)}")
    return value


def task_by_id(items: list[dict], task_id: str) -> dict:
    matches = [item for item in items if item.get("task_id") == task_id]
    if len(matches) != 1:
        fail(f"expected exactly one {task_id}; found {len(matches)}")
    return matches[0]


def main() -> int:
    state = load_json(STATE_PATH)
    task = load_json(TASK_PATH)
    receipt = load_json(RECEIPT_PATH)
    readiness = load_json(READINESS_PATH)

    if state.get("schema_version") != "1.1.0":
        fail("unexpected orchestration schema version")
    if state.get("repository") != "StegVerse-org/LLM-adapter":
        fail("repository mismatch")
    if state.get("status") != "ACTIVE_WITH_DECLARED_BLOCKERS":
        fail("unexpected repository status")

    active = state.get("active_tasks") or []
    if not isinstance(active, list) or not active:
        fail("active task registry missing")
    task_ids = [item.get("task_id") for item in active]
    if len(task_ids) != len(set(task_ids)):
        fail("duplicate active task IDs")
    if any(item.get("owner") == "pull/44" for item in active):
        fail("closed PR #44 remains an active owner")
    if any(item.get("task_id") == "LLMA-0001-IMAGE-PUBLICATION" for item in active):
        fail("completed publication task remains active")

    hil = task_by_id(active, "LLMA-0001-HIL-CYCLE")
    if hil.get("owner") != "pull/56" or hil.get("superseded_owner") != "pull/44":
        fail("HIL owner reconciliation is incomplete")

    completed = state.get("completed_tasks") or []
    merged = task_by_id(completed, "LLMA-SESSION-PROVIDER-LAYER-2026-08-02")
    if merged.get("state") != "MERGED_INTO_CANONICAL_WORKSTREAM":
        fail("merged PR #95 claim is not released")
    if merged.get("merge_commit") != "1505aac0073bc6466769ca84c6ae28d887abdefd":
        fail("PR #95 merge evidence mismatch")

    publication = task_by_id(completed, "LLMA-0001-IMAGE-PUBLICATION")
    if publication.get("state") != "COMPLETE":
        fail("publication task is not complete")
    if publication.get("scheduler_owner") != "StegVerse-Labs/StegVerse-Healer":
        fail("publication recurrence must remain delegated to StegVerse-Healer")
    if publication.get("image_digest") != EXPECTED_DIGEST:
        fail("publication task digest mismatch")
    if publication.get("publication_receipt_sha256") != EXPECTED_RECEIPT:
        fail("publication task receipt mismatch")
    if publication.get("consumer_pull_verified") is not True:
        fail("publication task lacks consumer pull evidence")

    queued = state.get("queued_exclusive_tasks") or []
    live = task_by_id(queued, "LLMA-0002-LIVE-PROVIDER")
    if live.get("owner") != "issue/18" or live.get("execution_class") != "EXCLUSIVE":
        fail("live provider task ownership or class changed")
    blockers = set(live.get("external_blockers") or [])
    required_blockers = {
        "authorized provider configuration",
        "persistent endpoint",
        "authenticated Master Records custody configuration",
    }
    if blockers != required_blockers:
        fail("live-provider blocker set does not match current proven state")
    completed_dependencies = "\n".join(live.get("completed_dependency_evidence") or [])
    if EXPECTED_DIGEST not in completed_dependencies or EXPECTED_RUN not in completed_dependencies:
        fail("published-package completion evidence missing from live-provider task")

    observers = state.get("machine_owned_observers") or []
    observer = task_by_id(observers, "LLMA-HEALER-PUBLICATION-RELAY")
    if observer.get("owner") != "StegVerse-Labs/StegVerse-Healer":
        fail("publication observer owner mismatch")
    if observer.get("state") != "BLOCKED" or observer.get("observed_result") != "HTTP 403":
        fail("Healer relay blocker changed without evidence")

    authority = state.get("authority") or {}
    if not authority or any(value is not False for value in authority.values()):
        fail("orchestration state grants authority")

    if task.get("task_id") != "LLMA-PUBLICATION-ACTIVATION-013":
        fail("activation task ID mismatch")
    if task.get("state") != "COMPLETE" or task.get("claimant") is not None:
        fail("activation claim is not released")
    if task.get("canonical_issue") != "StegVerse-org/LLM-adapter#18":
        fail("activation task canonical owner mismatch")
    if task.get("scheduler_owner") != "StegVerse-Labs/StegVerse-Healer":
        fail("activation task scheduler owner mismatch")
    if task.get("authority_effect") is not False:
        fail("activation task grants authority")

    validation = task.get("validation") or {}
    if validation.get("publication_state") != "PUBLISHED":
        fail("task validation does not record PUBLISHED")
    if validation.get("image_digest") != EXPECTED_DIGEST:
        fail("task validation digest mismatch")
    if validation.get("publication_receipt_sha256") != EXPECTED_RECEIPT:
        fail("task validation receipt mismatch")

    if receipt.get("schema") != "stegdeploy.image-publication.v2":
        fail("retained publication receipt is not v2")
    if receipt.get("state") != "PUBLISHED" or receipt.get("blockers") != []:
        fail("retained publication receipt is not zero-blocker PUBLISHED")
    if receipt.get("digest") != EXPECTED_DIGEST:
        fail("retained image digest mismatch")
    if receipt.get("receipt_sha256") != EXPECTED_RECEIPT:
        fail("retained receipt hash mismatch")
    if receipt.get("publication_run_id") != EXPECTED_RUN:
        fail("retained publication run mismatch")
    if receipt.get("consumer_pull_verified") is not True:
        fail("retained receipt lacks consumer pull verification")
    outcomes = receipt.get("stage_outcomes") or {}
    if set(outcomes.values()) != {"success"} or len(outcomes) != 4:
        fail("not all publication stages succeeded")

    if readiness.get("state") != "READY" or readiness.get("blockers") != []:
        fail("publication readiness is not READY")
    if readiness.get("observed_digest") != EXPECTED_DIGEST:
        fail("readiness digest mismatch")
    if readiness.get("consumer_pull_verified") is not True:
        fail("readiness lacks consumer pull verification")
    for authority_key in (
        "provider_execution_authorized",
        "persistent_deployment_authorized",
        "custody_authorized",
        "site_activation_authorized",
    ):
        if readiness.get(authority_key) is not False:
            fail(f"readiness grants {authority_key}")

    if not PULL_LOG_PATH.is_file():
        fail("retained pull log missing")
    pull_log = PULL_LOG_PATH.read_text(encoding="utf-8")
    if EXPECTED_DIGEST not in pull_log:
        fail("retained pull log digest mismatch")
    if "Downloaded newer image for ghcr.io/stegverse-org/llm-adapter:main" not in pull_log:
        fail("retained pull log lacks successful consumer status")

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    if "schedule:" in workflow:
        fail("managed schedule is present outside StegVerse-Healer")
    if "workflow_dispatch:" not in workflow:
        fail("explicit publication dispatch trigger missing")
    if "StegVerse-Labs/StegVerse-Healer" not in workflow:
        fail("workflow does not declare the canonical scheduler owner")

    handoff = HANDOFF_PATH.read_text(encoding="utf-8")
    for required in (
        "LLMA-PUBLICATION-ACTIVATION-013",
        "claim_state: COMPLETE",
        EXPECTED_DIGEST,
        EXPECTED_RECEIPT,
        EXPECTED_RUN,
        "StegVerse-Labs/StegVerse-Healer",
        "HTTP 403",
    ):
        if required not in handoff:
            fail(f"publication handoff missing {required}")

    print("LLM_ADAPTER_ORCHESTRATION_STATE_PASS")
    print(f"active_tasks={len(active)} completed_tasks={len(completed)} queued_exclusive={len(queued)}")
    print(f"publication_state=PUBLISHED digest={EXPECTED_DIGEST}")
    print("scheduler_owner=StegVerse-Labs/StegVerse-Healer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
