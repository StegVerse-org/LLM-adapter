#!/usr/bin/env python3
"""Verify AI Entry service wrapper defaults."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_adapter.ai_entry_service_wrapper import get_service_status, handle_service_request


def fail(message: str) -> None:
    raise SystemExit(f"AI_ENTRY_SERVICE_WRAPPER_FAIL: {message}")


def main() -> int:
    status = get_service_status()
    if status.wrapper_present is not True:
        fail("wrapper_present must be true")
    for key in ("started_by_import", "live_calls_enabled", "side_effects_enabled"):
        if getattr(status, key) is not False:
            fail(f"{key} must be false")

    response = handle_service_request({"message": "Compare StegVerse with ChatGPT"})
    if response.get("primary_route") != "llm_comparison":
        fail("route mismatch")
    service = response.get("service", {})
    if service.get("wrapper_present") is not True:
        fail("response service wrapper marker missing")
    if service.get("live_calls_enabled") is not False:
        fail("live calls must remain false")
    if response.get("governance", {}).get("authority_issued") is not False:
        fail("authority must not be issued")

    print("AI_ENTRY_SERVICE_WRAPPER_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
