#!/usr/bin/env python3
"""Write a volatile, non-authorizing heartbeat for each live activation workflow run."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "reports" / "ecosystem-chat-live-activation-status.json"
OBSERVATION = ROOT / "receipts" / "ecosystem-chat-live-activation.latest.json"
OUTPUT = ROOT / "reports" / "ecosystem-chat-live-activation-monitor.json"


def file_sha(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def canonical_sha(value: dict[str, Any]) -> str:
    material = dict(value)
    material.pop("monitor_sha256", None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def main() -> int:
    status = read_json(STATUS)
    blockers = status.get("blockers") if isinstance(status.get("blockers"), list) else []
    state = status.get("state") if status.get("state") in {"PENDING", "VERIFIED"} else "PENDING"
    payload: dict[str, Any] = {
        "schema": "stegverse.ecosystem_chat.live_activation_monitor.v1",
        "repository": "StegVerse-org/LLM-adapter",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "workflow": {
            "run_id": os.getenv("GITHUB_RUN_ID", "local"),
            "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "1"),
            "event_name": os.getenv("GITHUB_EVENT_NAME", "local"),
            "workflow_ref": os.getenv("GITHUB_WORKFLOW_REF", "local"),
            "sha": os.getenv("GITHUB_SHA", "local"),
        },
        "semantic_state": state,
        "semantic_blockers": sorted(str(item) for item in blockers),
        "semantic_status_sha256": file_sha(STATUS),
        "observation_sha256": file_sha(OBSERVATION),
        "next_machine_action": (
            "retain_verified_receipt_and_propagate" if state == "VERIFIED" and not blockers
            else "repeat_scheduled_live_activation_verification"
        ),
        "manual_user_action_required": False,
        "authority_boundary": {
            "monitor_is_activation_authority": False,
            "monitor_is_custody": False,
            "monitor_is_deployment_authority": False,
            "monitor_is_release_authority": False,
        },
    }
    payload["monitor_sha256"] = canonical_sha(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"LIVE ACTIVATION MONITOR: {state}")
    print(f"Blockers: {', '.join(payload['semantic_blockers']) or 'none'}")
    print(f"Receipt: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
