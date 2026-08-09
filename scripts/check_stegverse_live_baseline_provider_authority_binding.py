#!/usr/bin/env python3
"""Validate reuse of the existing receipt-gated provider authority path."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "status/stegverse-live-baseline-provider-authority-binding.json"
INTAKE = ROOT / "intake/stegverse-live-baseline-execution-request-v1.json"
REQUEST = ROOT / "authority/provider-execution-authority.github-models.request.json"
VALIDATOR = ROOT / "scripts/validate_provider_execution_authority.py"
WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-github-models-execution.yml"
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
    for path in (BINDING, INTAKE, REQUEST, VALIDATOR, WORKFLOW):
        require(path.is_file(), f"missing required artifact: {path.relative_to(ROOT)}")

    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    intake = json.loads(INTAKE.read_text(encoding="utf-8"))
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    require(binding.get("schema_version") == "1.1.0", "unsupported schema_version")
    require(binding.get("intake_id") == intake.get("intake_id"), "intake binding mismatch")
    require(binding.get("requested_transition") == intake.get("requested_transition"), "transition mismatch")
    require(binding.get("reuse_first") is True, "binding must preserve reuse-first decision")

    path = binding.get("provider_authority_path") or {}
    require(path.get("request_template") == "authority/provider-execution-authority.github-models.request.json", "request template mismatch")
    require(path.get("approval_receipt") == "receipts/provider-execution-authority.github-models.v1.json", "approval receipt mismatch")
    require(path.get("consumption_receipt") == "receipts/provider-execution-authority.github-models.consumed.json", "consumption receipt mismatch")
    require(path.get("validator") == "scripts/validate_provider_execution_authority.py", "validator mismatch")
    require(path.get("workflow") == ".github/workflows/ecosystem-chat-github-models-execution.yml", "workflow mismatch")

    contract = binding.get("provider_contract") or {}
    exact = {
        "provider": "github-models",
        "protocol": "openai-chat-completions-v1",
        "endpoint": "https://models.github.ai/inference/chat/completions",
        "allowed_host": "models.github.ai",
        "scope": "ecosystem-chat-single-governed-execution",
        "permission_required": "models: read",
        "credential_source": "ephemeral GitHub Actions GITHUB_TOKEN",
        "single_execution": True,
    }
    require(contract == exact, "provider contract changed")
    for field in ("provider", "protocol", "endpoint", "allowed_host", "scope", "permission_required", "credential_source", "single_execution"):
        require(request.get(field) == exact[field], f"authority request mismatch: {field}")

    custody = binding.get("custody_binding") or {}
    require(custody.get("mode") == "run_scoped_owned", "custody mode mismatch")
    require(custody.get("owner_repository") == "master-records/orchestration", "custody owner mismatch")
    require(custody.get("service") == "services.master_records_custody_api:app", "custody service mismatch")
    require(custody.get("workflow_preflight_required") is True, "custody preflight must be required")
    require(custody.get("preprovisioned_master_records_endpoint_required") is False, "bounded lane cannot require preprovisioned Master-Records endpoint")
    require(custody.get("preprovisioned_master_records_token_required") is False, "bounded lane cannot require preprovisioned Master-Records token")
    require(custody.get("preprovisioned_master_records_allowlist_required") is False, "bounded lane cannot require preprovisioned Master-Records allowlist")
    require(custody.get("authority_consumption_requires_healthy_custody") is True, "authority consumption must require healthy custody")

    required_before_dispatch = binding.get("required_before_dispatch") or []
    require(required_before_dispatch == [
        "valid unexpired approval receipt",
        "exact provider contract match",
        "single-use authority not previously consumed",
    ], "dispatch preconditions mismatch")
    require("Master-Records authorization bindings present" not in required_before_dispatch, "stale preprovisioned custody requirement remains")

    runtime_preconditions = binding.get("runtime_preconditions_before_authority_consumption") or []
    require(runtime_preconditions == [
        "canonical Master-Records custody source checked out",
        "run-scoped custody credentials generated and masked",
        "owned custody service started on loopback",
        "owned custody service health verified",
    ], "run-scoped custody preconditions mismatch")

    state = binding.get("current_state") or {}
    require(state.get("authority_request_present") is True, "authority request must be present")
    require(state.get("approval_receipt_observed") is False, "approval receipt cannot be inferred")
    require(state.get("authority_consumed") is False, "authority consumption cannot be inferred")
    require(state.get("dispatch_authorized") is False, "dispatch cannot be authorized")
    require(state.get("provider_execution_authorized") is False, "provider execution cannot be authorized")
    require(state.get("run_scoped_custody_implemented") is True, "run-scoped custody implementation must be recorded")
    require(state.get("run_scoped_custody_validated") is True, "run-scoped custody validation must be recorded")
    require(intake.get("dispatch_state") == "NOT_DISPATCHED", "intake cannot claim dispatch")
    require(intake.get("execution_authorized") is False, "intake cannot claim execution authority")

    for required in (
        "models: read",
        "validate_provider_execution_authority.py",
        "provider-execution-authority.github-models.consumed.json",
        "repository: master-records/orchestration",
        "services.master_records_custody_api:app",
        "Verify owned custody service health",
        "Consume authority before provider execution",
        "STEGVERSE_PROVIDER_DAILY_REQUEST_LIMIT: '1'",
    ):
        require(required in workflow, f"workflow contract missing: {required}")
    require(workflow.index("Verify owned custody service health") < workflow.index("Consume authority before provider execution"), "authority may be consumed before custody health")
    require(binding.get("authority") == NO_AUTHORITY, "binding authority boundary changed")

    print("STEGVERSE LIVE BASELINE PROVIDER AUTHORITY BINDING: REQUESTED_NOT_APPROVED / RUN_SCOPED_CUSTODY_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
