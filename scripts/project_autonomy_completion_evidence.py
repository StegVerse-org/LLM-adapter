#!/usr/bin/env python3
"""Project LLM-adapter runtime records into the ecosystem strict evidence contract.

This projection is fail-closed. It does not convert repository validation,
fixtures, pending status, or workflow success into operational completion.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "reports/ecosystem-chat-live-activation-status.json"
VERIFIED = ROOT / "receipts/ecosystem-chat-live-activation.verified.json"
DESTINATION = ROOT / "reports/ecosystem-chat-destination-activation-state.json"
OUT = ROOT / "data/autonomy/completion-evidence.json"

REQUIRED_GATES = (
    "durable_storage",
    "gateway_health_ok",
    "governed_provider_enabled",
    "provider_used",
    "provider_usage_custody_recorded",
    "provider_usage_reconstructability_pass",
    "transition_custody_recorded",
    "transition_reconstructability_pass",
)


def load_optional(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def main() -> None:
    status = load_optional(STATUS) or {}
    verified = load_optional(VERIFIED)
    destination = load_optional(DESTINATION)
    gates = status.get("gates", {}) if isinstance(status.get("gates"), dict) else {}

    missing: list[str] = []
    if status.get("state") != "VERIFIED":
        missing.append("live_activation_not_verified")
    for gate in REQUIRED_GATES:
        if gates.get(gate) is not True:
            missing.append(gate)
    if verified is None:
        missing.append("immutable_verified_activation_receipt_missing")
    if destination is None:
        missing.append("destination_activation_state_missing")
    elif destination.get("state") not in {"COMPLETE", "VERIFIED", "ACTIVE"}:
        missing.append("destination_activation_not_complete")

    complete = not missing
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "schema_version": "1.0",
        "repository": "StegVerse-org/LLM-adapter",
        "objective_id": "llm-adapter-ecosystem-chat-live-governance",
        "runtime_observed": complete,
        "user_visible_outcome_verified": complete,
        "verifier_source": "github-actions",
        "critical_blockers": 0 if complete else len(missing),
        "manual_completion_dependency": False,
        "verified_at": now,
        "evidence_urls": [
            "https://github.com/StegVerse-org/LLM-adapter/blob/main/reports/ecosystem-chat-live-activation-status.json",
            "https://github.com/StegVerse-org/LLM-adapter/blob/main/receipts/ecosystem-chat-live-activation.verified.json",
            "https://github.com/StegVerse-org/LLM-adapter/blob/main/reports/ecosystem-chat-destination-activation-state.json",
        ],
        "projection_state": "OPERATIONALLY_VERIFIED" if complete else "BLOCKED",
        "missing_gates": sorted(set(missing)),
        "source_state": status.get("state", "MISSING"),
        "source_blockers": status.get("blockers", []),
        "authority": {
            "projection_is_execution_authority": False,
            "projection_is_release_authority": False,
            "pending_status_is_completion": False,
            "workflow_success_is_completion": False,
            "manual_user_action_required": False,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"projection_state": payload["projection_state"], "missing_gates": payload["missing_gates"]}))


if __name__ == "__main__":
    main()
