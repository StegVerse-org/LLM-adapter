#!/usr/bin/env python3
"""Verify fixture-bound micro-node governed return-path compatibility."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "examples" / "micro_node_return_path"

REQUIRED_REQUEST_FIELDS = {
    "transition_id",
    "origin_system",
    "return_path",
    "action",
    "actor",
    "target",
    "scope",
    "policy_ref",
    "delegation_ref",
    "payload",
}

REQUIRED_RETURN_FIELDS = {
    "transition_id",
    "return_path",
    "decision",
    "receipt_hash",
    "returned_to_origin",
    "execution_authority_granted",
    "provider_output_is_authority",
}


def read_json(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def main() -> int:
    request = read_json("request.json")
    governed_return = read_json("governed_return.json")
    failures: list[str] = []

    missing_request = sorted(REQUIRED_REQUEST_FIELDS - set(request))
    if missing_request:
        failures.append(f"request missing fields: {missing_request}")

    missing_return = sorted(REQUIRED_RETURN_FIELDS - set(governed_return))
    if missing_return:
        failures.append(f"governed return missing fields: {missing_return}")

    if request.get("transition_id") != governed_return.get("transition_id"):
        failures.append("transition_id mismatch")
    if request.get("return_path") != governed_return.get("return_path"):
        failures.append("return_path mismatch")
    if governed_return.get("decision") not in {"ALLOW", "DENY", "FAIL_CLOSED"}:
        failures.append("bad terminal decision")
    if governed_return.get("returned_to_origin") is not True:
        failures.append("return path was not preserved")
    if governed_return.get("execution_authority_granted") is not False:
        failures.append("execution authority must remain false")
    if governed_return.get("provider_output_is_authority") is not False:
        failures.append("provider output must not become authority")
    if request.get("payload", {}).get("execution_authority_requested") is not False:
        failures.append("request must not ask for execution authority")

    if failures:
        print("MICRO_NODE_RETURN_PATH_FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("MICRO_NODE_RETURN_PATH_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
