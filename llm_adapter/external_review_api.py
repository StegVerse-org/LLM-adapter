"""Authenticated, package-only cooperative-review transport for External Chat."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException, Query
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


def load_registry(env_name: str, error_reason: str) -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(os.getenv(env_name, "{}"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=503, detail={"reason": error_reason}) from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=503, detail={"reason": error_reason})
    return value


def parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def require_registry_actor(
    authorization: str | None,
    actor_ref: str,
    scopes: set[str],
    *,
    env_name: str,
    missing_reason: str,
    auth_reason: str,
    scope_reason: str,
) -> dict[str, Any]:
    profile = load_registry(env_name, f"{missing_reason}_registry_invalid").get(actor_ref)
    if not profile:
        raise HTTPException(status_code=403, detail={"reason": missing_reason})
    supplied_hash = hashlib.sha256(bearer(authorization).encode()).hexdigest()
    if not hmac.compare_digest(supplied_hash, str(profile.get("token_sha256", ""))):
        raise HTTPException(status_code=403, detail={"reason": auth_reason})
    now = datetime.now(timezone.utc)
    valid_from, valid_until = parse_time(profile.get("valid_from")), parse_time(profile.get("valid_until"))
    if valid_from and now < valid_from:
        raise HTTPException(status_code=403, detail={"reason": f"{missing_reason}_delegation_not_yet_valid"})
    if valid_until and now > valid_until:
        raise HTTPException(status_code=403, detail={"reason": f"{missing_reason}_delegation_expired"})
    allowed = set(profile.get("scopes", []))
    if "*" not in allowed and not scopes.issubset(allowed):
        raise HTTPException(status_code=403, detail={"reason": scope_reason, "requested": sorted(scopes), "allowed": sorted(allowed)})
    if not profile.get("delegation_ref"):
        raise HTTPException(status_code=403, detail={"reason": f"{missing_reason}_delegation_ref_missing"})
    return profile


def require_reviewer(authorization: str | None, reviewer_ref: str, scopes: set[str]) -> dict[str, Any]:
    return require_registry_actor(
        authorization, reviewer_ref, scopes,
        env_name="STEGVERSE_EXTERNAL_REVIEWERS_JSON",
        missing_reason="reviewer_not_registered",
        auth_reason="reviewer_auth_failed",
        scope_reason="review_scope_not_delegated",
    )


def require_publisher(authorization: str | None, publisher_ref: str, scopes: set[str]) -> dict[str, Any]:
    return require_registry_actor(
        authorization, publisher_ref, scopes,
        env_name="STEGVERSE_EXTERNAL_PUBLISHERS_JSON",
        missing_reason="publisher_not_registered",
        auth_reason="publisher_auth_failed",
        scope_reason="publication_scope_not_delegated",
    )


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


class PublicationTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"]
    transition_type: Literal["external_framework_wiki_publication_transition"]
    package_id: str = Field(min_length=1, max_length=256)
    correction_receipt_id: str = Field(min_length=1, max_length=256)
    publisher_ref: str = Field(min_length=1, max_length=256)
    target_path: str = Field(pattern=r"^docs/external-frameworks/(reports/)?[a-z0-9][a-z0-9._/-]*$")
    decision: Literal["ALLOW_PUBLICATION_CANDIDATE", "DENY_PUBLICATION", "REVIEW_REQUIRED"]
    source_commit_ref: str = Field(min_length=1, max_length=256)
    evidence_references: list[str] = Field(min_length=1, max_length=100)
    publication_executed: Literal[False] = False
    boundary: dict[str, bool]

    @model_validator(mode="after")
    def publication_boundary(self):
        required = {
            "transition_is_not_repository_write": True,
            "transition_is_not_certification": True,
            "transition_creates_no_standing": True,
            "separate_repository_mutation_required": True,
        }
        if self.boundary != required:
            raise ValueError("publication transition boundary mismatch")
        return self


@router.get("/health")
def review_health() -> dict[str, Any]:
    return {
        "status": "ok", "service": "stegverse-external-review", "schema_version": "1.1.0",
        "package_only_storage": True, "raw_artifact_storage_allowed": False,
        "submitter_auth_configured": bool(os.getenv("STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN")),
        "reviewer_registry_configured": bool(os.getenv("STEGVERSE_EXTERNAL_REVIEWERS_JSON")),
        "publisher_registry_configured": bool(os.getenv("STEGVERSE_EXTERNAL_PUBLISHERS_JSON")),
        "receipt_key_configured": bool(os.getenv("STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY")),
        "publication_transition_supported": True,
        "publication_execution_authority": False, "certification_authority": False,
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


@router.get("/reviewer/packages/{package_id}")
def reviewer_get_package(
    package_id: str,
    reviewer_ref: str = Query(min_length=1, max_length=256),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    profile = require_reviewer(authorization, reviewer_ref, {"package:read"})
    package = store.get_package(package_id)
    if not package:
        raise HTTPException(status_code=404, detail={"reason": "review_package_not_found"})
    return {
        **package,
        "corrections": store.list_corrections(package_id),
        "reviewer_ref": reviewer_ref,
        "reviewer_delegation_ref": profile["delegation_ref"],
        "reviewer_identity_verified": True,
        "raw_submission_stored": False,
        "publication_authorized": False,
    }


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


@router.post("/publication-transitions")
def create_publication_transition(payload: PublicationTransitionRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    package = store.get_package(payload.package_id)
    if not package:
        raise HTTPException(status_code=404, detail={"reason": "review_package_not_found"})
    correction = store.get_correction(payload.correction_receipt_id)
    if not correction or correction["package_id"] != payload.package_id:
        raise HTTPException(status_code=409, detail={"reason": "correction_receipt_identity_mismatch"})
    if correction["decision"] == "INSUFFICIENT_EVIDENCE" and payload.decision == "ALLOW_PUBLICATION_CANDIDATE":
        raise HTTPException(status_code=409, detail={"reason": "insufficient_evidence_cannot_allow_publication"})
    scopes = {"publication:wiki", f"framework:{package['framework_id']}"}
    profile = require_publisher(authorization, payload.publisher_ref, scopes)
    body, issued_at = payload.model_dump(), now_iso()
    content_sha = digest(body)
    transition_id = signed_receipt(
        "external-framework-publication-transition",
        payload.package_id, payload.correction_receipt_id, payload.publisher_ref,
        str(profile["delegation_ref"]), payload.target_path, payload.decision, content_sha, issued_at,
    )
    record = {
        "publication_transition_id": transition_id,
        "package_id": payload.package_id,
        "correction_receipt_id": payload.correction_receipt_id,
        "publisher_ref": payload.publisher_ref,
        "publisher_delegation_ref": profile["delegation_ref"],
        "target_path": payload.target_path,
        "decision": payload.decision,
        "content_sha256": content_sha,
        "payload": body,
        "issued_at": issued_at,
    }
    try:
        stored, created = store.append_publication(record)
    except ReviewConflict as exc:
        raise HTTPException(status_code=409, detail={"reason": "publication_transition_conflict", "detail": str(exc)}) from exc
    return {
        **stored,
        "created": created,
        "publisher_identity_verified": True,
        "publisher_delegation_verified": True,
        "publication_scope_verified": True,
        "publication_executed": False,
        "repository_mutation_authorized": False,
        "certification_created": False,
        "standing_created": False,
        "required_next_transition": "separately_authorized_repository_mutation" if payload.decision == "ALLOW_PUBLICATION_CANDIDATE" else None,
    }
