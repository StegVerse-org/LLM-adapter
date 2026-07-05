#!/usr/bin/env python3
"""Verify AI Entry endpoint packaging remains pure and side-effect free."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_adapter.ai_entry_endpoint import handle_ai_entry_payload


def fail(message: str) -> None:
    raise SystemExit(f"AI_ENTRY_ENDPOINT_FAIL: {message}")


def main() -> int:
    response = handle_ai_entry_payload({"message": "Compare StegVerse with Claude"})
    if response.get("primary_route") != "llm_comparison":
        fail("route mismatch")
    endpoint = response.get("endpoint", {})
    if endpoint.get("mode") != "pure_function_preview":
        fail("endpoint mode mismatch")
    for key in ("http_server_started", "live_calls_performed", "side_effects_performed"):
        if endpoint.get(key) is not False:
            fail(f"{key} must be false")
    if response.get("governance", {}).get("authority_issued") is not False:
        fail("authority must not be issued")
    if response.get("governance", {}).get("receipt_id") is not None:
        fail("receipt_id must remain null")
    if len(response.get("comparison_outputs", [])) != 3:
        fail("expected comparison outputs")

    empty = handle_ai_entry_payload({})
    if empty.get("response_id") != "welcome":
        fail("empty payload should return welcome response")
    print("AI_ENTRY_ENDPOINT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
