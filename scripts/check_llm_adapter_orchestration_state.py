#!/usr/bin/env python3
"""Fail closed when LLM-adapter ownership or retained evidence drifts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "llm-adapter-orchestration-state.json"
PUBLICATION_TASK_PATH = ROOT / "tasks" / "LLMA-PUBLICATION-ACTIVATION-013.json"
SEQUENCE_TASK_PATH = ROOT / "tasks" / "LLMA-SEQUENCE-0001-RELEASE-015.json"
PUBLICATION_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "stegdeploy-image.yml"
SERVICE_GATEWAY_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "service-gateway-deploy.yml"
SERVICE_GATEWAY_TEST_PATH = ROOT / "tests" / "test_service_gateway.py"
PUBLICATION_HANDOFF_PATH = ROOT / "docs" / "STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md"
RECEIPT_PATH = ROOT / "receipts" / "stegdeploy-image-publication.json"
READINESS_PATH = ROOT / "status" / "stegdeploy-image-publication-readiness.json"
PULL_LOG_PATH = ROOT / "receipts" / "stegdeploy-image-verification-pull.log"

EXPECTED_DIGEST = "sha256:a5049d8d1a02f32475e4c9034eb6d9e626a1203507ae53da651237e39a04a961"
EXPECTED_PUBLICATION_RECEIPT = "80b0bc5063531a74194adedfcbf48677ca832ae29156b46ece14f188e58c7432"
EXPECTED_PUBLICATION_RUN = "30967405336"
EXPECTED_PUBLICATION_JOB = 92184247965
EXPECTED_TVC_COMMIT = "b1a817e629aff483ab80679297013b33e692b567"
EXPECTED_TVC_BLOB = "e376f2c276bda75ff497709637aac693853bf9cc"
EXPECTED_HIL_RUN = 30966031698
EXPECTED_PROVIDER_RUN = 30966031661
EXPECTED_SERVICE_GATEWAY_RUN = 30967405348


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


def record(items: list[dict], identifier: str, key: str = "task_id") -> dict:
    matches = [item for item in items if item.get(key) == identifier]
    if len(matches) != 1:
        fail(f"expected exactly one {identifier} by {key}; found {len(matches)}")
    return matches[0]


def assert_false_authority(value: dict, label: str) -> None:
    if not value or any(flag is not False for flag in value.values()):
        fail(f"{label} grants authority")


def main() -> int:
    state = load_json(STATE_PATH)
    publication_task = load_json(PUBLICATION_TASK_PATH)
    sequence_task = load_json(SEQUENCE_TASK_PATH)
    receipt = load_json(RECEIPT_PATH)
    readiness = load_json(READINESS_PATH)

    if state.get("schema_version") != "1.1.0" or state.get("repository") != "StegVerse-org/LLM-adapter":
        fail("orchestration identity mismatch")
    if state.get("status") != "ACTIVE_WITH_DECLARED_BLOCKERS" or state.get("task_sequence") != 2:
        fail("unexpected orchestration posture")

    active = state.get("active_tasks") or []
    if len(active) != 1:
        fail("sequence 0002 must have exactly one bounded active task before final release")
    active_task = record(active, "LLMA-SEQUENCE-0001-RELEASE-015")
    if active_task.get("owner") != "pull/116" or active_task.get("state") != "CLAIMED_FOR_VALIDATION":
        fail("publication-trigger stabilization claim mismatch")

    completed = state.get("completed_tasks") or []
    publication = record(completed, "LLMA-0001-IMAGE-PUBLICATION")
    if publication.get("state") != "COMPLETE":
        fail("publication task is not complete")
    for key, expected in (
        ("publication_run", int(EXPECTED_PUBLICATION_RUN)),
        ("publication_job", EXPECTED_PUBLICATION_JOB),
        ("publication_receipt_sha256", EXPECTED_PUBLICATION_RECEIPT),
        ("image_digest", EXPECTED_DIGEST),
        ("consumer_pull_verified", True),
        ("readiness_state", "READY"),
    ):
        if publication.get(key) != expected:
            fail(f"publication completed-task {key} mismatch")
    if publication.get("scheduler_owner") != "StegVerse-Labs/StegVerse-Healer":
        fail("publication scheduler owner mismatch")

    hil = record(completed, "LLMA-0001-HIL-CYCLE")
    if hil.get("state") != "COMPLETE" or hil.get("workflow_run") != EXPECTED_HIL_RUN:
        fail("HIL full-cycle evidence mismatch")
    if hil.get("persistent_deployment_proven") is not False:
        fail("ephemeral HIL proof is represented as persistent deployment")

    goal8 = record(completed, "LLMA-0001-GOAL8")
    if goal8.get("state") != "COMPLETE" or goal8.get("workflow_run") != EXPECTED_PROVIDER_RUN:
        fail("provider usage validation evidence mismatch")
    if goal8.get("python_versions") != ["3.9", "3.11", "3.12"] or goal8.get("authority_effect") is not False:
        fail("provider usage validation matrix or authority mismatch")

    live = record(state.get("queued_exclusive_tasks") or [], "LLMA-0002-LIVE-PROVIDER")
    if live.get("owner") != "issue/18" or live.get("execution_class") != "EXCLUSIVE":
        fail("live provider ownership changed")
    blockers = set(live.get("external_blockers") or [])
    if blockers != {
        "authorized provider configuration and scoped execution grant",
        "persistent endpoint",
        "authenticated Master Records custody configuration",
    }:
        fail("live-provider blocker set changed without evidence")
    dependency_text = "\n".join(live.get("completed_dependency_evidence") or [])
    for required in (EXPECTED_DIGEST, EXPECTED_PUBLICATION_RUN, str(EXPECTED_HIL_RUN), str(EXPECTED_PROVIDER_RUN), str(EXPECTED_SERVICE_GATEWAY_RUN)):
        if required not in dependency_text:
            fail(f"completed dependency evidence missing {required}")

    healer = record(state.get("machine_owned_observers") or [], "LLMA-HEALER-PUBLICATION-RELAY", "observer_id")
    if healer.get("owner") != "StegVerse-Labs/StegVerse-Healer" or healer.get("observed_result") != "HTTP 403":
        fail("Healer relay state mismatch")
    monitor = record(state.get("machine_owned_observers") or [], "LLMA-LIVE-ACTIVATION-MONITOR", "observer_id")
    if monitor.get("state") != "PENDING" or monitor.get("authority_effect") is not False:
        fail("live activation monitor state mismatch")
    assert_false_authority(state.get("authority") or {}, "orchestration")

    if publication_task.get("task_id") != "LLMA-PUBLICATION-ACTIVATION-013":
        fail("publication task identity mismatch")
    if publication_task.get("state") != "COMPLETE" or publication_task.get("claimant") is not None:
        fail("publication claim is not released")
    publication_validation = publication_task.get("validation") or {}
    for key, expected in (
        ("publication_run", int(EXPECTED_PUBLICATION_RUN)),
        ("publication_job", EXPECTED_PUBLICATION_JOB),
        ("publication_state", "PUBLISHED"),
        ("publication_receipt_sha256", EXPECTED_PUBLICATION_RECEIPT),
        ("image_digest", EXPECTED_DIGEST),
        ("consumer_pull_verified", True),
        ("readiness_state", "READY"),
    ):
        if publication_validation.get(key) != expected:
            fail(f"publication task validation {key} mismatch")

    if sequence_task.get("task_id") != "LLMA-SEQUENCE-0001-RELEASE-015":
        fail("sequence task identity mismatch")
    if sequence_task.get("state") != "CLAIMED_FOR_VALIDATION" or sequence_task.get("claimant") != "session-sequence-release-lane":
        fail("sequence task claim mismatch")
    if sequence_task.get("manual_user_action_required") is not False or sequence_task.get("authority_effect") is not False:
        fail("sequence task assigns manual work or authority")

    if receipt.get("schema") != "stegdeploy.image-publication.v2" or receipt.get("state") != "PUBLISHED":
        fail("retained publication receipt is not PUBLISHED v2")
    if receipt.get("blockers") != [] or receipt.get("consumer_pull_verified") is not True:
        fail("retained publication receipt has blockers or lacks fresh pull")
    for key, expected in (
        ("digest", EXPECTED_DIGEST),
        ("receipt_sha256", EXPECTED_PUBLICATION_RECEIPT),
        ("publication_run_id", EXPECTED_PUBLICATION_RUN),
    ):
        if receipt.get(key) != expected:
            fail(f"retained publication receipt {key} mismatch")
    material = dict(receipt)
    declared_hash = material.pop("receipt_sha256")
    actual_hash = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if declared_hash != actual_hash:
        fail("retained publication receipt hash is invalid")

    if readiness.get("state") != "READY" or readiness.get("blockers") != []:
        fail("publication readiness is not READY")
    if readiness.get("observed_digest") != EXPECTED_DIGEST or readiness.get("consumer_pull_verified") is not True:
        fail("readiness does not match retained publication")
    assert_false_authority({
        "provider": readiness.get("provider_execution_authorized"),
        "deployment": readiness.get("persistent_deployment_authorized"),
        "custody": readiness.get("custody_authorized"),
        "site": readiness.get("site_activation_authorized"),
    }, "publication readiness")

    if not PULL_LOG_PATH.is_file() or EXPECTED_DIGEST not in PULL_LOG_PATH.read_text(encoding="utf-8"):
        fail("fresh consumer pull log is missing the expected digest")

    publication_workflow = PUBLICATION_WORKFLOW_PATH.read_text(encoding="utf-8")
    for required in ("workflow_dispatch:", "StegVerse-Labs/StegVerse-Healer", "llm_adapter/**", ".github/workflows/stegdeploy-image.yml"):
        if required not in publication_workflow:
            fail(f"publication workflow missing {required}")
    trigger_section = publication_workflow.split("permissions:", 1)[0]
    for forbidden in (
        "scripts/check_stegdeploy_image_publication_readiness.py",
        "status/stegdeploy-image-publication-readiness.json",
        "docs/STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md",
        "schedule:",
    ):
        if forbidden in trigger_section:
            fail(f"publication workflow still contains forbidden trigger or schedule: {forbidden}")

    gateway_workflow = SERVICE_GATEWAY_WORKFLOW_PATH.read_text(encoding="utf-8")
    for required in (
        "pull_request:",
        f"TVC_COMMIT: {EXPECTED_TVC_COMMIT}",
        f"TVC_BLOB_SHA: {EXPECTED_TVC_BLOB}",
        "duplicate_receipt_equal",
        "Enforce activation result",
        "ephemeral GitHub-hosted activation proof; not persistent public hosting",
    ):
        if required not in gateway_workflow:
            fail(f"Service Gateway workflow missing {required}")
    gateway_test = SERVICE_GATEWAY_TEST_PATH.read_text(encoding="utf-8")
    if 'receipt_hash = material.pop("receipt_sha256")' not in gateway_test or 'material.pop("receiver_signature")' in gateway_test:
        fail("Service Gateway receipt-hash test does not match v2 semantics")

    publication_handoff = PUBLICATION_HANDOFF_PATH.read_text(encoding="utf-8")
    for required in (EXPECTED_DIGEST, EXPECTED_PUBLICATION_RECEIPT, EXPECTED_PUBLICATION_RUN, "claim_state: COMPLETE", "HTTP 403"):
        if required not in publication_handoff:
            fail(f"publication handoff missing {required}")

    print("LLM_ADAPTER_ORCHESTRATION_STATE_PASS")
    print(f"active_tasks={len(active)} current_publication_run={EXPECTED_PUBLICATION_RUN}")
    print(f"hil_run={EXPECTED_HIL_RUN} provider_validation_run={EXPECTED_PROVIDER_RUN}")
    print(f"service_gateway_run={EXPECTED_SERVICE_GATEWAY_RUN} publication_trigger=STABILIZED_PENDING_MERGE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
