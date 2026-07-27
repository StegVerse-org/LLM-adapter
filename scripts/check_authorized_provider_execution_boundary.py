#!/usr/bin/env python3
"""Validate the machine-readable authorized-provider execution boundary."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "authorized-provider-execution-boundary.json"


def fail(message: str) -> None:
    raise SystemExit(f"AUTHORIZED_PROVIDER_BOUNDARY_FAIL: {message}")


def main() -> int:
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if value.get("schema") != "stegverse.authorized-provider.execution-boundary.v1":
        fail("unexpected schema")

    posture = value.get("configuration_posture") or {}
    for key in (
        "may_read_secret_values",
        "may_start_provider_runtime",
        "may_call_provider",
        "may_submit_master_records_custody",
    ):
        if posture.get(key) is not False:
            fail(f"configuration posture must keep {key}=false")

    execution = value.get("authorized_execution") or {}
    if execution.get("required_event") != "workflow_dispatch":
        fail("authorized execution must require workflow_dispatch")
    if execution.get("required_boolean_input") != "execute_authorized_provider":
        fail("unexpected authorization input")
    if execution.get("required_boolean_value") is not True:
        fail("authorization input must require true")
    if execution.get("protected_environment_required") is not True:
        fail("protected environment approval must be required")
    if execution.get("maximum_provider_requests") != 1:
        fail("authorized execution must remain single-request")
    if float(execution.get("maximum_request_cost_usd", -1)) > 0.10:
        fail("per-request cost ceiling exceeds $0.10")
    if float(execution.get("maximum_run_cost_usd", -1)) > 0.10:
        fail("per-run cost ceiling exceeds $0.10")

    prohibitions = set(value.get("prohibitions") or [])
    required_prohibitions = {
        "scheduled_provider_execution",
        "pull_request_provider_execution",
        "push_provider_execution",
        "workflow_run_provider_execution",
        "credential_value_publication",
        "fallback_satisfies_provider_verification",
        "local_persistence_misclassified_as_custody",
    }
    missing = sorted(required_prohibitions - prohibitions)
    if missing:
        fail(f"missing prohibitions: {', '.join(missing)}")

    required_false = set(value.get("required_false_authority_projections") or [])
    if "provider_output_is_authority" not in required_false:
        fail("provider-output authority boundary missing")
    if "repository_mutation_authorized" not in required_false:
        fail("repository mutation boundary missing")
    if "publication_authorized" not in required_false:
        fail("publication boundary missing")

    print("AUTHORIZED_PROVIDER_BOUNDARY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
