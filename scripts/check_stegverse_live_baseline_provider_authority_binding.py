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

    require(binding.get("schema_version") == "1.0.0", "unsupported schema_version")
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

    state = binding.get("current_state") or {}
    require(state.get("authority_request_present") is True, "authority request must be present")
    require(state.get("approval_receipt_observed") is False, "approval receipt cannot be inferred")
    require(state.get("authority_consumed") is False, "authority consumption cannot be inferred")
    require(state.get("dispatch_authorized") is False, "dispatch cannot be authorized")
    require(state.get("provider_execution_authorized") is False, "provider execution cannot be authorized")
    require(intake.get("dispatch_state") == "NOT_DISPATCHED", "intake cannot claim dispatch")
    require(intake.get("execution_authorized") is False, "intake cannot claim execution authority")

    require("models: read" in workflow, "permission-bearing workflow missing models permission")
    require("validate_provider_execution_authority.py" in workflow, "workflow does not validate authority")
    require("provider-execution-authority.github-models.consumed.json" in workflow, "workflow does not consume authority")
    require("STEGVERSE_PROVIDER_DAILY_REQUEST_LIMIT: '1'" in workflow, "single request quota missing")
    require(binding.get("authority") == NO_AUTHORITY, "binding authority boundary changed")

    print("STEGVERSE LIVE BASELINE PROVIDER AUTHORITY BINDING: REQUESTED_NOT_APPROVED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
