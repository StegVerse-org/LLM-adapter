#!/usr/bin/env python3
"""Fail closed when LLM-adapter task ownership or retained evidence drifts."""
from __future__ import annotations

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

EXPECTED_DIGEST = "sha256:e465d52b3f41db9563fecaef5c5952c09c87d1777b85aafe566e187ffefcba55"
EXPECTED_PUBLICATION_RECEIPT = "2ebacb9f5efc426a38bbbb58492b70575b9408127f5f57a34f066b51a43ba7a9"
EXPECTED_PUBLICATION_RUN = "30964767464"
EXPECTED_HIL_MERGE = "e320c33189c1b6cf9d51a666a4505592b6fb981b"
EXPECTED_HIL_RUN = 30966031698
EXPECTED_HIL_RECEIPT = "f4d0a8b90b05017b5abf77f3c96c3b8ad3efb99eb57d9c68b90a611b928888da"
EXPECTED_HIL_ARTIFACT = 8914746865
EXPECTED_HIL_ARTIFACT_DIGEST = "sha256:e9fe894eb2331c9d3792545cbb68d2f0d9762b2b05327732ec4482adf20d1350"
EXPECTED_PROVIDER_RUN = 30966031661
EXPECTED_ARCHITECTURE_RUN = 30966031667
EXPECTED_FULL_VALIDATE_RUN = 30966031655


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


def record_by_id(items: list[dict], identifier: str, key: str = "task_id") -> dict:
    matches = [item for item in items if item.get(key) == identifier]
    if len(matches) != 1:
        fail(f"expected exactly one {identifier} by {key}; found {len(matches)}")
    return matches[0]


