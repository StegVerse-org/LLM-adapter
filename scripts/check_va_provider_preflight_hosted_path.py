#!/usr/bin/env python3
"""Validate the hosted VA provider-preflight admission path without executing a provider."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/va-claim-assistant-provider-preflight.yml"
TASK = ROOT / "tasks/VACP-PREFLIGHT-HOSTED-EXECUTION-008.json"
SOURCE_COMMIT = "e3865e79662529e07d27199235431056d127ea63"
SOURCE_BLOB_SHA = "e9bb981fbd4afea934c8b800a0f70f6b6ddaf61c"
SOURCE = (
    ROOT
    / "vendor/tvc"
    / SOURCE_COMMIT
    / "issue_va_ephemeral_route_admission.py"
)
PRIVATE_REUSABLE_CALL = (
    "uses: StegVerse-Labs/TVC/.github/workflows/"
    "va-route-ephemeral-admission.yml@"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"VA_PROVIDER_PREFLIGHT_HOSTED_PATH_FAIL:{message}")


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode("utf-8")
    return hashlib.sha1(header + content).hexdigest()


def load_source_module():
    spec = importlib.util.spec_from_file_location("vendored_va_tvc_admission", SOURCE)
    require(spec is not None and spec.loader is not None, "vendored_source_import_spec_missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_deterministic_source_shape() -> None:
    module = load_source_module()
    args = SimpleNamespace(
        route="service_connection",
        caller_repository="StegVerse-org/LLM-adapter",
        caller_commit="1" * 40,
        source_registry_commit="2" * 40,
        source_registry_blob_sha="3" * 40,
        answer_schema_commit="4" * 40,
        answer_receipt_hash="5" * 64,
        dispatch_receipt_hash="6" * 64,
        purpose="SOURCE_GROUNDED_VA_CLAIM_GUIDANCE",
        scope="PUBLIC_SOURCE_SERVICE_CONNECTION_PROCEDURAL_GUIDANCE",
        workflow_run_id="123456",
        workflow_run_attempt="1",
        output="unused.json",
    )
    now = datetime(2026, 8, 6, 15, 43, tzinfo=timezone.utc)
    receipt = module.build_receipt(args, now=now)
    require(receipt["state"] == "ADMITTED_PENDING_PROVIDER_EXECUTION", "admission_state")
    require(receipt["issuer"]["repository"] == "StegVerse-Labs/TVC", "issuer_repository")
    require(
        receipt["issuer"]["workflow"]
        == ".github/workflows/va-route-ephemeral-admission.yml",
        "issuer_workflow",
    )
    require(receipt["validity"]["lifetime_seconds"] == 900, "admission_lifetime")
    require(receipt["validity"]["single_use"] is True, "admission_single_use")
    require(receipt["provider_execution_requested"] is False, "provider_request_boundary")
    require(receipt["provider_execution_observed"] is False, "provider_execution_boundary")
    require(not any(receipt["authority_flags"].values()), "authority_flags")
    require(receipt["activation_effect"] is False, "activation_effect")
    require(receipt["receipt_hash"] == module.canonical_hash(receipt), "admission_hash")


def main() -> int:
    require(WORKFLOW.is_file(), "workflow_missing")
    require(TASK.is_file(), "task_missing")
    require(SOURCE.is_file(), "vendored_source_missing")
    require(git_blob_sha(SOURCE) == SOURCE_BLOB_SHA, "vendored_source_blob_mismatch")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require(PRIVATE_REUSABLE_CALL not in workflow, "private_reusable_workflow_call_present")
    require(str(SOURCE.relative_to(ROOT)) in workflow, "vendored_source_not_bound")
    require(SOURCE_COMMIT in workflow, "source_commit_not_bound")
    require(SOURCE_BLOB_SHA in workflow, "source_blob_not_bound")
    require("private_cross_organization_reusable_workflow_called': False" in workflow, "private_call_boundary_missing")
    require("va-route-ephemeral-admission-provenance.json" in workflow, "provenance_sidecar_missing")
    require("provenance_sha256" in workflow, "provenance_hash_missing")
    require("provider_permission_requested': False" in workflow, "provider_permission_boundary_missing")
    require("provider_execution_observed': False" in workflow, "provider_execution_boundary_missing")
    require("authority_effect': False" in workflow, "authority_boundary_missing")
    require("activation_effect': False" in workflow, "activation_boundary_missing")
    require("models: read" not in workflow.lower(), "provider_permission_requested")
    require("models:read" not in workflow.lower(), "provider_permission_requested_compact")
    require("retention-days: 30" in workflow, "preflight_artifact_retention_missing")
    require("retention-days: 1" in workflow, "admission_artifact_retention_missing")

    task = json.loads(TASK.read_text(encoding="utf-8"))
    require(task["task_id"] == "VACP-PREFLIGHT-HOSTED-EXECUTION-008", "task_id")
    require(task["state"] in {"CLAIMED", "COMPLETE", "BLOCKED"}, "task_state")
    require(task["authority_effect"] is False, "task_authority_effect")
    require(task["activation_effect"] is False, "task_activation_effect")
    require(task["manual_user_action_required"] is False, "manual_user_action")
    require(
        "Do not request models:read or call a provider."
        in task["collision_boundaries"],
        "task_provider_collision_boundary",
    )

    verify_deterministic_source_shape()
    print(
        "VA_PROVIDER_PREFLIGHT_HOSTED_PATH_PASS:"
        f"{SOURCE_COMMIT}:{SOURCE_BLOB_SHA}:{task['state']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
