#!/usr/bin/env python3
"""Verify interim AI Entry backend service scaffold remains disabled and bounded."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_adapter.ai_entry_backend_service import build_ai_entry_backend_response


def fail(message: str) -> None:
    raise SystemExit(f"AI_ENTRY_BACKEND_SERVICE_FAIL: {message}")


def assert_response(message: str, expected_route: str, expected_candidate: bool) -> None:
    response = build_ai_entry_backend_response(message)
    if response.primary_route != expected_route:
        fail(f"route mismatch for {message!r}: {response.primary_route} != {expected_route}")
    if response.governance["governed_candidate"] is not expected_candidate:
        fail(f"governed candidate mismatch for {message!r}")
    if response.governance["authority_issued"] is not False:
        fail("authority must not be issued")
    if response.governance["receipt_id"] is not None:
        fail("receipt_id must remain null")
    if response.activation["live_provider_calls_enabled"] is not False:
        fail("live provider calls must be disabled")
    if response.activation["credential_surface_enabled"] is not False:
        fail("credential surface must be disabled")
    if response.activation["provider_output_is_authority"] is not False:
        fail("provider output must not be authority")
    if len(response.comparison_outputs) != 3:
        fail("expected three comparison outputs")
    for item in response.comparison_outputs:
        if item["authority"] is not False:
            fail("comparison output authority must be false")


def main() -> int:
    assert_response("", "chat_answer", False)
    assert_response("Compare StegVerse with Claude", "llm_comparison", True)
    assert_response("How do I access the SDK?", "sdk_access_guidance", True)
    assert_response("Review a restricted admin workflow request", "restricted_admin", True)
    print("AI_ENTRY_BACKEND_SERVICE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
