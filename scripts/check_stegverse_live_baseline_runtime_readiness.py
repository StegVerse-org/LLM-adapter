#!/usr/bin/env python3
"""Fail-closed validation for the StegVerse live baseline runtime intake."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "intake/stegverse-live-baseline-execution-request-v1.json"
READINESS = ROOT / "status/stegverse-live-baseline-runtime-readiness.json"
NO_AUTHORITY = {
    "comparison": False,
    "admissibility": False,
    "certification": False,
    "execution": False,
    "custody": False,
    "parentage": False,
}
RUNTIME_PREREQUISITES = {
    "authorized_provider_configuration_receipt",
    "persistent_endpoint_activation_receipt",
    "provider_usage_persistence_contract",
    "master_records_custody_acceptance",
    "transition_custody_acceptance",
    "immutable_adapter_receipt_contract",
}


def require(value: object, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    require(INTAKE.is_file(), "missing live baseline intake")
    require(READINESS.is_file(), "missing runtime readiness contract")
    intake = json.loads(INTAKE.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))

    require(intake.get("intake_id") == readiness.get("intake_id"), "intake/readiness id mismatch")
    require(intake.get("runtime_owner") == "StegVerse-org/LLM-adapter", "runtime owner mismatch")
    require(readiness.get("runtime_owner") == "StegVerse-org/LLM-adapter", "readiness runtime owner mismatch")
    require(intake.get("authority") == NO_AUTHORITY, "intake authority boundary changed")
    require(readiness.get("authority") == NO_AUTHORITY, "readiness authority boundary changed")

    prerequisites = readiness.get("prerequisites") or {}
    require(prerequisites.get("intake_received") is True, "intake receipt regressed")
    require(RUNTIME_PREREQUISITES <= set(prerequisites), "missing runtime prerequisite")
    all_ready = all(prerequisites.get(key) is True for key in RUNTIME_PREREQUISITES)

    dispatch = readiness.get("dispatch") or {}
    execution = readiness.get("execution") or {}
    if all_ready:
        require(readiness.get("state") in {"READY", "EXECUTION_PENDING_OBSERVATION", "EXECUTION_COMPLETE"}, "satisfied prerequisites cannot remain BLOCKED")
    else:
        require(readiness.get("state") == "BLOCKED", "incomplete prerequisites must fail closed")
        require(readiness.get("blocking_conditions"), "BLOCKED readiness requires blocking conditions")
        require(dispatch.get("authorized") is False, "blocked readiness cannot authorize dispatch")
        require(dispatch.get("dispatch_id") is None, "blocked readiness cannot have dispatch id")
        require(dispatch.get("dispatched_at") is None, "blocked readiness cannot have dispatch time")
        require(execution.get("authorized") is False, "blocked readiness cannot authorize execution")
        require(execution.get("started") is False, "blocked readiness cannot start execution")
        require(execution.get("completed") is False, "blocked readiness cannot complete execution")
        require(execution.get("run_id") is None, "blocked readiness cannot have run id")

    require(intake.get("dispatch_state") == "NOT_DISPATCHED" if not all_ready else True, "intake dispatch state contradicts readiness")
    require(len(readiness.get("required_outputs") or []) >= 8, "runtime output contract incomplete")
    print(f"STEGVERSE LIVE BASELINE RUNTIME READINESS: {readiness.get('state')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