def main() -> int:
    state = load_json(STATE_PATH)
    publication_task = load_json(PUBLICATION_TASK_PATH)
    sequence_task = load_json(SEQUENCE_TASK_PATH)
    receipt = load_json(RECEIPT_PATH)
    readiness = load_json(READINESS_PATH)

    if state.get("schema_version") != "1.1.0":
        fail("unexpected orchestration schema version")
    if state.get("repository") != "StegVerse-org/LLM-adapter":
        fail("repository mismatch")
    if state.get("status") != "ACTIVE_WITH_DECLARED_BLOCKERS":
        fail("unexpected repository status")
    if state.get("task_sequence") != 2:
        fail("sequence 0001 was not advanced after completed task release")

    active = state.get("active_tasks") or []
    if not isinstance(active, list) or len(active) != 1:
        fail("sequence 0002 must have exactly one bounded active task")
    active_task = record_by_id(active, "LLMA-SEQUENCE-0001-RELEASE-015")
    if active_task.get("owner") != "branch/fix/service-gateway-proof-and-release-sequence":
        fail("sequence release owner mismatch")
    if active_task.get("state") != "CLAIMED_FOR_VALIDATION":
        fail("sequence release task is not in validation")
    if any(item.get("owner") in {"pull/44", "pull/56"} for item in active):
        fail("completed or superseded HIL owner remains active")
    if any(item.get("task_id") in {"LLMA-0001-HIL-CYCLE", "LLMA-0001-GOAL8"} for item in active):
        fail("completed sequence 0001 task remains active")

    completed = state.get("completed_tasks") or []
    merged = record_by_id(completed, "LLMA-SESSION-PROVIDER-LAYER-2026-08-02")
    if merged.get("state") != "MERGED_INTO_CANONICAL_WORKSTREAM":
        fail("merged PR #95 claim is not released")
    if merged.get("merge_commit") != "1505aac0073bc6466769ca84c6ae28d887abdefd":
        fail("PR #95 merge evidence mismatch")

    publication = record_by_id(completed, "LLMA-0001-IMAGE-PUBLICATION")
    if publication.get("state") != "COMPLETE":
        fail("publication task is not complete")
    if publication.get("scheduler_owner") != "StegVerse-Labs/StegVerse-Healer":
        fail("publication recurrence must remain delegated to StegVerse-Healer")
    if publication.get("image_digest") != EXPECTED_DIGEST:
        fail("publication task digest mismatch")
    if publication.get("publication_receipt_sha256") != EXPECTED_PUBLICATION_RECEIPT:
        fail("publication task receipt mismatch")
    if publication.get("consumer_pull_verified") is not True:
        fail("publication task lacks consumer pull evidence")

    hil = record_by_id(completed, "LLMA-0001-HIL-CYCLE")
    if hil.get("state") != "COMPLETE" or hil.get("owner") != "merged-pull/56":
        fail("HIL full-cycle claim is not released")
    if hil.get("merge_commit") != EXPECTED_HIL_MERGE:
        fail("HIL merge evidence mismatch")
    if hil.get("workflow_run") != EXPECTED_HIL_RUN:
        fail("HIL workflow evidence mismatch")
    if hil.get("receipt_sha256") != EXPECTED_HIL_RECEIPT:
        fail("HIL receipt mismatch")
    if hil.get("artifact_id") != EXPECTED_HIL_ARTIFACT:
        fail("HIL artifact ID mismatch")
    if hil.get("artifact_digest") != EXPECTED_HIL_ARTIFACT_DIGEST:
        fail("HIL artifact digest mismatch")
    if hil.get("persistent_deployment_proven") is not False:
        fail("ephemeral HIL proof was misrepresented as persistent deployment")

    goal8 = record_by_id(completed, "LLMA-0001-GOAL8")
    if goal8.get("state") != "COMPLETE":
        fail("Goal 8 provider validation is not complete")
    if goal8.get("workflow_run") != EXPECTED_PROVIDER_RUN:
        fail("Goal 8 workflow evidence mismatch")
    if goal8.get("python_versions") != ["3.9", "3.11", "3.12"]:
        fail("Goal 8 Python matrix mismatch")
    if goal8.get("canonical_fixture_and_adversarial_tests") is not True:
        fail("Goal 8 fixture or adversarial evidence missing")
    if goal8.get("authority_effect") is not False:
        fail("Goal 8 validation grants authority")

    queued = state.get("queued_exclusive_tasks") or []
    live = record_by_id(queued, "LLMA-0002-LIVE-PROVIDER")
    if live.get("owner") != "issue/18" or live.get("execution_class") != "EXCLUSIVE":
        fail("live provider task ownership or class changed")
    blockers = set(live.get("external_blockers") or [])
    required_blockers = {
        "authorized provider configuration and scoped execution grant",
        "persistent endpoint",
        "authenticated Master Records custody configuration",
    }
    if blockers != required_blockers:
        fail("live-provider blocker set does not match current proven state")
    completed_dependencies = "\n".join(live.get("completed_dependency_evidence") or [])
    for required in (
        EXPECTED_DIGEST,
        EXPECTED_PUBLICATION_RUN,
        str(EXPECTED_HIL_RUN),
        str(EXPECTED_PROVIDER_RUN),
    ):
        if required not in completed_dependencies:
            fail(f"completed dependency evidence missing {required}")

    observers = state.get("machine_owned_observers") or []
    healer = record_by_id(observers, "LLMA-HEALER-PUBLICATION-RELAY", key="observer_id")
    if healer.get("owner") != "StegVerse-Labs/StegVerse-Healer":
        fail("publication observer owner mismatch")
    if healer.get("state") != "BLOCKED" or healer.get("observed_result") != "HTTP 403":
        fail("Healer relay blocker changed without evidence")
    monitor = record_by_id(observers, "LLMA-LIVE-ACTIVATION-MONITOR", key="observer_id")
    if monitor.get("state") != "PENDING" or monitor.get("authority_effect") is not False:
        fail("live activation monitor state or authority changed")

    authority = state.get("authority") or {}
    if not authority or any(value is not False for value in authority.values()):
        fail("orchestration state grants authority")

    if sequence_task.get("task_id") != "LLMA-SEQUENCE-0001-RELEASE-015":
        fail("sequence task ID mismatch")
    if sequence_task.get("state") != "CLAIMED_FOR_VALIDATION":
        fail("sequence task state mismatch")
    if sequence_task.get("claimant") != "session-sequence-release-lane":
        fail("sequence task claimant mismatch")
    if sequence_task.get("manual_user_action_required") is not False:
        fail("sequence task incorrectly assigns manual user action")
    if sequence_task.get("authority_effect") is not False:
        fail("sequence task grants authority")
    dependencies = sequence_task.get("completed_dependencies") or {}
    if (dependencies.get("hil_full_cycle") or {}).get("workflow_run") != EXPECTED_HIL_RUN:
        fail("sequence task HIL evidence mismatch")
    provider_validation = dependencies.get("provider_usage_validation") or {}
    if provider_validation.get("workflow_run") != EXPECTED_PROVIDER_RUN:
        fail("sequence task provider validation evidence mismatch")
    if (dependencies.get("architecture_guard") or {}).get("workflow_run") != EXPECTED_ARCHITECTURE_RUN:
        fail("sequence task architecture evidence mismatch")
    if (dependencies.get("full_repository_validation") or {}).get("workflow_run") != EXPECTED_FULL_VALIDATE_RUN:
        fail("sequence task full validation evidence mismatch")

    if publication_task.get("task_id") != "LLMA-PUBLICATION-ACTIVATION-013":
        fail("publication activation task ID mismatch")
    if publication_task.get("state") != "COMPLETE" or publication_task.get("claimant") is not None:
        fail("publication activation claim is not released")
    publication_validation = publication_task.get("validation") or {}
    if publication_validation.get("publication_state") != "PUBLISHED":
        fail("publication task does not record PUBLISHED")
    if publication_validation.get("image_digest") != EXPECTED_DIGEST:
        fail("publication task digest mismatch")

    if receipt.get("schema") != "stegdeploy.image-publication.v2":
        fail("retained publication receipt is not v2")
    if receipt.get("state") != "PUBLISHED" or receipt.get("blockers") != []:
        fail("retained publication receipt is not zero-blocker PUBLISHED")
    if receipt.get("digest") != EXPECTED_DIGEST:
        fail("retained image digest mismatch")
    if receipt.get("receipt_sha256") != EXPECTED_PUBLICATION_RECEIPT:
        fail("retained receipt hash mismatch")
    if receipt.get("publication_run_id") != EXPECTED_PUBLICATION_RUN:
        fail("retained publication run mismatch")
    if receipt.get("consumer_pull_verified") is not True:
        fail("retained receipt lacks consumer pull verification")

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

    publication_workflow = PUBLICATION_WORKFLOW_PATH.read_text(encoding="utf-8")
    if "schedule:" in publication_workflow:
        fail("managed schedule is present outside StegVerse-Healer")
    if "workflow_dispatch:" not in publication_workflow:
        fail("explicit publication dispatch trigger missing")
    if "StegVerse-Labs/StegVerse-Healer" not in publication_workflow:
        fail("publication workflow does not declare canonical scheduler owner")

    gateway_workflow = SERVICE_GATEWAY_WORKFLOW_PATH.read_text(encoding="utf-8")
    for required in (
        "Verify pinned public-safe TVC evaluator mirror",
        "vendor/tvc/${TVC_COMMIT}/tvc_secret_governance.py",
        "result.mkdir(parents=True, exist_ok=True)",
        "ephemeral GitHub-hosted activation proof; not persistent public hosting",
    ):
        if required not in gateway_workflow:
            fail(f"Service Gateway workflow missing {required}")
    gateway_test = SERVICE_GATEWAY_TEST_PATH.read_text(encoding="utf-8")
    if 'receipt_hash = material.pop("receipt_sha256")' not in gateway_test:
        fail("Service Gateway test does not remove only receipt_sha256")
    if 'material.pop("receiver_signature")' in gateway_test:
        fail("Service Gateway test still excludes receiver_signature from receipt hash")

    publication_handoff = PUBLICATION_HANDOFF_PATH.read_text(encoding="utf-8")
    for required in (
        "LLMA-PUBLICATION-ACTIVATION-013",
        "claim_state: COMPLETE",
        EXPECTED_DIGEST,
        EXPECTED_PUBLICATION_RECEIPT,
        EXPECTED_PUBLICATION_RUN,
        "StegVerse-Labs/StegVerse-Healer",
        "HTTP 403",
    ):
        if required not in publication_handoff:
            fail(f"publication handoff missing {required}")

    print("LLM_ADAPTER_ORCHESTRATION_STATE_PASS")
    print(f"active_tasks={len(active)} completed_tasks={len(completed)} queued_exclusive={len(queued)}")
    print(f"hil_cycle=COMPLETE run={EXPECTED_HIL_RUN} receipt={EXPECTED_HIL_RECEIPT}")
    print(f"provider_usage_validation=COMPLETE run={EXPECTED_PROVIDER_RUN}")
    print("sequence_0002=CLAIMED_FOR_VALIDATION service_gateway_proof=PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
