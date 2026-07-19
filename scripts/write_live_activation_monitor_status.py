#!/usr/bin/env python3
"""Write a volatile, hash-bound heartbeat for the live activation monitor.

Unlike the stable semantic activation status, this record changes on every monitor run.
It proves that repository-owned automation executed and records the latest exact outcome
without granting activation, deployment, custody, release, or execution authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION = ROOT / "receipts" / "ecosystem-chat-live-activation.latest.json"
SEMANTIC = ROOT / "reports" / "ecosystem-chat-live-activation-status.json"
OUTPUT = ROOT / "reports" / "ecosystem-chat-live-activation-monitor.json"


def canonical_sha(value: dict[str, Any]) -> str:
    material = dict(value)
    material.pop("monitor_sha256", None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def main() -> int:
    observation = load(OBSERVATION)
    semantic = load(SEMANTIC)
    observed_at = observation.get("observed_at")
    blockers = observation.get("blockers") if isinstance(observation.get("blockers"), list) else []
    state = str(observation.get("state") or semantic.get("state") or "PENDING")
    if state not in {"PENDING", "VERIFIED"}:
        state = "PENDING"
        blockers = sorted({*map(str, blockers), "monitor_observed_invalid_state"})

    payload: dict[str, Any] = {
        "schema": "stegverse.ecosystem_chat.live_activation_monitor.v1",
        "repository": "StegVerse-org/LLM-adapter",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": os.getenv("GITHUB_RUN_ID") or None,
        "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT") or None,
        "workflow_event": os.getenv("GITHUB_EVENT_NAME") or None,
        "observation_present": bool(observation),
        "observation_observed_at": observed_at,
        "observation_result_sha256": observation.get("result_sha256"),
        "semantic_status_sha256": semantic.get("status_sha256"),
        "state": state,
        "blockers": sorted({str(item) for item in blockers if str(item)}),
        "manual_user_action_required": False,
        "next_machine_action": (
            "retain_immutable_verified_receipt_and_propagate"
            if state == "VERIFIED" and not blockers
            else "continue_bounded_fifteen_minute_verification"
        ),
        "authority_boundary": {
            "monitor_is_activation_authority": False,
            "monitor_is_deployment_authority": False,
            "monitor_is_custody": False,
            "monitor_is_release_authority": False,
            "monitor_is_execution_authority": False,
        },
    }
    payload["monitor_sha256"] = canonical_sha(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"LIVE ACTIVATION MONITOR: {payload['state']}")
    print(f"Observation present: {payload['observation_present']}")
    print(f"Blockers: {', '.join(payload['blockers']) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
