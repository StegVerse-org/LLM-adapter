#!/usr/bin/env python3
"""Derive fail-closed VA provider execution preflight state.

This observer consumes a fresh TVC admission artifact, optional validated explicit
provider authority, and presence-only Master Records configuration signals. It
never reads credential values and never calls a provider.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_ROUTE = "service_connection"
EXPECTED_CALLER = "StegVerse-org/LLM-adapter"
EXPECTED_ANSWER_HASH = "bd1f6c3e751b1adf2345383f724f133c321e0e42096b4556f682837caf73ee29"
EXPECTED_DISPATCH_HASH = "55419dc015db717f10914c86286b3222493753545f03fb4bd675a7dd2db4bd4e"
EXPECTED_PURPOSE = "SOURCE_GROUNDED_VA_CLAIM_GUIDANCE"
EXPECTED_SCOPE = "PUBLIC_SOURCE_SERVICE_CONNECTION_PROCEDURAL_GUIDANCE"


def canonical_hash(payload: dict[str, Any], hash_field: str) -> str:
    material = dict(payload)
    material.pop(hash_field, None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field}_missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def validate_admission(value: Any, *, expected_commit: str, now: datetime) -> list[str]:
    blockers: list[str] = []
    if not isinstance(value, dict):
        return ["tvc_admission_not_object"]

    if value.get("state") != "ADMITTED_PENDING_PROVIDER_EXECUTION":
        blockers.append("tvc_admission_state_invalid")
    if value.get("capability_id") != "va-claim-assistant-governed-retrieval":
        blockers.append("tvc_capability_id_invalid")

    issuer = value.get("issuer") or {}
    if issuer.get("repository") != "StegVerse-Labs/TVC":
        blockers.append("tvc_issuer_repository_invalid")
    if issuer.get("workflow") != ".github/workflows/va-route-ephemeral-admission.yml":
        blockers.append("tvc_issuer_workflow_invalid")

    caller = value.get("caller") or {}
    if caller.get("repository") != EXPECTED_CALLER:
        blockers.append("caller_repository_mismatch")
    if caller.get("commit") != expected_commit:
        blockers.append("caller_commit_mismatch")

    invocation = value.get("invocation") or {}
    exact = {
        "route": EXPECTED_ROUTE,
        "answer_receipt_hash": EXPECTED_ANSWER_HASH,
        "dispatch_receipt_hash": EXPECTED_DISPATCH_HASH,
        "purpose": EXPECTED_PURPOSE,
        "scope": EXPECTED_SCOPE,
    }
    for field, expected in exact.items():
        if invocation.get(field) != expected:
            blockers.append(f"admission_binding_mismatch:{field}")

    validity = value.get("validity") or {}
    try:
        issued = parse_time(validity.get("issued_at"), "issued_at")
        expires = parse_time(validity.get("expires_at"), "expires_at")
        if int((expires - issued).total_seconds()) != 900:
            blockers.append("admission_lifetime_not_900_seconds")
        if now < issued:
            blockers.append("admission_not_yet_valid")
        if now >= expires:
            blockers.append("admission_expired")
    except ValueError as exc:
        blockers.append(str(exc))

    if validity.get("single_use") is not True:
        blockers.append("admission_not_single_use")
    if validity.get("commit_time_validity_passed") is not True:
        blockers.append("admission_commit_time_validity_failed")
    if validity.get("revocation_state_at_issue") != "NOT_REVOKED":
        blockers.append("admission_revoked_or_unknown")
    if not str(validity.get("revocation_reference", "")).startswith("tvc://revocations/"):
        blockers.append("admission_revocation_reference_missing")

    checks = value.get("checks") or {}
    for field in (
        "caller_allowed",
        "route_allowed",
        "source_registry_bound",
        "answer_schema_bound",
        "answer_and_dispatch_hashes_bound",
        "purpose_bound",
        "scope_bound",
        "expiry_bounded",
        "revocation_checked",
        "authority_escalation_absent",
    ):
        if checks.get(field) is not True:
            blockers.append(f"admission_check_failed:{field}")
    for field in (
        "secret_values_present",
        "direct_identifiers_present",
        "raw_documents_present",
        "prompts_or_traces_present",
        "medical_narrative_present",
    ):
        if checks.get(field) is not False:
            blockers.append(f"admission_privacy_boundary_failed:{field}")

    if any((value.get("authority_flags") or {}).values()):
        blockers.append("admission_authority_escalation")
    if value.get("activation_effect") is not False:
        blockers.append("admission_activation_effect_invalid")

    expected_hash = value.get("receipt_hash")
    actual_hash = canonical_hash(value, "receipt_hash")
    if expected_hash != actual_hash:
        blockers.append("admission_receipt_hash_mismatch")
    return blockers


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}:not_object")
    return value


def present(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admission", required=True)
    parser.add_argument("--authority-validation", required=True)
    parser.add_argument("--expected-caller-commit", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = datetime.now(timezone.utc)
    admission_path = Path(args.admission)
    output_path = Path(args.output)
    blockers: list[str] = []

    try:
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        admission = {}
        blockers.append("fresh_tvc_admission_missing")
    except json.JSONDecodeError:
        admission = {}
        blockers.append("fresh_tvc_admission_invalid_json")

    if admission:
        blockers.extend(
            validate_admission(
                admission,
                expected_commit=args.expected_caller_commit,
                now=now,
            )
        )

    config = {
        "master_records_endpoint_configured": present("STEGVERSE_MASTER_RECORDS_ENDPOINT"),
        "master_records_allowed_hosts_configured": present("STEGVERSE_MASTER_RECORDS_ALLOWED_HOSTS"),
        "master_records_token_configured": present("STEGVERSE_MASTER_RECORDS_TOKEN"),
    }
    for field, configured in config.items():
        if not configured:
            blockers.append("authorized_configuration_missing:" + field.replace("_configured", "").upper())

    authority_path = Path(args.authority_validation)
    try:
        authority = load_optional_json(authority_path)
    except (json.JSONDecodeError, ValueError):
        authority = None
        blockers.append("provider_execution_authority_validation_invalid")

    if authority is None:
        blockers.append("provider_execution_authority_missing_or_invalid")
    else:
        if authority.get("state") != "VALID":
            blockers.append("provider_execution_authority_not_valid")
        if authority.get("caller_commit") != args.expected_caller_commit:
            blockers.append("provider_execution_authority_commit_mismatch")
        if float(authority.get("maximum_request_cost_usd", 999)) > 0.10:
            blockers.append("provider_execution_authority_cost_exceeds_ceiling")

    admission_valid = bool(admission) and not any(
        blocker.startswith("admission_")
        or blocker.startswith("tvc_")
        or blocker.startswith("caller_")
        or blocker.startswith("fresh_tvc_")
        for blocker in blockers
    )
    config_ready = all(config.values())
    authority_ready = authority is not None and not any(
        blocker.startswith("provider_execution_authority") for blocker in blockers
    )

    if not admission_valid:
        state = "REVIEW_REQUIRED"
        next_action = "Repair the TVC reusable admission binding before any provider authority or configuration can be consumed."
    elif not config_ready:
        state = "CONFIGURATION_REQUIRED"
        next_action = "Configure the authorized Master Records endpoint, allowed hosts, and token in the protected GitHub execution environment."
    elif not authority_ready:
        state = "AUTHORITY_REQUIRED"
        next_action = "A separately authorized owner must commit a valid, unexpired VA-specific provider-execution authority receipt for this exact caller commit."
    else:
        state = "READY_FOR_EXPLICIT_AUTHORIZED_EXECUTION"
        next_action = "A workflow_dispatch-only, single-request execution lane may consume both the fresh TVC admission and explicit authority before requesting models:read."

    observation_source = (
        "GITHUB_ACTIONS_WORKFLOW"
        if os.getenv("GITHUB_ACTIONS", "").lower() == "true"
        else "LOCAL_DETERMINISTIC_VALIDATION"
    )

    result: dict[str, Any] = {
        "schema": "stegverse.va_claim_assistant.provider_execution_preflight.v1",
        "state": state,
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "observation_source": observation_source,
        "workflow_run_id": os.getenv("GITHUB_RUN_ID") or None,
        "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT") or None,
        "route": EXPECTED_ROUTE,
        "caller_repository": EXPECTED_CALLER,
        "caller_commit": args.expected_caller_commit,
        "tvc_admission": {
            "present": bool(admission),
            "valid": admission_valid,
            "receipt_id": admission.get("receipt_id"),
            "receipt_hash": admission.get("receipt_hash"),
            "issued_at": (admission.get("validity") or {}).get("issued_at"),
            "expires_at": (admission.get("validity") or {}).get("expires_at"),
            "single_use": (admission.get("validity") or {}).get("single_use"),
        },
        "configuration": config,
        "explicit_provider_authority": {
            "present_and_valid": authority_ready,
            "authority_sha256": authority.get("authority_sha256") if authority else None,
            "model": authority.get("model") if authority else None,
            "maximum_request_cost_usd": authority.get("maximum_request_cost_usd") if authority else None,
        },
        "provider": {
            "name": "github-models",
            "permission_requested_by_preflight": False,
            "credential_source_if_later_authorized": "ephemeral GitHub Actions GITHUB_TOKEN",
            "provider_execution_observed": False,
        },
        "blockers": sorted(set(blockers)),
        "next_executable_action": next_action,
        "manual_user_action_required": False,
        "secret_values_present": False,
        "authority_effect": False,
        "activation_effect": False,
        "custody_state": "NOT_SUBMITTED",
        "reconstruction_state": "NOT_SUBMITTED",
    }
    result["result_sha256"] = canonical_hash(result, "result_sha256")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"VA_PROVIDER_PREFLIGHT_{state}:{result['result_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
