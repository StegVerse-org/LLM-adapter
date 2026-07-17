#!/usr/bin/env python3
"""Write the non-authorizing Ecosystem Chat destination activation state.

Repository validation, declared production topology, and the retained live receipt are
converted into machine-owned gates. No environment secret value is copied into state.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "ecosystem-chat-destination-activation-state.json"
BLUEPRINT = ROOT / "render-production.yaml"
LIVE_RECEIPT = ROOT / "receipts" / "ecosystem-chat-live-activation.verified.json"


def env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def blueprint_markers() -> dict[str, bool]:
    text = BLUEPRINT.read_text(encoding="utf-8") if BLUEPRINT.exists() else ""
    return {
        "gateway_declared": "name: stegverse-ecosystem-chat-gateway" in text,
        "custody_private_service_declared": "type: pserv" in text and "name: stegverse-master-records-custody" in text,
        "custody_durable": "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS" in text and 'value: "true"' in text,
        "custody_auth_generated": "MASTER_RECORDS_AUTH_TOKEN" in text and "generateValue: true" in text,
        "custody_receipt_key_generated": "MASTER_RECORDS_RECEIPT_KEY" in text and "generateValue: true" in text,
        "private_hostport_bound": "STEGVERSE_MASTER_RECORDS_HOSTPORT" in text and "property: hostport" in text,
        "shared_token_bound": "envVarKey: MASTER_RECORDS_AUTH_TOKEN" in text,
        "provider_enabled": "STEGVERSE_PROVIDER_ENABLED" in text,
        "mutation_disabled": "STEGVERSE_EXTERNAL_MUTATION_ENABLED" in text and 'value: "false"' in text,
    }


def main() -> int:
    repository = env("GITHUB_REPOSITORY") or "StegVerse-org/LLM-adapter"
    commit_sha = env("GITHUB_SHA")
    event_name = env("GITHUB_EVENT_NAME")
    run_id = env("GITHUB_RUN_ID")
    git_ref = env("GITHUB_REF")
    validation_job_status = env("VALIDATION_JOB_STATUS")

    current_main_context = git_ref == "refs/heads/main"
    validation_succeeded = validation_job_status == "success"
    local_validation_observed = bool(commit_sha and run_id and current_main_context and validation_succeeded)

    markers = blueprint_markers()
    topology_complete = all(markers.values())
    live = load_json(LIVE_RECEIPT)
    live_verified = bool(live and live.get("state") == "VERIFIED" and live.get("blockers") == [])
    live_evidence = live.get("evidence", {}) if live_verified else {}
    health = live_evidence.get("health", {}) if isinstance(live_evidence, dict) else {}
    chat = live_evidence.get("chat", {}) if isinstance(live_evidence, dict) else {}
    transition = live_evidence.get("transition", {}) if isinstance(live_evidence, dict) else {}
    usage_custody = chat.get("master_records_usage_submission", {}) if isinstance(chat, dict) else {}

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
            "complete": topology_complete and live_verified and health.get("status") == "ok",
            "owner": repository,
            "automation": "render-production.yaml and deployment platform",
            "declared_topology_complete": topology_complete,
        },
        "automatic_provider_usage_submission": {
            "complete": topology_complete,
            "owner": repository,
            "automation": "private Render service binding and llm_adapter/master_records_usage_submission.py",
        },
        "retrieval_and_provider_usage_receipts": {
            "complete": bool(
                live_verified
                and usage_custody.get("custody_recorded") is True
                and usage_custody.get("reconstructability") == "PASS"
                and transition.get("master_record_status") == "RECORDED"
                and transition.get("reconstruction_status") == "PASS"
            ),
            "owner": repository,
            "automation": ".github/workflows/ecosystem-chat-live-activation.yml",
        },
    }

    complete = all(item["complete"] for item in gates.values())
    state = "DESTINATION_ACTIVATION_EVIDENCE_COMPLETE" if complete else "DESTINATION_ACTIVATION_PENDING_EXTERNAL_EVIDENCE"
    payload = {
        "schema_version": "1.1.0",
        "record_type": "ecosystem_chat_destination_activation_state",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": repository,
        "commit_sha": commit_sha,
        "event_name": event_name,
        "workflow_run_id": run_id,
        "state": state,
        "manual_user_action_required": False,
        "gates": gates,
        "production_topology": markers,
        "live_receipt": {
            "present": live is not None,
            "verified": live_verified,
            "path": str(LIVE_RECEIPT.relative_to(ROOT)),
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
