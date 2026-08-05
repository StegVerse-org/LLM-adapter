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
SERVICE_GATEWAY_RECEIPT_PATH = ROOT / "receipts" / "service-gateway-activation-proof.json"
PUBLICATION_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "stegdeploy-image.yml"
SERVICE_GATEWAY_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "service-gateway-deploy.yml"
SERVICE_GATEWAY_TEST_PATH = ROOT / "tests" / "test_service_gateway.py"
PUBLICATION_HANDOFF_PATH = ROOT / "docs" / "STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md"
REPOSITORY_HANDOFF_PATH = ROOT / "docs" / "LLM_ADAPTER_MIRROR_HANDOFF.md"
PUBLICATION_RECEIPT_PATH = ROOT / "receipts" / "stegdeploy-image-publication.json"
READINESS_PATH = ROOT / "status" / "stegdeploy-image-publication-readiness.json"
PULL_LOG_PATH = ROOT / "receipts" / "stegdeploy-image-verification-pull.log"

EXPECTED_DIGEST = "sha256:ae309681c4b1411c39860bcb349acc5cf727b70f8876a9e61fccfbb9e767a901"
EXPECTED_PUBLICATION_RECEIPT = "d70f19a0a3afd9a34f313b3e0a4959e3343b00194c86fd85e3cdec5b3c0a7d87"
EXPECTED_PUBLICATION_RUN = 30967973138
EXPECTED_PUBLICATION_JOB = 92185969448
EXPECTED_TVC_COMMIT = "b1a817e629aff483ab80679297013b33e692b567"
EXPECTED_TVC_BLOB = "e376f2c276bda75ff497709637aac693853bf9cc"
EXPECTED_HIL_RUN = 30966031698
EXPECTED_HIL_RECEIPT = "f4d0a8b90b05017b5abf77f3c96c3b8ad3efb99eb57d9c68b90a611b928888da"
EXPECTED_PROVIDER_RUN = 30966031661
EXPECTED_SERVICE_GATEWAY_RUN = 30967405348
EXPECTED_SERVICE_GATEWAY_JOB = 92184247979
EXPECTED_SERVICE_GATEWAY_ARTIFACT = 8915257517
EXPECTED_SERVICE_GATEWAY_ARTIFACT_DIGEST = "sha256:3695622d5f8eb67c11cbfe4339fafb52569554142137af76a3a950274d1e7531"


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


def verify_hash_bound_receipt(receipt: dict, field: str = "receipt_sha256") -> None:
    material = dict(receipt)
    declared = material.pop(field, None)
    if not declared:
        fail(f"receipt missing {field}")
    actual = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if declared != actual:
        fail(f"invalid {field}: {declared} != {actual}")


