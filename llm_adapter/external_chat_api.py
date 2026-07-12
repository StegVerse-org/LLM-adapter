"""HTTP router for bounded External Chat compatibility testing."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from llm_adapter.external_framework_compatibility import evaluate_submission

router = APIRouter(prefix="/api", tags=["external-chat"])


class ExternalFrameworkSubmission(BaseModel):
    model_config = ConfigDict(extra="allow")
    framework_id: str = Field(min_length=1, max_length=128)
    framework_name: str = Field(min_length=1, max_length=256)
    source_references: list[str] = Field(default_factory=list, max_length=50)
    input_artifact_type: str | None = Field(default=None, max_length=512)
    output_artifact_type: str | None = Field(default=None, max_length=512)
    actor_or_authority_model: str | None = Field(default=None, max_length=4000)
    evidence_model: str | None = Field(default=None, max_length=4000)
    policy_or_rule_model: str | None = Field(default=None, max_length=4000)
    delegation_model: str | None = Field(default=None, max_length=4000)
    decision_or_result_model: str | None = Field(default=None, max_length=4000)
    receipt_or_trace_model: str | None = Field(default=None, max_length=4000)
    reconstruction_model: str | None = Field(default=None, max_length=4000)
    fail_closed_conditions: list[str] = Field(default_factory=list, max_length=100)
    execution_authority_claim: bool = False
    commit_time_authority_claim: bool = False
    certification_claim: bool = False
    equivalence_claim: bool = False
    sample_artifact: dict[str, Any] | list[Any] | str | None = None


@router.post("/external-framework-compatibility")
def external_framework_compatibility(payload: ExternalFrameworkSubmission) -> dict[str, Any]:
    body = payload.model_dump()
    encoded_size = len(str(body).encode("utf-8"))
    if encoded_size > 250_000:
        raise HTTPException(status_code=413, detail={"reason": "submission_too_large", "maximum_bytes": 250000})
    result = evaluate_submission(body)
    return {
        **result,
        "submission_retained": False,
        "raw_artifact_published": False,
        "execution_performed": False,
        "wiki_record_created": False,
        "review_required_before_publication": True,
    }
