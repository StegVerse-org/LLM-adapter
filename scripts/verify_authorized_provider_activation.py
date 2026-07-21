#!/usr/bin/env python3
"""Verify the real provider -> usage -> custody -> reconstruction runtime slice.

This verifier accepts only a genuinely used provider response. Deterministic fallback
text, local persistence without custody, or a response that upgrades authority fails
closed. The generated receipt never includes credentials or provider response text.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "receipts" / "ecosystem-chat-authorized-provider-activation.latest.json"
BASE_URL = os.getenv("STEGVERSE_PROVIDER_ACTIVATION_BASE_URL", "http://127.0.0.1:8110").rstrip("/")


def canonical_sha256(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def fetch_json(url: str, *, data: dict | None = None, headers: dict[str, str] | None = None) -> dict:
    body = None if data is None else json.dumps(data).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers=headers or {},
        method="POST" if body is not None else "GET",
    )
    with urlopen(request, timeout=35) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"HTTP {response.status} from {url}")
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object from {url}")
    return value


def wait_for_health() -> dict:
    last_error = "unobserved"
    for _ in range(60):
        try:
            health = fetch_json(f"{BASE_URL}/health")
            if health.get("status") == "ok":
                return health
        except (OSError, URLError, HTTPError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(1)
    raise RuntimeError(f"authorized provider gateway health not ready: {last_error}")


def validate_runtime_result(health: dict, response: dict, identity: dict) -> list[str]:
    blockers: list[str] = []

    if health.get("governed_provider_enabled") is not True:
        blockers.append("provider_not_enabled")
    if health.get("master_records_submission_enabled") is not True:
        blockers.append("transition_custody_not_enabled")
    if health.get("provider_output_is_authority") is not False:
        blockers.append("health_provider_authority_boundary_invalid")

    for key in ("transition_id", "run_id", "event_id", "origin_manifest_id"):
        if response.get(key) != identity[key]:
            blockers.append(f"response_{key}_mismatch")

    provider = response.get("provider") or {}
    if provider.get("used") is not True:
        blockers.append("real_provider_not_used")
    if provider.get("status") != "USED":
        blockers.append("provider_status_not_used")
    if not provider.get("provider_receipt_id"):
        blockers.append("provider_receipt_missing")
    if provider.get("fallback_required") is not False:
        blockers.append("provider_fallback_used")

    local_usage = response.get("provider_usage_submission") or {}
    if local_usage.get("schema") != "stegverse.usage.internal_submission.v1":
        blockers.append("provider_usage_persistence_missing")
    if not local_usage.get("measurement_id") or not local_usage.get("event_sha256"):
        blockers.append("provider_usage_identity_missing")
    if local_usage.get("authority_granted") is not False:
        blockers.append("provider_usage_authority_escalation")
    if local_usage.get("custody_recorded") is not False:
        blockers.append("local_usage_misclassified_as_custody")

    usage_custody = response.get("master_records_usage_submission") or {}
    if usage_custody.get("status") != "CUSTODY_RECORDED":
        blockers.append("provider_usage_custody_not_recorded")
    if usage_custody.get("custody_recorded") is not True:
        blockers.append("provider_usage_custody_flag_false")
    if not usage_custody.get("receipt_id"):
        blockers.append("provider_usage_custody_receipt_missing")
    if usage_custody.get("authority_granted") is not False:
        blockers.append("provider_usage_custody_authority_escalation")

    if response.get("lifecycle_state") != "COMPLETED":
        blockers.append("transition_not_completed")
    if response.get("master_record_status") != "RECORDED":
        blockers.append("transition_custody_not_recorded")
    if not response.get("master_record_ref"):
        blockers.append("master_record_ref_missing")
    if response.get("reconstruction_status") != "PASS":
        blockers.append("transition_reconstruction_not_pass")

    custody = response.get("custody_submission") or {}
    if custody.get("state") != "RECORDED":
        blockers.append("custody_submission_state_not_recorded")
    if not custody.get("custody_receipt_id"):
        blockers.append("transition_custody_receipt_missing")

    authority = response.get("authority") or {}
    required_false = (
        "provider_output_is_authority",
        "repository_mutation_allowed",
        "publication_allowed",
        "gateway_receipt_is_final",
        "final_response_receipt_is_repository_execution_authority",
        "local_persistence_is_master_records_custody",
        "site_grants_admissibility",
        "provider_usage_grants_authority",
    )
    for key in required_false:
        if authority.get(key) is not False:
            blockers.append(f"authority_{key}_must_be_false")
    if authority.get("provider_usage_is_master_records_custody") is not True:
        blockers.append("provider_usage_custody_authority_projection_missing")
    if authority.get("master_records_installed") is not True:
        blockers.append("master_records_installation_projection_missing")

    return blockers


def main() -> int:
    blockers: list[str] = []
    evidence: dict[str, object] = {}
    identity = {
        "transition_id": f"transition.authorized-provider.{os.getenv('GITHUB_RUN_ID', 'local')}",
        "run_id": f"authorized-provider-run.{os.getenv('GITHUB_RUN_ID', 'local')}",
        "event_id": f"authorized-provider-event.{os.getenv('GITHUB_RUN_ID', 'local')}",
        "origin_manifest_id": f"origin.authorized-provider.{os.getenv('GITHUB_RUN_ID', 'local')}",
        "parent_transition_id": None,
        "previous_receipt_id": None,
    }

    try:
        health = wait_for_health()
        evidence["health"] = {
            "status": health.get("status"),
            "service": health.get("service"),
            "governed_provider_enabled": health.get("governed_provider_enabled"),
            "master_records_submission_enabled": health.get("master_records_submission_enabled"),
            "provider_output_is_authority": health.get("provider_output_is_authority"),
        }
        response = fetch_json(
            f"{BASE_URL}/api/ecosystem-chat",
            data={
                "message": "Describe the verified StegVerse provider, custody, and reconstruction boundary.",
                "session_id": f"authorized-provider-session-{os.getenv('GITHUB_RUN_ID', 'local')}",
                "requested_route": "Site",
                "transition_intent": "explain",
                "transition_destination": "ecosystem-chat.html#how-it-works",
                "goal": "verify real provider through authenticated custody and reconstruction",
                "execution_model": "allowlisted_task_request_only",
                "raw_shell_allowed": False,
                "authority_required": True,
                "rate_limit_required": True,
                "receipt_required_for_execution": True,
                "interaction_profile": {"governance": 100},
                "interaction_bands": ["provider", "custody", "receipt"],
                "math_solver_supported": True,
                "transition_identity": identity,
            },
            headers={"Content-Type": "application/json"},
        )
        blockers.extend(validate_runtime_result(health, response, identity))
        provider = response.get("provider") or {}
        local_usage = response.get("provider_usage_submission") or {}
        usage_custody = response.get("master_records_usage_submission") or {}
        evidence["runtime"] = {
            "transition_id": response.get("transition_id"),
            "run_id": response.get("run_id"),
            "lifecycle_state": response.get("lifecycle_state"),
            "provider_used": provider.get("used"),
            "provider_status": provider.get("status"),
            "provider_name": provider.get("provider_name"),
            "model": provider.get("model"),
            "provider_request_id": provider.get("provider_request_id"),
            "provider_receipt_id": provider.get("provider_receipt_id"),
            "provider_usage_measurement_id": local_usage.get("measurement_id"),
            "provider_usage_event_sha256": local_usage.get("event_sha256"),
            "provider_usage_custody_status": usage_custody.get("status"),
            "provider_usage_custody_receipt_id": usage_custody.get("receipt_id"),
            "master_record_status": response.get("master_record_status"),
            "master_record_ref": response.get("master_record_ref"),
            "reconstruction_status": response.get("reconstruction_status"),
            "final_receipt_id": response.get("final_receipt_id"),
        }
    except Exception as exc:
        blockers.append(f"runtime_exception:{type(exc).__name__}:{exc}")

    payload = {
        "schema": "stegverse.ecosystem_chat.authorized_provider_activation.v1",
        "state": "VERIFIED" if not blockers else "BLOCKED",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "runtime_path": [
            "governed_provider_response",
            "provider_usage_persistence",
            "provider_usage_custody",
            "transition_custody",
            "transition_reconstruction",
        ],
        "blockers": blockers,
        "evidence": evidence,
        "provider_output_is_authority": False,
        "custody_grants_execution_authority": False,
        "reconstruction_grants_publication_authority": False,
        "repository_mutation_authorized": False,
        "publication_authorized": False,
        "manual_user_action_required": False,
    }
    payload["result_sha256"] = canonical_sha256(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
