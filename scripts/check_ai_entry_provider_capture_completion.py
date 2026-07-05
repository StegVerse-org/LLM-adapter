#!/usr/bin/env python3
"""Verify provider capture boundary completion stays live-disabled."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "ai-entry-provider-capture-completion.json"
COMPLETED = (
    "provider_capture_boundary_module",
    "provider_capture_boundary_verifier",
    "provider_capture_request_fixture",
    "provider_capture_response_fixture",
    "provider_capture_fixture_verifier",
    "adapter_full_validation_wired",
)
FALSE_KEYS = (
    "provider_call_performed",
    "provider_output_captured",
    "provider_authority",
    "persisted",
    "live_calls_allowed",
)


def fail(message: str) -> None:
    raise SystemExit(f"ADAPTER_PROVIDER_CAPTURE_COMPLETION_FAIL: {message}")


def main() -> int:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    if data.get("schema_version") != "stegverse.adapter.ai_entry.provider_capture_completion.v0.1":
        fail("bad schema version")
    if data.get("state") != "preview_complete_live_disabled":
        fail("state must be preview_complete_live_disabled")
    completed = data.get("completed_components", {})
    for key in COMPLETED:
        if completed.get(key) is not True:
            fail(f"{key} must be true")
    boundary = data.get("current_boundary", {})
    for key in FALSE_KEYS:
        if boundary.get(key) is not False:
            fail(f"{key} must be false")
    if data.get("next_goal_candidate") != "SDK access decision boundary":
        fail("next goal candidate mismatch")
    print("ADAPTER_PROVIDER_CAPTURE_COMPLETION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
