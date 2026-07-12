"""Deployable governed HTTP gateway for StegVerse Ecosystem Chat.

The service accepts text-only requests, preserves canonical transition identity,
rejects restricted administration and credential-shaped input, applies a bounded
in-memory rate limit, and returns a non-authorizing response contract.
"""
from __future__ import annotations

import os
import re
import time
from collections import defaultdict, deque
from hashlib import sha256
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

from llm_adapter.ai_entry_backend_service import build_ai_entry_backend_response

RESTRICTED_PATTERNS = (
    re.compile(r"\b(secret|token|credential|password|api[_ -]?key|deploy key|private key)\b", re.I),
    re.compile(r"\b(rm\s+-rf|git\s+push|force[- ]?push|delete\s+(repo|repository|branch|workflow|release|tag))\b", re.I),
    re.compile(r"\b(permission|collaborator|webhook|branch protection|dns|infrastructure setting)\b", re.I),
)

ALLOWED_ROUTES = {
    "Site", "repo-standards", "StegVerse-002", "formalism-tests", "Continuity",
    "Publisher", "Solver", "Restricted admin", "Unknown",
}


class TransitionIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transition_id: str = Field(min_length=1, max_length=256)
    run_id: str = Field(min_length=1, max_length=256)
    event_id: str = Field(min_length=1, max_length=256)
    origin_manifest_id: str = Field(min_length=1, max_length=256)
    parent_transition_id: str | None = None
    previous_receipt_id: str | None = None


class EcosystemChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=12000)
    session_id: str = Field(min_length=1, max_length=256)
    requested_route: str = "Unknown"
    transition_intent: str = "explain"
    transition_destination: str = "ecosystem-chat.html#how-it-works"
    goal: str = "user advancement console with governed task boundaries"
    execution_model: str = "allowlisted_task_request_only"
    raw_shell_allowed: bool = False
    authority_required: bool = True
    rate_limit_required: bool = True
    receipt_required_for_execution: bool = True
    interaction_profile: dict[str, int] = Field(default_factory=dict)
    interaction_bands: list[str] = Field(default_factory=list)
    math_solver_supported: bool = True
    transition_identity: TransitionIdentity

    @field_validator("requested_route")
    @classmethod
    def validate_route(cls, value: str) -> str:
        return value if value in ALLOWED_ROUTES else "Unknown"

    @field_validator("raw_shell_allowed")
    @classmethod
    def shell_must_be_disabled(cls, value: bool) -> bool:
        if value:
            raise ValueError("raw_shell_allowed must be false")
        return value

    @field_validator("authority_required", "rate_limit_required", "receipt_required_for_execution")
    @classmethod
    def required_governance_flags(cls, value: bool) -> bool:
        if not value:
            raise ValueError("governance requirement flag must be true")
        return value


class WindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> tuple[bool, int]:
        current = time.time() if now is None else now
        bucket = self._events[key]
        threshold = current - self.window_seconds
        while bucket and bucket[0] <= threshold:
            bucket.popleft()
        if len(bucket) >= self.limit:
            retry_after = max(1, int(bucket[0] + self.window_seconds - current))
            return False, retry_after
        bucket.append(current)
        return True, 0


RATE_LIMIT = int(os.getenv("STEGVERSE_CHAT_RATE_LIMIT", "20"))
RATE_WINDOW_SECONDS = int(os.getenv("STEGVERSE_CHAT_RATE_WINDOW_SECONDS", "3600"))
limiter = WindowRateLimiter(RATE_LIMIT, RATE_WINDOW_SECONDS)

app = FastAPI(title="StegVerse Ecosystem Chat Gateway", version="1.0.0")
allowed_origins = [
    value.strip() for value in os.getenv(
        "STEGVERSE_ALLOWED_ORIGINS",
        "https://stegverse-labs.github.io,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",") if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-SteGVerse-Session"],
)


def is_restricted(message: str, requested_route: str) -> bool:
    return requested_route == "Restricted admin" or any(pattern.search(message) for pattern in RESTRICTED_PATTERNS)


def gateway_receipt_id(payload: EcosystemChatRequest, status: str) -> str:
    material = "\n".join([
        payload.transition_identity.transition_id,
        payload.transition_identity.run_id,
        payload.session_id,
        status,
        payload.message,
    ])
    return "gateway-receipt:sha256:" + sha256(material.encode("utf-8")).hexdigest()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "stegverse-ecosystem-chat-gateway",
        "schema_version": "1.0.0",
        "execution_authority": False,
        "final_receipt_authority": False,
        "master_records_authority": False,
    }


@app.post("/api/ecosystem-chat")
def ecosystem_chat(payload: EcosystemChatRequest, request: Request) -> dict[str, Any]:
    client_key = request.client.host if request.client else payload.session_id
    allowed, retry_after = limiter.allow(f"{client_key}:{payload.session_id}")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"task_status": "rejected", "reason": "rate_limit", "retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )

    restricted = is_restricted(payload.message, payload.requested_route)
    backend = build_ai_entry_backend_response(payload.message).to_dict()
    identity = payload.transition_identity.model_dump()

    if restricted:
        task_status = "pending_authority"
        response_text = (
            "This request contains restricted administration or credential-shaped content. "
            "The public gateway performed no execution and routed the request to separate authority review."
        )
        routed_module = "Restricted admin"
        next_action = "Create a separately authorized governed task with bounded scope and receipt requirements."
    else:
        task_status = "preview_only"
        response_text = backend["stegverse_response"]
        routed_module = payload.requested_route if payload.requested_route != "Unknown" else backend["primary_route"]
        next_action = "Continue through hybrid-collab-bridge normalization and governed delegation evaluation."

    receipt_id = gateway_receipt_id(payload, task_status)
    return {
        "response": response_text,
        "routed_module": routed_module,
        "task_status": task_status,
        "receipt_id": receipt_id,
        "receipt_class": "GATEWAY_INTAKE_RECEIPT",
        "final_receipt": False,
        "next_action": next_action,
        "transition_id": identity["transition_id"],
        "run_id": identity["run_id"],
        "event_id": identity["event_id"],
        "origin_manifest_id": identity["origin_manifest_id"],
        "transition_candidate": {
            "schema_version": "1.0.0",
            "record_type": "governed_transition_relationship",
            "transition_id": identity["transition_id"],
            "run_id": identity["run_id"],
            "lifecycle_state": "DECLARED",
            "origin": {
                "origin_class": "SITE_INPUT",
                "event_id": identity["event_id"],
                "origin_manifest_id": identity["origin_manifest_id"],
                "source_ref": "StegVerse-Labs/Site/ecosystem-chat.html",
            },
            "relationships": {
                "parent_transition_id": identity.get("parent_transition_id"),
                "previous_receipt_id": identity.get("previous_receipt_id"),
                "target_ref": "repository:StegVerse-Labs/hybrid-collab-bridge",
                "task_ref": f"task:ecosystem-chat:{payload.transition_intent}",
            },
            "governance": {
                "admissibility_result": "PENDING",
                "commit_time_validity": "PENDING",
                "execution_authorized": False,
            },
            "continuity": {
                "gateway_receipt_id": receipt_id,
                "final_receipt_id": None,
                "master_record_status": "NOT_YET_SUBMITTED",
                "reconstruction_status": "NOT_YET_CHECKED",
            },
        },
        "interaction_profile": payload.interaction_profile,
        "authority": {
            "gateway_may_execute": False,
            "gateway_receipt_is_final": False,
            "site_grants_admissibility": False,
            "master_records_installed": False,
        },
    }
