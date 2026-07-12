"""Authenticated, package-only cooperative-review transport for External Chat."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from llm_adapter.external_review_store import ReviewConflict, now_iso, store

router = APIRouter(prefix="/api/external-review", tags=["external-chat-review"])


def canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(payload)).hexdigest()


def signed_receipt(prefix: str, *parts: str) -> str:
    key = os.getenv("STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail={"reason": "review_receipt_key_not_configured"})
    signature = hmac.new(key.encode(), "\n".join(parts).encode(), hashlib.sha256).hexdigest()
    return f"{prefix}:hmac-sha256:{signature}"


def bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"reason": "bearer_token_required"})
    return authorization[7:].strip()


def require_submitter(authorization: str | None) -> None:
    expected = os.getenv("STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN", "")
    if not expected or not hmac.compare_digest(bearer(authorization), expected):
        raise HTTPException(status_code=403, detail={"reason": "submitter_auth_failed"})


def reviewer_registry() -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(os.getenv("STEGVERSE_EXTERNAL_REVIEWERS_JSON", "{}"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=503, detail={"reason": "reviewer_registry_invalid"}) from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=503, detail={"reason": "reviewer_registry_invalid"})
    return value


def parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def require_reviewer(authorization: str | None, reviewer_ref: str, scopes: set[str]) -> dict[str, Any]:
    profile = reviewer_registry().get(reviewer_ref)
    if not profile:
        raise HTTPException(status_code=403, detail={"reason": "reviewer_not_registered"})
    supplied_hash = hashlib.sha256(bearer(authorization).encode()).hexdigest()
    if not hmac.compare_digest(supplied_hash, str(profile.get("token_sha256", ""))):
        raise HTTPException(status_code=403, detail={"reason": "reviewer_auth_failed"})
    now = datetime.now(timezone.utc)
    valid_from, valid_until = parse_time(profile.get("valid_from")), parse_time(profile.get("valid_until"))
    if valid_from and now < valid_from:
        raise HTTPException(status_code=403, detail={"reason": "reviewer_delegation_not_yet_valid"})
    if valid_until and now > valid_until:
        raise HTTPException(status_code=403, detail={"reason": "reviewer_delegation_expired"})
    allowed = set(profile.get("scopes", []))
    if "*" not in allowed and not scopes.issubset(allowed):
        raise HTTPException(status_code=403, detail={"reason": "review_scope_not_delegated", "requested": sorted(scopes), "allowed": sorted(allowed)})
    if not profile.get("delegation_ref"):
        raise HTTPException(status_code=403, detail={"reason": "reviewer_delegation_ref_missing"})
    return profile


class CooperativeReviewPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"]
    packet_type: Literal["external_framework_cooperative_review_package"]
    package_id: str | None = Field(default=None, max_length=256)
    framework_id: str = Field(min_length=1, max_length=128)
    framework_name: str | None = Field(default=None, max_length=256)
    compatibility_receipt_id: str = Field(pattern=r"^external-compatibility-receipt:sha256:[a-f0-9]{64}$")
    submission_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    compatibility_result: Literal["COMPATIBILITY_EVIDENCE_READY", "PARTIAL_COMPATIBILITY_INTAKE", "FAIL_CLOSED_BOUNDARY_REVIEW"]
    submitter_opt_in: Literal[True]
    publication_requested: bool
    raw_submission_included: Literal[False]
    review_scope: list[str] = Field(min_length=1, max_length=50)
    evidence_references: list[str] = Field(default_factory=list, max_length=100)
    contact_reference: str | None = Field(default=None, max_length=512)
    boundary: dict[str, bool]

    @model_validator(mode="after")
    def canonical_boundary(self):
        required = {
            "package_is_publication_authority": False,
            "package_is_certification": False,
            "package_creates_standing": False,
            "review_may_change_result_without_receipt": False,
        }
        if self.boundary != required:
            raise ValueError("cooperative review package boundary mismatch")
        return self


class CorrectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    packet_type: Literal["external_framework_correction_request"]
    schema_version: Literal["1.0.0"]
    package_id: str = Field(min_length=1, max_length=256)
    challenged_receipt_id: str = Field(min_length=1, max_length=256)
    challenged_submission_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer_ref: str = Field(min_length=1, max_length=256)
    decision: Literal["UPHOLD", "CORRECT", "PARTIAL_CORRECTION", "INSUFFICIENT_EVIDENCE"]
    reviewed_fields: list[str] = Field(min_length=1, max_length=50)
    supporting_evidence_references: list[str] = Field(min_length=1, max_length=100)
    rationale: str = Field(min_length=1, max_length=12000)
    replacement_result: str | None = Field(default=None, max_length=128)
    replacement_receipt_id: str | None = Field(default=None, max_length=256)
    publication_authorized: Literal[False] = False

    @model_validator(mode="after")
    def replacement_pair(self):
        replacement = bool(self.replacement_result and self.replacement_receipt_id)
        if self.decision in {"CORRECT", "PARTIAL_CORRECTION"} and not replacement:
            raise ValueError("correction decisions require replacement result and receipt")
        if self.decision in {"UPHOLD", "INSUFFICIENT_EVIDENCE"} and (self.replacement_result or self.replacement_receipt_id):
            raise ValueError("non-correction decisions may not create replacement results")
        return self


@router.get("/health")
def review_health() -> dict[str, Any]:
    return {
        "status": "ok", "service": "stegverse-external-review", "schema_version": "1.0.0",
        "package_only_storage": True, "raw_artifact_storage_allowed": False,
        "submitter_auth_configured": bool(os.getenv("STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN")),
        "reviewer_registry_configured": bool(os.getenv("STEGVERSE_EXTERNAL_REVIEWERS_JSON")),
        "receipt_key_configured": bool(os.getenv("STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY")),
        "publication_authority": False, "certification_authority": False,
    }


@router.post("/packages")
def submit_review_package(payload: CooperativeReviewPackage, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_submitter(authorization)
    body = payload.model_dump(exclude={"package_id"})
    content_sha = digest(body)
    package_id = payload.package_id or f"external-review-package:sha256:{hashlib.sha256((payload.compatibility_receipt_id + payload.submission_sha256).encode()).hexdigest()}"
    intake_receipt_id = signed_receipt("external-review-intake-receipt", package_id, payload.compatibility_receipt_id, payload.submission_sha256, content_sha)
    record = {
        "package_id": package_id, "framework_id": payload.framework_id,
        "compatibility_receipt_id": payload.compatibility_receipt_id, "submission_sha256": payload.submission_sha256,
        "content_sha256": content_sha, "payload": body, "intake_receipt_id": intake_receipt_id,
        "review_state": "AWAITING_DELEGATED_REVIEW", "received_at": now_iso(),
    }
    try:
        stored, created = store.append_package(record)
    except ReviewConflict as exc:
        raise HTTPException(status_code=409, detail={"reason": "review_package_conflict", "detail": str(exc)}) from exc
    return {**stored, "created": created, "raw_submission_stored": False, "wiki_record_created": False, "publication_authorized": False, "standing_created": False}


@router.get("/packages/{package_id}")
def get_review_package(package_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_submitter(authorization)
    package = store.get_package(package_id)
    if not package:
        raise HTTPException(status_code=404, detail={"reason": "review_package_not_found"})
    return {**package, "corrections": store.list_corrections(package_id), "raw_submission_stored": False, "publication_authorized": False}


@router.post("/corrections")
def issue_correction(payload: CorrectionRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    package = store.get_package(payload.package_id)
    if not package:
        raise HTTPException(status_code=404, detail={"reason": "review_package_not_found"})
    if payload.challenged_receipt_id != package["compatibility_receipt_id"]:
        raise HTTPException(status_code=409, detail={"reason": "challenged_receipt_identity_mismatch"})
    if payload.challenged_submission_sha256 != package["submission_sha256"]:
        raise HTTPException(status_code=409, detail={"reason": "challenged_submission_identity_mismatch"})
    scopes = {f"field:{field}" for field in payload.reviewed_fields}
    if package["payload"].get("publication_requested"):
        scopes.add("publication_review")
    profile = require_reviewer(authorization, payload.reviewer_ref, scopes)
    body, issued_at = payload.model_dump(), now_iso()
    content_sha = digest(body)
    correction_receipt_id = signed_receipt("external-framework-correction-receipt", payload.package_id, payload.challenged_receipt_id, payload.reviewer_ref, str(profile["delegation_ref"]), payload.decision, content_sha, issued_at)
    record = {
        "correction_receipt_id": correction_receipt_id, "package_id": payload.package_id,
        "challenged_receipt_id": payload.challenged_receipt_id, "reviewer_ref": payload.reviewer_ref,
        "reviewer_delegation_ref": profile["delegation_ref"], "decision": payload.decision,
        "content_sha256": content_sha, "payload": body, "issued_at": issued_at,
    }
    try:
        stored, created = store.append_correction(record)
    except ReviewConflict as exc:
        raise HTTPException(status_code=409, detail={"reason": "correction_conflict", "detail": str(exc)}) from exc
    return {**stored, "created": created, "reviewer_identity_verified": True, "reviewer_delegation_verified": True, "review_scope_verified": True, "publication_authorized": False, "certification_created": False, "standing_created": False}
