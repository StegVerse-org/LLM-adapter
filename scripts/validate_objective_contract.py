#!/usr/bin/env python3
"""Validate the machine-readable repository objective contract fail-closed."""

from __future__ import annotations

import json
from pathlib import Path

CONTRACT_PATH = Path("data/autonomy/objective-contract.json")
EXPECTED_REPOSITORY = "StegVerse-org/LLM-adapter"
EXPECTED_DESTINATIONS = {
    "master-records/orchestration",
    "StegVerse-org/StegVerse-SDK",
    "StegVerse-Labs/Site",
    "GCAT-BCAT-Engine/Publisher",
    "StegVerse-Labs/admissibility-wiki",
    "StegVerse-002/stegguardian-wiki",
}
REQUIRED_OUTCOMES = {
    "gateway_health_ok",
    "durable_storage_confirmed",
    "governed_provider_enabled",
    "real_provider_use_observed",
    "provider_usage_local_persistence_non_custodial",
    "provider_usage_custody_recorded",
    "provider_usage_reconstructability_pass",
    "transition_custody_recorded",
    "transition_reconstructability_pass",
    "immutable_verified_activation_receipt_published",
    "site_activation_complete",
    "downstream_verified_public_evidence",
}
REQUIRED_DISALLOWED_SUBSTITUTES = {
    "source_files_only",
    "workflow_presence_only",
    "workflow_artifact_only",
    "pending_status_as_activation",
    "provider_output_as_authority",
    "local_persistence_as_custody",
    "custody_receipt_as_execution_authority",
    "verified_receipt_as_release_authority",
}
REQUIRED_FALSE_FLAGS = {
    "provider_output_is_authority",
    "usage_measurement_is_admissibility",
    "local_persistence_is_custody",
    "custody_receipt_is_execution_authority",
    "verified_receipt_is_release_authority",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"objective contract invalid: {message}")


def main() -> None:
    require(CONTRACT_PATH.is_file(), f"missing {CONTRACT_PATH}")
    try:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"objective contract invalid: unreadable JSON: {exc}") from exc

    require(contract.get("schema_version") == "1.0", "unsupported schema_version")
    require(contract.get("repository") == EXPECTED_REPOSITORY, "repository identity mismatch")
    require(isinstance(contract.get("goal"), str) and contract["goal"].strip(), "goal is empty")
    require(set(contract.get("required_outcomes", [])) == REQUIRED_OUTCOMES, "required outcomes drift")
    require(
        set(contract.get("disallowed_substitutes", [])) == REQUIRED_DISALLOWED_SUBSTITUTES,
        "disallowed substitutes drift",
    )
    require(
        set(contract.get("canonical_downstream_destinations", [])) == EXPECTED_DESTINATIONS,
        "downstream destination drift",
    )
    require(
        set(contract.get("authority_flags_required_false", [])) == REQUIRED_FALSE_FLAGS,
        "authority boundary drift",
    )
    require(contract.get("manual_user_action_required") is False, "manual action was introduced")

    evidence = contract.get("completion_evidence")
    require(isinstance(evidence, dict), "completion_evidence is missing")
    for key in ("pending_status", "verified_receipt", "destination_state"):
        value = evidence.get(key)
        require(isinstance(value, str) and value.strip(), f"completion evidence path missing: {key}")

    completion_rule = contract.get("completion_rule")
    require(isinstance(completion_rule, str) and "runtime evidence" in completion_rule, "completion rule is not outcome-level")
    require("authority flags remain false" in completion_rule, "completion rule omits authority boundary")

    print("LLM adapter objective contract: VALID")


if __name__ == "__main__":
    main()
