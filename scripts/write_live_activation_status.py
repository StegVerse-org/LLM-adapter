#!/usr/bin/env python3
"""Write a stable, non-authorizing status from the latest live activation observation.

The output intentionally omits timestamps and volatile request evidence. It changes only
when the deployment posture or semantic blocker set changes, making scheduled workflow
state durable without creating hourly commit churn.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "receipts" / "ecosystem-chat-live-activation.latest.json"
OUTPUT = ROOT / "reports" / "ecosystem-chat-live-activation-status.json"


def canonical_sha(value: dict[str, Any]) -> str:
    material = dict(value)
    material.pop("status_sha256", None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def main() -> int:
    observation = json.loads(SOURCE.read_text(encoding="utf-8"))
    if not isinstance(observation, dict):
        raise SystemExit("live activation observation must be a JSON object")

    evidence = observation.get("evidence") if isinstance(observation.get("evidence"), dict) else {}
    health = evidence.get("health") if isinstance(evidence.get("health"), dict) else {}
    chat = evidence.get("chat") if isinstance(evidence.get("chat"), dict) else {}
    transition = evidence.get("transition") if isinstance(evidence.get("transition"), dict) else {}
    provider = chat.get("provider") if isinstance(chat.get("provider"), dict) else {}
    provider_usage = (
        chat.get("master_records_usage_submission")
        if isinstance(chat.get("master_records_usage_submission"), dict)
        else {}
    )

    blockers = sorted({str(item) for item in observation.get("blockers", []) if str(item)})
    state = str(observation.get("state") or "PENDING")
    if state not in {"PENDING", "VERIFIED"}:
        raise SystemExit("unsupported live activation state")
    if state == "VERIFIED" and blockers:
        raise SystemExit("verified live activation cannot retain blockers")

    payload: dict[str, Any] = {
        "schema": "stegverse.ecosystem_chat.live_activation_status.v1",
        "repository": "StegVerse-org/LLM-adapter",
        "state": state,
        "blockers": blockers,
        "gateway_base_url": observation.get("gateway_base_url"),
        "gates": {
            "gateway_health_ok": health.get("status") == "ok",
            "durable_storage": health.get("storage_durable_across_restarts") is True,
            "governed_provider_enabled": health.get("governed_provider_enabled") is True,
            "master_records_submission_enabled": health.get("master_records_submission_enabled") is True,
            "provider_used": provider.get("used") is True,
            "provider_usage_custody_recorded": provider_usage.get("custody_recorded") is True,
            "provider_usage_reconstructability_pass": provider_usage.get("reconstructability") == "PASS",
            "transition_custody_recorded": transition.get("master_record_status") == "RECORDED",
            "transition_reconstructability_pass": transition.get("reconstruction_status") == "PASS",
        },
        "manual_user_action_required": False,
        "continuation_mode": "scheduled_workflow_managed",
        "authority_boundary": {
            "status_is_activation_authority": False,
            "status_is_deployment_authority": False,
            "status_is_custody": False,
            "status_is_release_authority": False,
        },
    }
    payload["status_sha256"] = canonical_sha(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"LIVE ACTIVATION STATUS: {state}")
    print(f"Blockers: {', '.join(blockers) or 'none'}")
    print(f"Receipt: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
