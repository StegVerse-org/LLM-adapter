#!/usr/bin/env python3
"""Verify AI Entry and governed-provider boundaries remain fail-closed."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_adapter.ai_entry_provider_boundary import build_disabled_provider_boundary
from llm_adapter import governed_provider


def fail(message: str) -> None:
    raise SystemExit(f"AI_ENTRY_PROVIDER_BOUNDARY_FAIL: {message}")


def verify_governed_provider_readiness() -> None:
    names = (
        "STEGVERSE_PROVIDER_ENABLED",
        "STEGVERSE_PROVIDER_ENDPOINT",
        "STEGVERSE_PROVIDER_ALLOWED_HOSTS",
        "STEGVERSE_PROVIDER_TOKEN",
        "STEGVERSE_PROVIDER_MODEL",
    )
    previous = {name: os.environ.get(name) for name in names}
    try:
        for name in names:
            os.environ.pop(name, None)
        blocked = governed_provider.readiness()
        if blocked.ready is not False or blocked.state != "BLOCKED":
            fail("empty provider configuration must remain blocked")
        if "provider_allowed_hosts_missing" not in blocked.blockers:
            fail("empty hostname allowlist must be an explicit blocker")
        if blocked.authority_granted is not False or blocked.execution_authority is not False:
            fail("provider readiness must not grant authority")

        os.environ.update({
            "STEGVERSE_PROVIDER_ENABLED": "true",
            "STEGVERSE_PROVIDER_ENDPOINT": "https://provider.example.test/generate",
            "STEGVERSE_PROVIDER_TOKEN": "verification-token-must-not-escape",
            "STEGVERSE_PROVIDER_MODEL": "verification-model",
        })
        no_allowlist = governed_provider.readiness()
        if no_allowlist.ready is not False:
            fail("configured HTTPS provider without an explicit allowlist must fail closed")
        if "provider_allowed_hosts_missing" not in no_allowlist.blockers:
            fail("missing explicit allowlist blocker not reported")
        if "verification-token-must-not-escape" in str(no_allowlist.to_dict()):
            fail("provider readiness diagnostics exposed credential material")

        os.environ["STEGVERSE_PROVIDER_ALLOWED_HOSTS"] = "provider.example.test"
        ready = governed_provider.readiness()
        if ready.ready is not True or ready.blockers:
            fail(f"complete bounded provider configuration should be ready: {ready.blockers}")
        if ready.endpoint_hostname_allowlisted is not True:
            fail("configured provider hostname must be explicitly allowlisted")
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


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

    verify_governed_provider_readiness()
    print("AI_ENTRY_PROVIDER_BOUNDARY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
