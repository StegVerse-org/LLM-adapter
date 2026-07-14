"""Validate observed workflow evidence for the system-boundary workstream.

This module records observation state only. It does not execute workflows, grant
release authority, enable production binding, or convert missing status into PASS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

VALID_RESULTS = {"PENDING", "PASS", "FAIL"}


@dataclass(frozen=True)
class WorkflowEvidenceResult:
    accepted: bool
    verified: bool
    result: str
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "verified": self.verified,
            "result": self.result,
            "errors": list(self.errors),
        }


def validate_workflow_evidence(record: Mapping[str, Any]) -> WorkflowEvidenceResult:
    errors: list[str] = []
    if not isinstance(record, Mapping):
        return WorkflowEvidenceResult(False, False, "FAIL", ("record must be an object",))

    required = {
        "schema_version",
        "repository",
        "workflow",
        "required_commit",
        "observed_commit",
        "run_id",
        "run_url",
        "result",
        "production_binding_enabled",
        "release_authorized",
    }
    if set(record) != required:
        errors.append("workflow evidence keys do not match required contract")
        return WorkflowEvidenceResult(False, False, "FAIL", tuple(errors))

    if record["schema_version"] != "stegverse.system_boundary.workflow_evidence.v0.1":
        errors.append("unsupported schema_version")
    if record["repository"] != "StegVerse-org/LLM-adapter":
        errors.append("repository mismatch")
    if record["workflow"] != ".github/workflows/validate.yml":
        errors.append("workflow mismatch")
    if record["result"] not in VALID_RESULTS:
        errors.append("result must be PENDING, PASS, or FAIL")
    if record["production_binding_enabled"] is not False:
        errors.append("production_binding_enabled must remain false")
    if record["release_authorized"] is not False:
        errors.append("release_authorized must remain false")

    result = record.get("result", "FAIL")
    if result == "PENDING":
        for key in ("observed_commit", "run_id", "run_url"):
            if record.get(key) is not None:
                errors.append(f"{key} must be null while result is PENDING")
    else:
        for key in ("observed_commit", "run_id", "run_url"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                errors.append(f"{key} is required when result is {result}")
        if result == "PASS" and record.get("observed_commit") != record.get("required_commit"):
            errors.append("PASS must be bound to the required commit")

    if errors:
        return WorkflowEvidenceResult(False, False, result, tuple(errors))
    return WorkflowEvidenceResult(True, result == "PASS", result, ())
