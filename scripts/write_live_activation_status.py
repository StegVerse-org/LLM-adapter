#!/usr/bin/env python3
"""Write stable, non-authorizing live activation continuation state.

The output intentionally omits timestamps and volatile request evidence. It changes only
when the semantic blocker or gate posture changes. Missing or malformed observations are
converted into durable fail-closed blockers rather than causing the status writer itself
to fail. No third-party gateway is implied when an observation does not name one.
A PENDING status carries the six non-ALLOW fields. The gates read the provider usage
record and the organization-ledger transition receipt; Master Records is not a gate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "receipts" / "ecosystem-chat-live-activation.latest.json"
OUTPUT = ROOT / "reports" / "ecosystem-chat-live-activation-status.json"
OWNING_EXISTING_GOAL = "LLMA-DECLARED-PATH-CONFORMANCE-368"


def canonical_sha(value: dict[str, Any]) -> str:
    material = dict(value)
    material.pop("status_sha256", None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def load_observation() -> tuple[dict[str, Any], list[str]]:
    if not SOURCE.exists():
        return {}, ["live_activation_observation_file_missing"]
    try:
        value = json.loads(SOURCE.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}, ["live_activation_observation_unreadable"]
    if not isinstance(value, dict):
        return {}, ["live_activation_observation_not_object"]
    return value, []


def main() -> int:
    observation, structural_blockers = load_observation()
    evidence = observation.get("evidence") if isinstance(observation.get("evidence"), dict) else {}
    health = evidence.get("health") if isinstance(evidence.get("health"), dict) else {}
    chat = evidence.get("chat") if isinstance(evidence.get("chat"), dict) else {}
    transition = evidence.get("transition") if isinstance(evidence.get("transition"), dict) else {}
    provider = chat.get("provider") if isinstance(chat.get("provider"), dict) else {}
    provider_usage_record = chat.get("provider_usage_submission") if isinstance(chat.get("provider_usage_submission"), dict) else {}

    observation_blockers = observation.get("blockers", [])
    if not isinstance(observation_blockers, list):
        structural_blockers.append("live_activation_blockers_not_list")
        observation_blockers = []
    blockers = sorted({str(item) for item in [*structural_blockers, *observation_blockers] if str(item)})

    requested_state = str(observation.get("state") or "PENDING")
    if requested_state not in {"PENDING", "VERIFIED"}:
        blockers.append("live_activation_state_invalid")
        requested_state = "PENDING"
    if requested_state == "VERIFIED" and blockers:
        blockers.append("verified_live_activation_contains_blockers")
        requested_state = "PENDING"
    blockers = sorted(set(blockers))

    gateway_base_url = observation.get("gateway_base_url")
    if gateway_base_url is not None and not isinstance(gateway_base_url, str):
        blockers.append("live_activation_gateway_base_url_invalid")
        gateway_base_url = None
        requested_state = "PENDING"
    blockers = sorted(set(blockers))

    payload: dict[str, Any] = {
        "schema": "stegverse.ecosystem_chat.live_activation_status.v1",
        "repository": "StegVerse-org/LLM-adapter",
        "state": requested_state,
        "blockers": blockers,
        "gateway_base_url": gateway_base_url,
        "gateway_selection": "OBSERVATION_EXPLICIT_ONLY",
        "implicit_third_party_gateway": False,
        "gates": {
            "gateway_health_ok": health.get("status") == "ok",
            "durable_storage": health.get("storage_durable_across_restarts") is True,
            "governed_provider_enabled": health.get("governed_provider_enabled") is True,
            "provider_used": provider.get("used") is True,
            "provider_usage_record_present": bool(
                provider_usage_record.get("measurement_id") and provider_usage_record.get("event_sha256")
            ),
            "provider_usage_authority_false": provider_usage_record.get("authority_granted") is False,
            "organization_ledger_transition_receipt_observed": bool(
                transition.get("lifecycle_state") == "COMPLETED" and transition.get("final_receipt_id")
            ),
        },
        "manual_user_action_required": False,
        "continuation_mode": "resident_worker_managed",
        "authority_boundary": {
            "status_is_activation_authority": False,
            "status_is_deployment_authority": False,
            "status_is_custody": False,
            "status_is_release_authority": False,
        },
    }
    if requested_state != "VERIFIED":
        failure_code = blockers[0] if blockers else "live_activation_not_verified"
        payload.update({
            "disposition": "FAIL_CLOSED",
            "failure_code": failure_code,
            "failed_predicate": "ecosystem_chat_live_activation_verified",
            "required_evidence_or_repair": "repair every listed blocker in the live activation observation: "
            + (", ".join(blockers) or failure_code),
            "retry_entrypoint": "STEGVERSE_GATEWAY_BASE_URL=<gateway> python scripts/verify_live_ecosystem_chat_activation.py",
            "owning_existing_goal": OWNING_EXISTING_GOAL,
            "next_attempt": "rewrite this status from the next live activation observation",
        })
    else:
        payload["disposition"] = "ALLOW"
    payload["status_sha256"] = canonical_sha(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"LIVE ACTIVATION STATUS: {requested_state}")
    print(f"Blockers: {', '.join(blockers) or 'none'}")
    print(f"Receipt: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
