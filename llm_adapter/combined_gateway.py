"""Combined governed gateway application for Ecosystem Chat and External Chat."""
from __future__ import annotations

import json
import os
from types import SimpleNamespace

from fastapi import Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from llm_adapter.ecosystem_chat_gateway import app
from llm_adapter.external_chat_api import router as external_chat_router
from llm_adapter.external_review_api import router as external_review_router
from llm_adapter.external_publication_mutation import router as external_mutation_router
from llm_adapter.master_records_usage_submission import (
    MasterRecordsUsageError,
    submit_provider_usage_to_master_records,
)
from llm_adapter.provider_usage_submission import persist_provider_usage
from llm_adapter.usage_session_api import router as usage_session_router

app.include_router(external_chat_router)
app.include_router(external_review_router)
app.include_router(external_mutation_router)
app.include_router(usage_session_router)


@app.middleware("http")
async def record_provider_usage_after_ecosystem_chat(request: Request, call_next):
    """Persist successful provider usage and attempt authenticated custody transfer.

    Local persistence remains non-custodial. Master-Records custody is reported only
    when an identity-bound external receipt validates. Transport or custody failure is
    visible in the response but never converts provider output into authority.
    """
    if request.method != "POST" or request.url.path != "/api/ecosystem-chat":
        return await call_next(request)

    request_body = await request.body()

    async def receive() -> dict:
        return {"type": "http.request", "body": request_body, "more_body": False}

    forwarded = Request(request.scope, receive)
    response = await call_next(forwarded)
    chunks = [chunk async for chunk in response.body_iterator]
    raw_body = b"".join(chunks)

    if response.status_code < 400:
        try:
            request_payload = json.loads(request_body.decode("utf-8"))
            response_payload = json.loads(raw_body.decode("utf-8"))
            provider = response_payload.get("provider") or {}
            local_submission = persist_provider_usage(
                session_id=str(request_payload["session_id"]),
                transition_id=str(response_payload["transition_id"]),
                run_id=str(response_payload["run_id"]),
                parent_transition_id=(request_payload.get("transition_identity") or {}).get("parent_transition_id"),
                provider_result=SimpleNamespace(**provider),
            )
            custody_submission = None
            if local_submission is not None:
                canonical_event = local_submission.pop("canonical_event")
                try:
                    custody_submission = submit_provider_usage_to_master_records(canonical_event)
                except MasterRecordsUsageError as exc:
                    custody_submission = {
                        "schema": "stegverse.usage.master_records_submission.v1",
                        "status": "CUSTODY_SUBMISSION_FAILED",
                        "reason": str(exc),
                        "authority_granted": False,
                        "custody_recorded": False,
                    }

            response_payload["provider_usage_submission"] = local_submission
            response_payload["master_records_usage_submission"] = custody_submission
            authority = response_payload.setdefault("authority", {})
            authority["provider_usage_is_master_records_custody"] = bool(
                custody_submission and custody_submission.get("custody_recorded") is True
            )
            authority["provider_usage_grants_authority"] = False
            raw_body = json.dumps(response_payload, separators=(",", ":")).encode("utf-8")
        except Exception as exc:  # fail visible without invalidating the bounded response
            try:
                response_payload = json.loads(raw_body.decode("utf-8"))
                response_payload["provider_usage_submission"] = {
                    "status": "LOCAL_USAGE_PERSISTENCE_FAILED",
                    "reason": type(exc).__name__,
                    "authority_granted": False,
                    "custody_recorded": False,
                }
                response_payload["master_records_usage_submission"] = {
                    "status": "NOT_ATTEMPTED",
                    "authority_granted": False,
                    "custody_recorded": False,
                }
                raw_body = json.dumps(response_payload, separators=(",", ":")).encode("utf-8")
            except Exception:
                pass

    headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in {"content-length", "content-type"}
    }
    return Response(
        content=raw_body,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type or "application/json",
        background=response.background,
    )


# Outer CORS boundary for authenticated cooperative-review submissions. Provider,
# custody, reviewer, publisher, mutator, submitter, and usage-submission credentials
# are never exposed to the browser. Same-origin usage retrieval relies on a matching
# session cookie or X-SteGVerse-Session identity rather than a Site-configured token.
allowed_origins = [
    value.strip()
    for value in os.getenv(
        "STEGVERSE_ALLOWED_ORIGINS",
        "https://stegverse-labs.github.io,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-SteGVerse-Session"],
)