def main() -> int:
    state = load_json(STATE_PATH)
    publication_task = load_json(PUBLICATION_TASK_PATH)
    sequence_task = load_json(SEQUENCE_TASK_PATH)
    service_gateway_receipt = load_json(SERVICE_GATEWAY_RECEIPT_PATH)
    publication_receipt = load_json(PUBLICATION_RECEIPT_PATH)
    readiness = load_json(READINESS_PATH)

    if state.get("schema_version") != "1.1.0":
        fail("unexpected orchestration schema")
    if state.get("repository") != "StegVerse-org/LLM-adapter":
        fail("repository identity mismatch")
    if state.get("status") != "ACTIVE_WITH_DECLARED_BLOCKERS":
        fail("repository status must preserve declared blockers")
    if state.get("task_sequence") != 2:
        fail("unexpected task sequence")
    if state.get("active_tasks") != []:
        fail("completed sequence still has active task claims")
    if state.get("idle_terminal_statement") != "end of current work task sequence 0002, no tasks running":
        fail("idle terminal statement mismatch")

    consolidation = state.get("session_consolidation") or {}
    if consolidation.get("state") != "COMPLETE" or consolidation.get("archive_ready") is not True:
        fail("session consolidation is not complete")
    if set(consolidation.get("canonical_continuation") or []) != {
        "StegVerse-org/LLM-adapter#18",
        "StegVerse-org/LLM-adapter#72",
        "StegVerse-Labs/TVC#6",
    }:
        fail("canonical continuation set mismatch")
    assert_false_authority(state.get("authority") or {}, "orchestration")

    completed = state.get("completed_tasks") or []
    publication = record(completed, "LLMA-0001-IMAGE-PUBLICATION")
    for key, expected in (
        ("state", "COMPLETE"),
        ("publication_run", EXPECTED_PUBLICATION_RUN),
        ("publication_job", EXPECTED_PUBLICATION_JOB),
        ("publication_receipt_sha256", EXPECTED_PUBLICATION_RECEIPT),
        ("image_digest", EXPECTED_DIGEST),
        ("consumer_pull_verified", True),
        ("readiness_state", "READY"),
        ("evidence_only_changes_rebuild_image", False),
    ):
        if publication.get(key) != expected:
            fail(f"publication completed-task {key} mismatch")
    if publication.get("scheduler_owner") != "StegVerse-Labs/StegVerse-Healer":
        fail("publication scheduler owner mismatch")

    hil = record(completed, "LLMA-0001-HIL-CYCLE")
    if hil.get("state") != "COMPLETE" or hil.get("workflow_run") != EXPECTED_HIL_RUN:
        fail("HIL full-cycle evidence mismatch")
    if hil.get("receipt_sha256") != EXPECTED_HIL_RECEIPT:
        fail("HIL receipt evidence mismatch")
    if hil.get("persistent_deployment_proven") is not False:
        fail("ephemeral HIL proof is represented as persistent deployment")

    goal8 = record(completed, "LLMA-0001-GOAL8")
    if goal8.get("state") != "COMPLETE" or goal8.get("workflow_run") != EXPECTED_PROVIDER_RUN:
        fail("provider usage validation evidence mismatch")
    if goal8.get("python_versions") != ["3.9", "3.11", "3.12"]:
        fail("provider usage validation matrix mismatch")
    if goal8.get("authority_effect") is not False:
        fail("provider usage validation grants authority")

    sequence = record(completed, "LLMA-SEQUENCE-0001-RELEASE-015")
    if sequence.get("state") != "COMPLETE":
        fail("sequence release is not complete")
    if sequence.get("service_gateway_run") != EXPECTED_SERVICE_GATEWAY_RUN:
        fail("Service Gateway run mismatch in completed state")
    if sequence.get("service_gateway_artifact") != EXPECTED_SERVICE_GATEWAY_ARTIFACT:
        fail("Service Gateway artifact mismatch in completed state")
    if sequence.get("service_gateway_artifact_digest") != EXPECTED_SERVICE_GATEWAY_ARTIFACT_DIGEST:
        fail("Service Gateway artifact digest mismatch in completed state")
    if sequence.get("persistent_deployment_proven") is not False:
        fail("Service Gateway CI proof is represented as persistent deployment")

    live = record(state.get("queued_exclusive_tasks") or [], "LLMA-0002-LIVE-PROVIDER")
    if live.get("owner") != "issue/18" or live.get("state") != "BLOCKED":
        fail("live-provider task owner or state mismatch")
    if live.get("execution_class") != "EXCLUSIVE":
        fail("live-provider execution class mismatch")
    if live.get("blocked_until") != "all authority-bound blockers are cleared":
        fail("live-provider task retains a stale sequence barrier")
    blockers = set(live.get("external_blockers") or [])
    if blockers != {
        "authorized provider configuration and scoped execution grant",
        "persistent endpoint",
        "authenticated Master Records custody configuration",
    }:
        fail("live-provider blocker set mismatch")
    dependency_text = "\n".join(live.get("completed_dependency_evidence") or [])
    for required in (
        EXPECTED_DIGEST,
        str(EXPECTED_PUBLICATION_RUN),
        str(EXPECTED_HIL_RUN),
        str(EXPECTED_PROVIDER_RUN),
        str(EXPECTED_SERVICE_GATEWAY_RUN),
    ):
        if required not in dependency_text:
            fail(f"completed dependency evidence missing {required}")

    observers = state.get("machine_owned_observers") or []
    healer = record(observers, "LLMA-HEALER-PUBLICATION-RELAY", "observer_id")
    if healer.get("owner") != "StegVerse-Labs/StegVerse-Healer":
        fail("Healer relay owner mismatch")
    if healer.get("state") != "BLOCKED" or healer.get("observed_result") != "HTTP 403":
        fail("Healer relay blocker mismatch")
    monitor = record(observers, "LLMA-LIVE-ACTIVATION-MONITOR", "observer_id")
    if monitor.get("state") != "PENDING" or monitor.get("authority_effect") is not False:
        fail("live activation monitor posture mismatch")

    if publication_task.get("state") != "COMPLETE" or publication_task.get("claimant") is not None:
        fail("publication task claim is not released")
    publication_validation = publication_task.get("validation") or {}
    for key, expected in (
        ("publication_run", EXPECTED_PUBLICATION_RUN),
        ("publication_job", EXPECTED_PUBLICATION_JOB),
        ("publication_state", "PUBLISHED"),
        ("publication_receipt_sha256", EXPECTED_PUBLICATION_RECEIPT),
        ("image_digest", EXPECTED_DIGEST),
        ("consumer_pull_verified", True),
        ("readiness_state", "READY"),
    ):
        if publication_validation.get(key) != expected:
            fail(f"publication task validation {key} mismatch")

    if sequence_task.get("state") != "COMPLETE" or sequence_task.get("claimant") is not None:
        fail("sequence task claim is not released")
    if sequence_task.get("archive_dependency") != "SATISFIED; all unique session requirements and evidence are durably installed or transferred.":
        fail("sequence archive dependency is not satisfied")
    if sequence_task.get("manual_user_action_required") is not False or sequence_task.get("authority_effect") is not False:
        fail("sequence task assigns manual work or authority")

    if publication_receipt.get("schema") != "stegdeploy.image-publication.v2":
        fail("publication receipt schema mismatch")
    if publication_receipt.get("state") != "PUBLISHED" or publication_receipt.get("blockers") != []:
        fail("publication receipt is not zero-blocker PUBLISHED")
    for key, expected in (
        ("digest", EXPECTED_DIGEST),
        ("receipt_sha256", EXPECTED_PUBLICATION_RECEIPT),
        ("publication_run_id", str(EXPECTED_PUBLICATION_RUN)),
        ("consumer_pull_verified", True),
        ("repository_retained", True),
    ):
        if publication_receipt.get(key) != expected:
            fail(f"publication receipt {key} mismatch")
    verify_hash_bound_receipt(publication_receipt)

    if readiness.get("state") != "READY" or readiness.get("blockers") != []:
        fail("publication readiness is not READY")
    if readiness.get("observed_digest") != EXPECTED_DIGEST or readiness.get("consumer_pull_verified") is not True:
        fail("publication readiness does not match retained receipt")
    assert_false_authority({
        "provider": readiness.get("provider_execution_authorized"),
        "deployment": readiness.get("persistent_deployment_authorized"),
        "custody": readiness.get("custody_authorized"),
        "site": readiness.get("site_activation_authorized"),
    }, "publication readiness")

    if not PULL_LOG_PATH.is_file() or EXPECTED_DIGEST not in PULL_LOG_PATH.read_text(encoding="utf-8"):
        fail("fresh consumer pull log is missing final digest")

    if service_gateway_receipt.get("schema") != "stegverse.service_gateway.activation_proof.v1":
        fail("Service Gateway proof schema mismatch")
    if service_gateway_receipt.get("result") != "PASS":
        fail("Service Gateway proof is not PASS")
    if service_gateway_receipt.get("boundary") != "ephemeral GitHub-hosted activation proof; not persistent public hosting":
        fail("Service Gateway boundary mismatch")
    main_activation = service_gateway_receipt.get("main_activation") or {}
    for key, expected in (
        ("workflow_run", EXPECTED_SERVICE_GATEWAY_RUN),
        ("workflow_job", EXPECTED_SERVICE_GATEWAY_JOB),
        ("artifact_id", EXPECTED_SERVICE_GATEWAY_ARTIFACT),
        ("artifact_digest", EXPECTED_SERVICE_GATEWAY_ARTIFACT_DIGEST),
        ("receipt_schema", "HIL-RECEIVER-RECEIPT-v2"),
        ("receipt_hash_validated", True),
        ("durable_receipt_file_observed", True),
        ("duplicate_receipt_semantically_equal", True),
        ("duplicate_submission_id_equal", True),
        ("duplicate_receipt_sha256_equal", True),
        ("final_enforcement_passed", True),
    ):
        if main_activation.get(key) != expected:
            fail(f"Service Gateway proof {key} mismatch")
    assert_false_authority(service_gateway_receipt.get("authority") or {}, "Service Gateway proof")

    publication_workflow = PUBLICATION_WORKFLOW_PATH.read_text(encoding="utf-8")
    trigger_section = publication_workflow.split("permissions:", 1)[0]
    for required in (
        "workflow_dispatch:",
        "StegVerse-Labs/StegVerse-Healer",
        "Dockerfile",
        "pyproject.toml",
        "llm_adapter/**",
        "scripts/container-entrypoint.sh",
        "compose.stegdeploy.yaml",
        ".github/workflows/stegdeploy-image.yml",
    ):
        if required not in trigger_section:
            fail(f"publication trigger missing {required}")
    for forbidden in (
        "docs/STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md",
        "receipts/stegdeploy-image-publication.json",
        "status/stegdeploy-image-publication-readiness.json",
        "scripts/check_stegdeploy_image_publication_readiness.py",
        "schedule:",
    ):
        if forbidden in trigger_section:
            fail(f"publication trigger contains forbidden non-runtime path or schedule: {forbidden}")

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
    if 'receipt_hash = material.pop("receipt_sha256")' not in gateway_test:
        fail("Service Gateway test does not remove receipt_sha256")
    if 'material.pop("receiver_signature")' in gateway_test:
        fail("Service Gateway test excludes receiver_signature from v2 receipt hash")

    publication_handoff = PUBLICATION_HANDOFF_PATH.read_text(encoding="utf-8")
    repository_handoff = REPOSITORY_HANDOFF_PATH.read_text(encoding="utf-8")
    for path_name, text in (
        ("publication handoff", publication_handoff),
        ("repository handoff", repository_handoff),
    ):
        for required in (
            EXPECTED_DIGEST,
            EXPECTED_PUBLICATION_RECEIPT,
            str(EXPECTED_PUBLICATION_RUN),
            "StegVerse-org/LLM-adapter#18",
        ):
            if required not in text:
                fail(f"{path_name} missing {required}")
    if "ARCHIVE THIS SESSION" not in repository_handoff:
        fail("repository handoff does not record archive disposition")

    print("LLM_ADAPTER_ORCHESTRATION_STATE_PASS")
    print("active_tasks=0 sequence_0002=COMPLETE session_consolidation=COMPLETE")
    print(f"stable_publication_run={EXPECTED_PUBLICATION_RUN} digest={EXPECTED_DIGEST}")
    print(f"hil_run={EXPECTED_HIL_RUN} provider_validation_run={EXPECTED_PROVIDER_RUN}")
    print(f"service_gateway_run={EXPECTED_SERVICE_GATEWAY_RUN} boundary=EPHEMERAL_CI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
