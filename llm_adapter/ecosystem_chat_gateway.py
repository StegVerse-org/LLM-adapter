"""Deployable governed HTTP gateway for StegVerse Ecosystem Chat.

`POST /api/ecosystem-chat` is manifest-bound transport. It translates a chat
turn into the SDK's `stegverse.route.ecosystem-chat.v1` manifest, hands it to
`stegverse.manifest_execution.execute_manifest` through `sdk_boundary`, and
returns the SDK disposition. The manifest's route selects processing; the
caller's `requested_route` and keyword patterns do not. The gateway generates
no response, calls no provider, decides no admissibility, reads no provider or
Master Records credential, and writes no Master Records record (Master Records
is non-gating).
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from llm_adapter import collab_ingress
from llm_adapter.governed_chat_pipeline import get_transition_status
from llm_adapter.transition_store import store

SURFACE = "ecosystem-chat-gateway"

#: Accepted for request-shape compatibility. Not consulted: the manifest route
#: selects processing.
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
STORAGE_DURABLE_ACROSS_RESTARTS = os.getenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "false").lower() == "true"
limiter = WindowRateLimiter(RATE_LIMIT, RATE_WINDOW_SECONDS)

app = FastAPI(title="StegVerse Ecosystem Chat Gateway", version="1.3.0")
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


def ecosystem_chat_request(payload: "EcosystemChatRequest") -> dict[str, Any]:
    """The SDK's Ecosystem Chat processor request for one turn.

    `requested_topic` is the caller's declared intent. It only populates the
    manifest draft; the route is fixed by the manifest, not by the topic.
    """
    return {
        "schema": collab_ingress.ROUTES[collab_ingress.ECOSYSTEM_CHAT]["request_schema"],
        "session_ref": payload.session_id,
        "message": payload.message,
        "requested_topic": payload.transition_intent,
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "stegverse-ecosystem-chat-gateway",
        "schema_version": "1.3.0",
        "native_executor": "STEGVERSE_AI_ENTITY",
        "native_executor_status": "MANIFEST_BOUND_TRANSPORT",
        "bounded_response_pipeline": False,
        "manifest_route": collab_ingress.ROUTES[collab_ingress.ECOSYSTEM_CHAT]["route_id"],
        "processing_selected_by": "MANIFEST_DECLARED_ROUTE",
        "transition_status_lookup": True,
        "sqlite_transition_store": True,
        "storage_durable_across_restarts": STORAGE_DURABLE_ACROSS_RESTARTS,
        "local_persistence_is_master_records_organization_record": False,
        "custody_queue": False,
        "master_records_submission_enabled": False,
        "governed_provider_enabled": False,
        "provider_output_is_authority": False,
        "provider_failure_falls_back": False,
        "execution_authority": False,
        "repository_mutation_authority": False,
        "final_response_receipt_authority": False,
        "master_records_authority": False,
    }


@app.get("/api/transitions/{transition_id}")
def transition_status(transition_id: str) -> dict[str, Any]:
    record = get_transition_status(transition_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"reason": "transition_not_found"})
    custody = store.custody_status(transition_id)
    return {
        "transition_id": record["transition_id"],
        "run_id": record["run_id"],
        "lifecycle_state": record["lifecycle_state"],
        "admissibility_result": record["governance"]["admissibility_result"],
        "commit_time_validity": record["governance"]["commit_time_validity"],
        "final_receipt_id": record["continuity"]["final_receipt_id"],
        "master_record_status": record["continuity"]["master_record_status"],
        "master_record_ref": record["continuity"].get("master_record_ref"),
        "reconstruction_status": record["continuity"]["reconstruction_status"],
        "provider": record.get("provider"),
        "sqlite_persisted": True,
        "storage_durable_across_restarts": STORAGE_DURABLE_ACROSS_RESTARTS,
        "local_persistence_is_custody": False,
        "custody_submission": custody,
        "relationship": record,
    }


@app.post("/api/ecosystem-chat")
def ecosystem_chat(payload: EcosystemChatRequest, request: Request) -> JSONResponse:
    """Translate one chat turn into the Ecosystem Chat manifest and return the SDK disposition.

    The manifest's route (`stegverse.route.ecosystem-chat.v1`) selects
    processing. `requested_route` is not consulted and no keyword pattern is
    evaluated: neither may select processing. This gateway generates no
    response, calls no provider, decides no admissibility, and writes no
    transition or Master Records record; the receiving organization does the
    processing once the manifest is admitted. Without the canonical
    organization boundary the disposition is FAIL_CLOSED
    CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED.
    """
    client_key = request.client.host if request.client else payload.session_id
    allowed, retry_after = limiter.allow(f"{client_key}:{payload.session_id}")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"task_status": "rejected", "reason": "rate_limit", "retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )
    identity = payload.transition_identity.model_dump()
    disposition = collab_ingress.execute(
        collab_ingress.ECOSYSTEM_CHAT,
        ecosystem_chat_request(payload),
        surface=SURFACE,
        source_output_id=f"{SURFACE}:{payload.session_id}:{collab_ingress.digest(identity)}",
        data={"message_sha256": collab_ingress.digest(payload.message.encode("utf-8")),
              "caller_transition_identity_sha256": collab_ingress.digest(identity)},
    )
    body = {
        **disposition,
        # Kept for clients of the previous shape. None of these is decided
        # here: there is no locally generated response and no local receipt.
        "response": None,
        "routed_module": collab_ingress.ECOSYSTEM_CHAT,
        "task_status": "manifest_" + disposition["disposition"].lower(),
        "receipt_id": None,
        "final_receipt": False,
        "final_receipt_id": None,
        "transition_id": identity["transition_id"],
        "run_id": identity["run_id"],
        "event_id": identity["event_id"],
        "caller_transition_identity_is_manifest_identity": False,
        "interaction_profile": payload.interaction_profile,
        "authority": {
            "local_response_generated": False,
            "provider_called": False,
            "local_admissibility_decided": False,
            "provider_output_is_authority": False,
            "repository_mutation_allowed": False,
            "publication_allowed": False,
            "site_grants_admissibility": False,
            "master_records_gating": False,
        },
    }
    return JSONResponse(status_code=collab_ingress.http_status(disposition), content=body,
                        headers={"Cache-Control": "no-store"})
