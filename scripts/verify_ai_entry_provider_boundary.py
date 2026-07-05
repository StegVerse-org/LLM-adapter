#!/usr/bin/env python3
"""Verify AI Entry provider boundary remains disabled by default."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_adapter.ai_entry_provider_boundary import build_disabled_provider_boundary


def fail(message: str) -> None:
    raise SystemExit(f"AI_ENTRY_PROVIDER_BOUNDARY_FAIL: {message}")


def main() -> int:
    result = build_disabled_provider_boundary()
    if result.live_provider_calls_enabled is not False:
        fail("live provider calls must be disabled")
    if result.credential_surface_enabled is not False:
        fail("credential surface must be disabled")
    if result.provider_secret_required_for_tests is not False:
        fail("tests must not require provider secrets")
    if result.provider_output_is_authority is not False:
        fail("provider output must not be authority")
    if result.receipt_capture_required_before_live_activation is not True:
        fail("receipt capture must be required before live activation")
    if len(result.comparisons) != 3:
        fail("expected three comparison providers")
    for comparison in result.comparisons:
        if comparison.enabled is not False:
            fail(f"{comparison.provider} must be disabled")
        if comparison.live_call_allowed is not False:
            fail(f"{comparison.provider} live calls must be disallowed")
        if comparison.authority is not False:
            fail(f"{comparison.provider} must not have authority")
        if comparison.comparison_only is not True:
            fail(f"{comparison.provider} must remain comparison-only")
    print("AI_ENTRY_PROVIDER_BOUNDARY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
