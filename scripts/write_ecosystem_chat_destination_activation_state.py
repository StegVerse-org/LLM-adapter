#!/usr/bin/env python3
"""Write the non-authorizing Ecosystem Chat destination activation state.

This projection follows the canonical sovereign execution path. Repository/source
readiness is reported separately from live execution evidence and can never by itself
satisfy activation. Historical Render topology is intentionally not consulted.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "ecosystem-chat-destination-activation-state.json"
SOVEREIGN_STATE = ROOT / "data" / "ecosystem-chat-sovereign-orchestration-state.json"
CARRIER_TASK = ROOT / "tasks" / "LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json"
LIVE_RECEIPT = ROOT / "receipts" / "ecosystem-chat-live-activation.verified.json"
SOVEREIGN_RECEIPT = ROOT / "receipts" / "ecosystem-chat-sovereign-activation.verified.json"


def env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def canonical_sha256(value: dict[str, Any], *, omit: str | None = None) -> str:
    binding = dict(value)
    if omit:
        binding.pop(omit, None)
    encoded = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_contract_markers() -> dict[str, bool]:
    state = load_json(SOVEREIGN_STATE) or {}
    task = load_json(CARRIER_TASK) or {}
    authority = task.get("authority_contract") if isinstance(task.get("authority_contract"), dict) else {}
    validation = task.get("validation_evidence") if isinstance(task.get("validation_evidence"), dict) else {}
    completed_transport = state.get("completed_transport_evidence_adapter")
    completed_transport = completed_transport if isinstance(completed_transport, dict) else {}

    return {
        "canonical_model_runtime_released": (
            isinstance(state.get("canonical_micro_node_runtime"), dict)
            and state["canonical_micro_node_runtime"].get("state") == "COMPLETE_RELEASED"
        ),
        "transport_evidence_adapter_released": completed_transport.get("state") == "COMPLETE_RELEASED",
        "carrier_executor_released": task.get("state") == "COMPLETE_RELEASED",
        "carrier_executor_validation_pass": validation.get("validation_matrix") == "PASS",
        "credential_requirement_none": authority.get("credential_requirement_for_local_model") == "NONE",
        "github_token_required_false": authority.get("github_token_required") is False,
        "github_actions_production_role_false": authority.get("github_actions_production_role") is False,
        "execution_authority_false": authority.get("execution_authority") is False,
        "model_output_authority_false": authority.get("model_output_authority") is False,
    }


def verified_live_receipt(value: dict[str, Any] | None) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return False, ["verified_live_receipt_missing"]
    if value.get("schema") != "stegverse.ecosystem_chat.live_activation.v1":
        errors.append("verified_live_receipt_schema")
    if value.get("state") != "VERIFIED":
        errors.append("verified_live_receipt_state")
    if value.get("blockers") != []:
        errors.append("verified_live_receipt_blockers")
    for flag in ("authority_granted", "publication_authorized", "repository_mutation_authorized"):
        if value.get(flag) is not False:
            errors.append(f"verified_live_receipt_{flag}")
    expected = value.get("result_sha256")
    if not isinstance(expected, str) or expected != canonical_sha256(value, omit="result_sha256"):
        errors.append("verified_live_receipt_hash")
    return not errors, errors


def verified_sovereign_receipt(value: dict[str, Any] | None) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return False, ["verified_sovereign_receipt_missing"]
    if value.get("schema") != "stegverse.ecosystem_chat.sovereign_activation_projection.v1":
        errors.append("verified_sovereign_receipt_schema")
    if value.get("state") != "VERIFIED":
        errors.append("verified_sovereign_receipt_state")
    predicates = value.get("predicates") if isinstance(value.get("predicates"), dict) else {}
    required = (
        "real_model_process_observed",
        "private_endpoint_only",
        "ephemeral_e1_e2_execution_observed",
        "measured_usage_persisted",
        "provider_usage_reconstruction_pass",
        "transition_reconstruction_pass",
        "same_execution",
        "persistent_conversational_runtime_ready",
    )
    if any(predicates.get(key) is not True for key in required):
        errors.append("verified_sovereign_receipt_predicates")
    credential = value.get("credential_boundary") if isinstance(value.get("credential_boundary"), dict) else {}
    if credential.get("credential_authority") != "TV/TVC" or credential.get("credential_requirement") != "NONE":
        errors.append("verified_sovereign_receipt_credential_boundary")
    if credential.get("github_token_required") is not False or credential.get("github_actions_activation_role") is not False:
        errors.append("verified_sovereign_receipt_hosted_authority")
    authority = value.get("authority_boundary") if isinstance(value.get("authority_boundary"), dict) else {}
    if any(authority.get(flag) is not False for flag in (
        "projection_grants_activation_authority",
        "projection_grants_execution_authority",
        "projection_grants_custody_authority",
        "projection_grants_release_authority",
        "projection_grants_publication_authority",
    )):
        errors.append("verified_sovereign_receipt_authority")
    expected = value.get("projection_sha256")
    if not isinstance(expected, str) or expected != canonical_sha256(value, omit="projection_sha256"):
        errors.append("verified_sovereign_receipt_hash")
    return not errors, errors


def sovereign_predicates(value: dict[str, Any] | None, verified: bool) -> dict[str, bool]:
    if not verified or not isinstance(value, dict):
        return {
            "runtime_service_observed": False,
            "real_provider_used": False,
            "local_usage_receipt_valid": False,
            "provider_usage_custody_recorded": False,
            "provider_usage_reconstructability_pass": False,
            "transition_custody_recorded": False,
            "transition_reconstructability_pass": False,
            "provider_usage_authority_false": False,
        }
    provider = value.get("provider_usage") if isinstance(value.get("provider_usage"), dict) else {}
    transition = value.get("transition") if isinstance(value.get("transition"), dict) else {}
    runtime = value.get("runtime") if isinstance(value.get("runtime"), dict) else {}
    predicates = value.get("predicates") if isinstance(value.get("predicates"), dict) else {}
    return {
        "runtime_service_observed": runtime.get("persistent_conversational_runtime_ready") is True,
        "real_provider_used": predicates.get("ephemeral_e1_e2_execution_observed") is True,
        "local_usage_receipt_valid": provider.get("measured") is True and isinstance(provider.get("event_sha256"), str),
        "provider_usage_custody_recorded": provider.get("custody_recorded") is True and provider.get("authority_granted") is False,
        "provider_usage_reconstructability_pass": provider.get("reconstructability") == "PASS",
        "transition_custody_recorded": transition.get("custody_recorded") is True,
        "transition_reconstructability_pass": transition.get("reconstructability") == "PASS",
        "provider_usage_authority_false": provider.get("authority_granted") is False,
    }


def live_predicates(live: dict[str, Any] | None, verified: bool) -> dict[str, bool]:
    evidence = live.get("evidence") if verified and isinstance(live, dict) else {}
    evidence = evidence if isinstance(evidence, dict) else {}
    health = evidence.get("health") if isinstance(evidence.get("health"), dict) else {}
    chat = evidence.get("chat") if isinstance(evidence.get("chat"), dict) else {}
    transition = evidence.get("transition") if isinstance(evidence.get("transition"), dict) else {}
    provider = chat.get("provider") if isinstance(chat.get("provider"), dict) else {}
    local_usage = chat.get("provider_usage_submission") if isinstance(chat.get("provider_usage_submission"), dict) else {}
    custody = chat.get("master_records_usage_submission") if isinstance(chat.get("master_records_usage_submission"), dict) else {}
    authority = chat.get("authority") if isinstance(chat.get("authority"), dict) else {}

    return {
        "runtime_service_observed": bool(verified and health.get("status") == "ok"),
        "real_provider_used": bool(verified and provider.get("used") is True),
        "local_usage_receipt_valid": bool(
            verified
            and local_usage
            and local_usage.get("custody_recorded") is False
            and isinstance(local_usage.get("event_sha256"), str)
        ),
        "provider_usage_custody_recorded": bool(
            verified
            and custody.get("custody_recorded") is True
            and custody.get("authority_granted") is False
        ),
        "provider_usage_reconstructability_pass": bool(
            verified and custody.get("reconstructability") == "PASS"
        ),
        "transition_custody_recorded": bool(
            verified and transition.get("master_record_status") == "RECORDED"
        ),
        "transition_reconstructability_pass": bool(
            verified and transition.get("reconstruction_status") == "PASS"
        ),
        "provider_usage_authority_false": bool(
            verified and authority.get("provider_usage_grants_authority") is False
        ),
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
    current_main_validation = bool(commit_sha and run_id and current_main_context and validation_succeeded)

    source_markers = source_contract_markers()
    source_contract_ready = all(source_markers.values())
    live = load_json(LIVE_RECEIPT)
    live_verified, live_errors = verified_live_receipt(live)
    sovereign = load_json(SOVEREIGN_RECEIPT)
    sovereign_verified, sovereign_errors = verified_sovereign_receipt(sovereign)
    if sovereign_verified:
        observed = sovereign_predicates(sovereign, True)
        evidence_mode = "SOVEREIGN_PARENT_PROJECTION"
    else:
        observed = live_predicates(live, live_verified)
        evidence_mode = "LEGACY_LIVE_ACTIVATION_RECEIPT" if live_verified else "NONE"

    # Compatibility gate names are retained because Site consumes them. Their current
    # semantics are sovereign-runtime evidence, not a hosted/Render topology declaration.
    gates = {
        "destination_current_main_validation": {
            "complete": current_main_validation,
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
            "complete": observed["runtime_service_observed"],
            "owner": "StegVerse-Labs/.github#60 -> StegVerse-Labs/TVC -> StegVerse-org/LLM-adapter",
            "compatibility_name": True,
            "current_semantics": "canonical_sovereign_runtime_service_observed",
            "source_contract_ready": source_contract_ready,
        },
        "automatic_provider_usage_submission": {
            "complete": bool(
                observed["real_provider_used"]
                and observed["local_usage_receipt_valid"]
                and observed["provider_usage_custody_recorded"]
            ),
            "owner": "StegVerse-org/LLM-adapter -> master-records/orchestration",
            "current_semantics": "measured_provider_usage_emitted_and_custodied_in_verified_same_execution",
            "source_contract_ready": source_contract_ready,
        },
        "retrieval_and_provider_usage_receipts": {
            "complete": bool(
                observed["real_provider_used"]
                and observed["local_usage_receipt_valid"]
                and observed["provider_usage_custody_recorded"]
                and observed["provider_usage_reconstructability_pass"]
                and observed["transition_custody_recorded"]
                and observed["transition_reconstructability_pass"]
                and observed["provider_usage_authority_false"]
            ),
            "owner": "StegVerse-org/LLM-adapter + master-records/orchestration",
            "current_semantics": "verified_provider_usage_and_transition_same_execution_evidence",
            "source_contract_ready": source_contract_ready,
        },
    }

    complete = all(item["complete"] for item in gates.values())
    state = "DESTINATION_ACTIVATION_EVIDENCE_COMPLETE" if complete else "DESTINATION_ACTIVATION_PENDING_EXTERNAL_EVIDENCE"
    payload: dict[str, Any] = {
        "schema_version": "1.2.0",
        "record_type": "ecosystem_chat_destination_activation_state",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": repository,
        "commit_sha": commit_sha,
        "event_name": event_name,
        "workflow_run_id": run_id,
        "state": state,
        "manual_user_action_required": False,
        "canonical_execution_path": "STEGVERSE_LOCAL_PRIVATE_ENDPOINT",
        "source_contract": {
            "ready": source_contract_ready,
            "markers": source_markers,
            "source_readiness_is_activation": False,
        },
        "gates": gates,
        "activation_evidence_mode": evidence_mode,
        "live_receipt": {
            "present": live is not None,
            "verified": live_verified,
            "validation_errors": live_errors,
            "path": str(LIVE_RECEIPT.relative_to(ROOT)),
        },
        "sovereign_parent_projection": {
            "present": sovereign is not None,
            "verified": sovereign_verified,
            "validation_errors": sovereign_errors,
            "path": str(SOVEREIGN_RECEIPT.relative_to(ROOT)),
        },
        "observed_live_predicates": observed,
        "superseded_topology": {
            "render_required": False,
            "github_models_required": False,
            "github_actions_production_role": False,
            "third_party_runtime_required": False,
        },
        "credential_boundary": {
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "github_token_required": False,
        },
        "authority_boundary": {
            "deployment_authorized": False,
            "mutation_authorized": False,
            "custody_claimed": False,
            "publication_authorized": False,
            "execution_authorized": False,
        },
    }
    payload["state_sha256"] = canonical_sha256(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"ECOSYSTEM CHAT DESTINATION STATE: {state}")
    print(f"SOVEREIGN SOURCE CONTRACT READY: {source_contract_ready}")
    print(f"VERIFIED LIVE RECEIPT: {live_verified}")\n    print(f"VERIFIED SOVEREIGN PARENT PROJECTION: {sovereign_verified}")
    print(f"Receipt: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
