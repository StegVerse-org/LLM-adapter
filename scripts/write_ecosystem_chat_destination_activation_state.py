#!/usr/bin/env python3
"""Write a non-authorizing Ecosystem Chat destination activation state.

This record converts repository-local validation and external deployment prerequisites
into machine-owned gates. It never grants deployment, mutation, custody, publication,
or execution authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "ecosystem-chat-destination-activation-state.json"


def env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def main() -> int:
    repository = env("GITHUB_REPOSITORY") or "StegVerse-org/LLM-adapter"
    commit_sha = env("GITHUB_SHA")
    event_name = env("GITHUB_EVENT_NAME")
    run_id = env("GITHUB_RUN_ID")
    git_ref = env("GITHUB_REF")
    validation_job_status = env("VALIDATION_JOB_STATUS")
    deployment_url = env("STEGVERSE_GATEWAY_BASE_URL")
    custody_url = env("STEGVERSE_CUSTODY_BASE_URL")
    auth_configured = bool(env("MASTER_RECORDS_AUTH_TOKEN"))

    current_main_context = git_ref == "refs/heads/main"
    validation_succeeded = validation_job_status == "success"
    local_validation_observed = bool(
        commit_sha
        and run_id
        and current_main_context
        and validation_succeeded
    )
    deployment_configured = bool(deployment_url)
    custody_submission_configured = bool(custody_url and auth_configured)

    gates = {
        "destination_current_main_validation": {
            "complete": local_validation_observed,
            "owner": repository,
            "automation": ".github/workflows/validate.yml",
            "evidence": {
                "commit_sha_present": bool(commit_sha),
                "workflow_run_id_present": bool(run_id),
                "git_ref": git_ref,
                "current_main_context": current_main_context,
                "validation_job_status": validation_job_status,
                "validation_succeeded": validation_succeeded,
            },
        },
        "same_origin_authenticated_deployment": {
            "complete": deployment_configured,
            "owner": repository,
            "automation": "render-production.yaml and deployment platform",
        },
        "automatic_provider_usage_submission": {
            "complete": custody_submission_configured,
            "owner": repository,
            "automation": "llm_adapter/provider_usage_submission.py",
        },
        "retrieval_and_provider_usage_receipts": {
            "complete": False,
            "owner": repository,
            "automation": "deployed gateway runtime",
        },
    }

    complete = all(item["complete"] for item in gates.values())
    state = "DESTINATION_ACTIVATION_EVIDENCE_COMPLETE" if complete else "DESTINATION_ACTIVATION_PENDING_EXTERNAL_EVIDENCE"

    payload = {
        "schema_version": "1.0.1",
        "record_type": "ecosystem_chat_destination_activation_state",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": repository,
        "commit_sha": commit_sha,
        "event_name": event_name,
        "workflow_run_id": run_id,
        "state": state,
        "manual_user_action_required": False,
        "gates": gates,
        "external_configuration": {
            "gateway_base_url_present": deployment_configured,
            "custody_base_url_present": bool(custody_url),
            "custody_auth_present": auth_configured,
        },
        "authority_boundary": {
            "deployment_authorized": False,
            "mutation_authorized": False,
            "custody_claimed": False,
            "publication_authorized": False,
            "execution_authorized": False,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload["state_sha256"] = hashlib.sha256(canonical).hexdigest()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"ECOSYSTEM CHAT DESTINATION STATE: {state}")
    print(f"Receipt: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
