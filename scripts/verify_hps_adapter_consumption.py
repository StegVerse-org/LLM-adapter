#!/usr/bin/env python3
"""Verify LLM-adapter HPS route consumption fixtures.

This verifier checks that HPS route outcomes are consumed as bounded route
signals, not as execution authority.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VALID_DECISIONS = {"ALLOW", "DENY", "REVIEW", "FAIL_CLOSED"}
VALID_ACTIONS = {
    "PROCEED_TO_NEXT_GOVERNED_BOUNDARY",
    "BLOCK_CONSEQUENCE",
    "ROUTE_TO_REVIEW",
    "BLOCK_CONSEQUENCE_AND_PRESERVE_EVIDENCE",
}

REQUIRED = {
    "fixture_type",
    "fixture_id",
    "requested_action",
    "hps_route_decision",
    "adapter_action",
    "execution_authority_granted",
    "provider_output_is_authority",
    "receipt_required",
    "expected_result",
}


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    message: str
    errors: list[str]


def load_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("fixture root must be a JSON object")
    return data


def verify_fixture(fixture: dict[str, Any]) -> VerificationResult:
    errors: list[str] = []
    for key in sorted(REQUIRED - set(fixture.keys())):
        errors.append(f"missing required field: {key}")

    if errors:
        return VerificationResult(False, "FAIL: fixture structurally incomplete", errors)

    if fixture.get("fixture_type") != "hps_adapter_consumption":
        errors.append("fixture_type must be hps_adapter_consumption")

    decision = fixture.get("hps_route_decision")
    action = fixture.get("adapter_action")

    if decision not in VALID_DECISIONS:
        errors.append("hps_route_decision is not recognized")
    if action not in VALID_ACTIONS:
        errors.append("adapter_action is not recognized")

    if fixture.get("execution_authority_granted") is not False:
        errors.append("execution_authority_granted must be false")
    if fixture.get("provider_output_is_authority") is not False:
        errors.append("provider_output_is_authority must be false")
    if fixture.get("receipt_required") is not True:
        errors.append("receipt_required must be true")

    expected_action = {
        "ALLOW": "PROCEED_TO_NEXT_GOVERNED_BOUNDARY",
        "DENY": "BLOCK_CONSEQUENCE",
        "REVIEW": "ROUTE_TO_REVIEW",
        "FAIL_CLOSED": "BLOCK_CONSEQUENCE_AND_PRESERVE_EVIDENCE",
    }.get(str(decision))

    if expected_action and action != expected_action:
        errors.append(f"adapter_action {action} does not match expected action {expected_action}")

    if fixture.get("expected_result") != "PASS":
        errors.append("expected_result must be PASS for fixture verification")

    if errors:
        return VerificationResult(False, "FAIL: HPS adapter consumption invalid", errors)

    return VerificationResult(True, "PASS: HPS adapter consumption valid", [])


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: verify_hps_adapter_consumption.py <fixture.json>", file=sys.stderr)
        return 2
    try:
        result = verify_fixture(load_fixture(Path(argv[1])))
    except Exception as exc:
        print(f"FAIL: could not read fixture: {exc}", file=sys.stderr)
        return 1

    print(result.message)
    for error in result.errors:
        print(f"- {error}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
