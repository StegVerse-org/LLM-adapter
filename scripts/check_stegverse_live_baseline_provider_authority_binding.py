#!/usr/bin/env python3
"""Validate the StegVerse sovereign provider-authority binding.

This checker deliberately rejects the retired GitHub Models authority path. The
resident StegVerse carrier + TVC route authority own live execution; LLM-adapter
is transport/evidence only and GitHub tokens have no runtime authority.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "status/stegverse-live-baseline-provider-authority-binding.json"
INTAKE = ROOT / "intake/stegverse-live-baseline-execution-request-v1.json"
RETIRED_WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-github-models-execution.yml"
WORKFLOW_HANDOFF = ROOT / "docs/WORKFLOW_CONSOLIDATION_MIRROR_HANDOFF.md"
NO_AUTHORITY = {
    "comparison": False,
    "admissibility": False,
    "certification": False,
    "execution": False,
    "custody": False,
    "parentage": False,
}


def require(value: object, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    for path in (BINDING, INTAKE, WORKFLOW_HANDOFF):
        require(path.is_file(), f"missing required artifact: {path.relative_to(ROOT)}")
    require(not RETIRED_WORKFLOW.exists(), "retired GitHub Models execution workflow must remain absent")

    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    intake = json.loads(INTAKE.read_text(encoding="utf-8"))
    handoff = WORKFLOW_HANDOFF.read_text(encoding="utf-8")

    require(binding.get("schema_version") == "1.2.0", "unsupported schema_version")
    require(binding.get("intake_id") == intake.get("intake_id"), "intake binding mismatch")
    require(binding.get("requested_transition") == intake.get("requested_transition"), "transition mismatch")
    require(binding.get("reuse_first") is True, "binding must preserve reuse-first decision")

    path = binding.get("provider_authority_path") or {}
    require(path.get("authority_owner") == "StegVerse-Labs/TVC", "TVC authority owner mismatch")
    require(path.get("runtime_owner") == "StegVerse-002/micro-node-runtime", "local runtime owner mismatch")
    require(path.get("transport_executor") == "StegVerse-org/LLM-adapter", "transport executor mismatch")
    require(path.get("custody_owner") == "master-records/orchestration", "custody owner mismatch")
    require(path.get("github_hosted_provider_workflow") is None, "GitHub-hosted provider workflow cannot remain authoritative")

    contract = binding.get("provider_contract") or {}
    require(contract.get("provider") == "stegverse-sovereign-local-model", "provider must be the sovereign local model")
    require(contract.get("credential_authority") == "TV/TVC", "credential authority must be TV/TVC")
    require(contract.get("credential_requirement") == "NONE_FOR_LOCAL_MODEL", "local model must require no provider credential")
    require(contract.get("github_token_runtime_authority") == "NONE", "GitHub token runtime authority must be NONE")
    require(contract.get("third_party_provider_required") is False, "third-party provider cannot be required")
    require(contract.get("single_execution") is True, "single-execution contract changed")

    custody = binding.get("custody_binding") or {}
    require(custody.get("mode") == "same_execution_master_records", "custody mode mismatch")
    require(custody.get("owner_repository") == "master-records/orchestration", "custody owner mismatch")
    require(custody.get("authority_owner") == "TV/TVC", "custody authority owner mismatch")
    require(custody.get("preprovisioned_non_tvc_token_required") is False, "non-TV/TVC token cannot be required")
    require(custody.get("github_token_required") is False, "GitHub token cannot be required")
    require(custody.get("reconstruction_required") is True, "same-execution reconstruction must remain required")

    required_before_dispatch = binding.get("required_before_dispatch") or []
    require(required_before_dispatch == [
        "eligible resident StegVerse carrier",
        "TVC admitted route or credential_requirement NONE",
        "private local model process observed",
        "same-execution Master Records reconstruction path available",
    ], "dispatch preconditions mismatch")

    runtime_preconditions = binding.get("runtime_preconditions_before_authority_consumption") or []
    require(runtime_preconditions == [
        "resident sovereign carrier active",
        "fresh authorized claim/fence",
        "TVC route admission resolved",
        "exact LLM-adapter route available",
        "Master Records same-execution reconstruction available",
    ], "runtime preconditions mismatch")

    state = binding.get("current_state") or {}
    require(state.get("sovereign_local_model_source_complete") is True, "formal local model source must remain complete")
    require(state.get("local_runtime_discovery_launch_inference_proof_complete") is True, "local runtime proof path must remain complete")
    require(state.get("live_same_carrier_activation_complete") is False, "live activation cannot be inferred")
    require(state.get("dispatch_authorized") is False, "dispatch cannot be inferred")
    require(state.get("provider_execution_authorized") is False, "provider execution cannot be inferred")
    require(intake.get("dispatch_state") == "NOT_DISPATCHED", "intake cannot claim dispatch")
    require(intake.get("execution_authorized") is False, "intake cannot claim execution authority")

    for required in (
        "credential_authority: TV/TVC",
        "github_token_runtime_authority: NONE",
        "GitHub token as provider credential: prohibited",
        "resident sovereign carrier",
    ):
        require(required in handoff, f"workflow handoff missing authority invariant: {required}")

    require(binding.get("authority") == NO_AUTHORITY, "binding authority boundary changed")
    serialized = json.dumps(binding, sort_keys=True)
    for prohibited in (
        "github-models",
        "models.github.ai",
        "GITHUB_TOKEN",
        "ephemeral GitHub Actions",
    ):
        require(prohibited not in serialized, f"retired provider authority remains in binding: {prohibited}")

    print("STEGVERSE LIVE BASELINE PROVIDER AUTHORITY BINDING: TVC_SOVEREIGN_ROUTE / LIVE_ACTIVATION_PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
