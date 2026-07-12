"""Separately authorized repository-mutation adapter for External Chat.

Consumes only stored ALLOW_PUBLICATION_CANDIDATE transitions. The adapter is
disabled by default and can mutate only StegVerse-Labs/admissibility-wiki paths
under docs/external-frameworks after commit-time authority, delegation, policy,
freshness, source-head, target-blob, and receipt identity checks pass.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from llm_adapter.external_review_store import now_iso

router = APIRouter(prefix="/api/external-review", tags=["external-chat-mutation"])

ALLOWED_REPOSITORY = "StegVerse-Labs/admissibility-wiki"
ALLOWED_PREFIX = "docs/external-frameworks/"


def _db_path() -> str:
    return os.getenv("STEGVERSE_EXTERNAL_REVIEW_DB", "/tmp/stegverse-external-review.db")


def _connect() -> sqlite3.Connection:
    Path(_db_path()).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(_db_path())
    db.row_factory = sqlite3.Row
    db.execute(
        """CREATE TABLE IF NOT EXISTS repository_mutation_receipts (
        mutation_receipt_id TEXT PRIMARY KEY,
        publication_transition_id TEXT NOT NULL UNIQUE,
        repository_full_name TEXT NOT NULL,
        target_path TEXT NOT NULL,
        content_sha256 TEXT NOT NULL,
        previous_blob_sha TEXT,
        commit_sha TEXT NOT NULL,
        actor_ref TEXT NOT NULL,
        delegation_ref TEXT NOT NULL,
        policy_ref TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        committed_at TEXT NOT NULL
        )"""
    )
    return db


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"reason": "bearer_token_required"})
    return authorization[7:].strip()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _registry() -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(os.getenv("STEGVERSE_EXTERNAL_MUTATORS_JSON", "{}"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=503, detail={"reason": "mutator_registry_invalid"}) from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=503, detail={"reason": "mutator_registry_invalid"})
    return value


def _require_mutator(authorization: str | None, actor_ref: str, framework_id: str) -> dict[str, Any]:
    profile = _registry().get(actor_ref)
    if not profile:
        raise HTTPException(status_code=403, detail={"reason": "mutator_not_registered"})
    supplied_hash = hashlib.sha256(_bearer(authorization).encode()).hexdigest()
    if not hmac.compare_digest(supplied_hash, str(profile.get("token_sha256", ""))):
        raise HTTPException(status_code=403, detail={"reason": "mutator_auth_failed"})
    now = datetime.now(timezone.utc)
    valid_from = _parse_time(profile["valid_from"]) if profile.get("valid_from") else None
    valid_until = _parse_time(profile["valid_until"]) if profile.get("valid_until") else None
    if valid_from and now < valid_from:
        raise HTTPException(status_code=403, detail={"reason": "mutator_delegation_not_yet_valid"})
    if valid_until and now > valid_until:
        raise HTTPException(status_code=403, detail={"reason": "mutator_delegation_expired"})
    required = {
        f"repository:{ALLOWED_REPOSITORY}",
        "path:docs/external-frameworks/*",
        f"framework:{framework_id}",
        "repository:mutate",
    }
    allowed = set(profile.get("scopes", []))
    if "*" not in allowed and not required.issubset(allowed):
        raise HTTPException(status_code=403, detail={"reason": "mutation_scope_not_delegated", "required": sorted(required)})
    if not profile.get("delegation_ref"):
        raise HTTPException(status_code=403, detail={"reason": "mutator_delegation_ref_missing"})
    return profile


def _github_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "StegVerse-External-Chat-Mutation-Adapter",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:2000]
        raise HTTPException(status_code=502, detail={"reason": "github_api_error", "status": exc.code, "detail": detail}) from exc
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=502, detail={"reason": "github_transport_error", "detail": str(exc)}) from exc


class RepositoryMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"]
    request_type: Literal["external_framework_repository_mutation_request"]
    publication_transition_id: str = Field(min_length=1, max_length=256)
    actor_ref: str = Field(min_length=1, max_length=256)
    repository_full_name: Literal["StegVerse-Labs/admissibility-wiki"]
    target_path: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1, max_length=1_000_000)
    expected_repository_head_sha: str = Field(pattern=r"^[a-f0-9]{40}$")
    expected_target_blob_sha: str | None = Field(default=None, pattern=r"^[a-f0-9]{40}$")
    commit_message: str = Field(min_length=1, max_length=256)
    authority_ref: str = Field(min_length=1, max_length=512)
    delegation_ref: str = Field(min_length=1, max_length=512)
    policy_ref: str = Field(min_length=1, max_length=512)
    freshness_valid_until: str
    branch: Literal["main"] = "main"

    @model_validator(mode="after")
    def path_and_freshness(self):
        if not self.target_path.startswith(ALLOWED_PREFIX) or ".." in self.target_path:
            raise ValueError("target path outside External Chat wiki boundary")
        if _parse_time(self.freshness_valid_until) <= datetime.now(timezone.utc):
            raise ValueError("freshness window expired")
        return self


@router.get("/repository-mutation/health")
def mutation_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "stegverse-external-publication-mutation",
        "schema_version": "1.0.0",
        "mutation_enabled": os.getenv("STEGVERSE_EXTERNAL_MUTATION_ENABLED", "false").lower() == "true",
        "allowed_repository": ALLOWED_REPOSITORY,
        "allowed_path_prefix": ALLOWED_PREFIX,
        "commit_time_revalidation_required": True,
        "publication_transition_is_mutation_authority": False,
    }


@router.post("/repository-mutations")
def mutate_repository(payload: RepositoryMutationRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if os.getenv("STEGVERSE_EXTERNAL_MUTATION_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=503, detail={"reason": "repository_mutation_disabled"})
    github_token = os.getenv("STEGVERSE_EXTERNAL_GITHUB_TOKEN", "")
    receipt_key = os.getenv("STEGVERSE_EXTERNAL_MUTATION_RECEIPT_KEY", "")
    required_policy = os.getenv("STEGVERSE_EXTERNAL_MUTATION_POLICY_REF", "")
    if not github_token or not receipt_key or not required_policy:
        raise HTTPException(status_code=503, detail={"reason": "mutation_configuration_incomplete"})
    if payload.policy_ref != required_policy:
        raise HTTPException(status_code=403, detail={"reason": "commit_time_policy_mismatch"})

    with _connect() as db:
        row = db.execute(
            "SELECT * FROM publication_transitions WHERE publication_transition_id = ?",
            (payload.publication_transition_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"reason": "publication_transition_not_found"})
        publication = dict(row)
        publication_payload = json.loads(publication["payload_json"])
        if publication["decision"] != "ALLOW_PUBLICATION_CANDIDATE":
            raise HTTPException(status_code=409, detail={"reason": "publication_transition_not_allowed"})
        if publication["target_path"] != payload.target_path:
            raise HTTPException(status_code=409, detail={"reason": "publication_target_identity_mismatch"})
        package = db.execute("SELECT * FROM review_packages WHERE package_id = ?", (publication["package_id"],)).fetchone()
        correction = db.execute("SELECT * FROM correction_receipts WHERE correction_receipt_id = ?", (publication["correction_receipt_id"],)).fetchone()
        if not package or not correction:
            raise HTTPException(status_code=409, detail={"reason": "publication_evidence_chain_incomplete"})
        framework_id = package["framework_id"]

    profile = _require_mutator(authorization, payload.actor_ref, framework_id)
    if payload.delegation_ref != profile["delegation_ref"]:
        raise HTTPException(status_code=403, detail={"reason": "commit_time_delegation_mismatch"})
    if not payload.authority_ref:
        raise HTTPException(status_code=403, detail={"reason": "commit_time_authority_missing"})

    head = _github_json("GET", f"https://api.github.com/repos/{ALLOWED_REPOSITORY}/git/ref/heads/{payload.branch}", github_token)
    current_head = head.get("object", {}).get("sha")
    if current_head != payload.expected_repository_head_sha:
        raise HTTPException(status_code=409, detail={"reason": "repository_head_drift", "observed": current_head})

    content_url = f"https://api.github.com/repos/{ALLOWED_REPOSITORY}/contents/{payload.target_path}?ref={payload.branch}"
    observed_blob_sha: str | None = None
    try:
        existing = _github_json("GET", content_url, github_token)
        observed_blob_sha = existing.get("sha")
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        if detail.get("status") != 404:
            raise
    if observed_blob_sha != payload.expected_target_blob_sha:
        raise HTTPException(status_code=409, detail={"reason": "target_blob_drift", "observed": observed_blob_sha})

    content_sha = hashlib.sha256(payload.content.encode()).hexdigest()
    request_body: dict[str, Any] = {
        "message": payload.commit_message,
        "content": base64.b64encode(payload.content.encode()).decode(),
        "branch": payload.branch,
    }
    if observed_blob_sha:
        request_body["sha"] = observed_blob_sha
    result = _github_json("PUT", f"https://api.github.com/repos/{ALLOWED_REPOSITORY}/contents/{payload.target_path}", github_token, request_body)
    commit_sha = result.get("commit", {}).get("sha")
    new_blob_sha = result.get("content", {}).get("sha")
    if not commit_sha or not new_blob_sha:
        raise HTTPException(status_code=502, detail={"reason": "github_mutation_receipt_incomplete"})

    committed_at = now_iso()
    material = "\n".join([
        payload.publication_transition_id, payload.actor_ref, profile["delegation_ref"], payload.policy_ref,
        payload.repository_full_name, payload.target_path, content_sha, commit_sha, new_blob_sha, committed_at,
    ])
    mutation_receipt_id = "external-framework-repository-mutation-receipt:hmac-sha256:" + hmac.new(
        receipt_key.encode(), material.encode(), hashlib.sha256
    ).hexdigest()
    receipt_payload = {
        "receipt_type": "external_framework_repository_mutation_receipt",
        "schema_version": "1.0.0",
        "mutation_receipt_id": mutation_receipt_id,
        "publication_transition_id": payload.publication_transition_id,
        "repository_full_name": payload.repository_full_name,
        "target_path": payload.target_path,
        "previous_blob_sha": observed_blob_sha,
        "new_blob_sha": new_blob_sha,
        "content_sha256": content_sha,
        "commit_sha": commit_sha,
        "actor_ref": payload.actor_ref,
        "delegation_ref": profile["delegation_ref"],
        "authority_ref": payload.authority_ref,
        "policy_ref": payload.policy_ref,
        "committed_at": committed_at,
        "commit_time_revalidation": {
            "authority": "PASS", "delegation": "PASS", "policy": "PASS", "freshness": "PASS",
            "repository_head": "PASS", "target_blob": "PASS", "publication_identity": "PASS",
        },
        "boundary": {
            "mutation_receipt_is_certification": False,
            "mutation_receipt_creates_standing": False,
            "publication_implies_general_compatibility": False,
        },
    }
    with _connect() as db:
        existing = db.execute("SELECT * FROM repository_mutation_receipts WHERE publication_transition_id = ?", (payload.publication_transition_id,)).fetchone()
        if existing:
            if existing["commit_sha"] != commit_sha or existing["content_sha256"] != content_sha:
                raise HTTPException(status_code=409, detail={"reason": "repository_mutation_receipt_conflict"})
        else:
            db.execute(
                """INSERT INTO repository_mutation_receipts
                (mutation_receipt_id, publication_transition_id, repository_full_name, target_path,
                 content_sha256, previous_blob_sha, commit_sha, actor_ref, delegation_ref, policy_ref,
                 payload_json, committed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (mutation_receipt_id, payload.publication_transition_id, payload.repository_full_name,
                 payload.target_path, content_sha, observed_blob_sha, commit_sha, payload.actor_ref,
                 profile["delegation_ref"], payload.policy_ref, json.dumps(receipt_payload, sort_keys=True), committed_at),
            )
            db.commit()
    return receipt_payload
