"""Combined governed gateway application for Ecosystem Chat and External Chat."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
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
from llm_adapter.hil_intake_v1_1_api import router as hil_intake_router
from llm_adapter.hil_publication_api import router as hil_publication_router
from llm_adapter.hil_sovereign_receiver_profile import (
    SovereignHILProfileError,
    apply_sovereign_hil_receiver_profile,
)
from llm_adapter.org_federation_rendezvous_api import router as org_federation_rendezvous_router
from llm_adapter.master_records_usage_submission import (
    MasterRecordsUsageError,
    submit_provider_usage_to_master_records,
)
from llm_adapter.provider_usage_submission import persist_provider_usage
from llm_adapter.resident_rendezvous_api import router as resident_rendezvous_router
from llm_adapter.usage_session_api import router as usage_session_router


try:
    HIL_SOVEREIGN_RECEIVER_PROFILE = apply_sovereign_hil_receiver_profile()
except SovereignHILProfileError as exc:
    HIL_SOVEREIGN_RECEIVER_PROFILE = {
        "schema": "stegverse.hil.sovereign-receiver-profile.v1",
        "state": "FAIL_CLOSED_CONFIGURATION_REQUIRED",
        "reason": str(exc),
        "participant_machine_required": False,
        "developer_machine_required": False,
        "github_hosted_runtime_required": False,
        "third_party_runtime_required": False,
        "authority_granted": False,
    }

app.include_router(external_chat_router)
app.include_router(external_review_router)
app.include_router(external_mutation_router)
app.include_router(usage_session_router)
app.include_router(hil_intake_router)
app.include_router(hil_publication_router)
app.include_router(resident_rendezvous_router)
app.include_router(org_federation_rendezvous_router)


def _canonical_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@app.get("/api/hil/sovereign-receiver-profile")
def hil_sovereign_receiver_profile() -> dict:
    """Expose the non-secret runtime binding used by public HIL discovery."""
    return dict(HIL_SOVEREIGN_RECEIVER_PROFILE)


@app.get("/api/stegverse-node")
def stegverse_node_advertisement(request: Request) -> dict:
    """Return a health-bound, non-authorizing advertisement for this StegVerse node."""
    base_url = str(request.base_url).rstrip("/")
    payload = {
        "schema": "stegverse.node.endpoint-advertisement.v1",
        "node_id": os.getenv("STEGVERSE_NODE_ID", "ecosystem-chat-portable-node"),
        "capability_id": "ecosystem-chat-gateway",
        "endpoint": f"{base_url}/api/ecosystem-chat",
        "health_endpoint": f"{base_url}/health",
        "coinbase_skap_readiness_endpoint": f"{base_url}/api/coinbase/skap/readiness",
        "coinbase_skap_ingress_endpoint": f"{base_url}/api/coinbase/skap/ingress",
        "coinbase_skap_completed_boundary": "DEVICE_TO_KV",
        "coinbase_skap_next_required_transition": "KV_SKAP_VAULT_INTERLOCK_ADMISSION",
        "coinbase_skap_credential_authority": "TV/TVC",
        "coinbase_skap_gateway_execution_authority": "NONE",
        "math_solver_readiness_endpoint": f"{base_url}/api/math-solver/v1/readiness",
        "math_solver_solve_endpoint": f"{base_url}/api/math-solver/v1/solve",
        "attachment_readiness_endpoint": f"{base_url}/api/attachments/v1/readiness",
        "attachment_intake_endpoint": f"{base_url}/api/attachments/v1/intake",
        "math_solver_image_review_endpoint": f"{base_url}/api/math-solver/v1/image-review",
        "hil_intake_readiness_endpoint": f"{base_url}/api/hil/readiness",
        "hil_intake_submission_endpoint": f"{base_url}/api/hil/submissions",
        "hil_submission_status_endpoint_template": f"{base_url}/api/hil/submissions/{{submission_id}}/status",
        "hil_exact_bytes_endpoint_template": f"{base_url}/api/hil/submissions/{{submission_id}}/exact-bytes",
        "hil_exact_bytes_auth": "EXISTING_TV_TVC_REVIEW_AUTH_REQUIRED",
        "hil_sovereign_receiver_profile_endpoint": f"{base_url}/api/hil/sovereign-receiver-profile",
        "hil_publication_readiness_endpoint": f"{base_url}/api/hil/publication-readiness",
        "evaluator_intr_readiness_endpoint": f"{base_url}/intr/evaluator/readiness",
        "evaluator_intr_endpoint": f"{base_url}/intr/evaluator",
        "evaluator_intr_transport": "InTr",
        "evaluator_intr_gateway_authority": "NONE",
        "resident_rendezvous_request_endpoint": f"{base_url}/api/resident-rendezvous/v1/requests",
        "resident_rendezvous_ack_endpoint": f"{base_url}/api/resident-rendezvous/v1/acknowledgements",
        "resident_rendezvous_enabled": os.getenv("STEGVERSE_RESIDENT_RENDEZVOUS_ENABLED", "false").lower() == "true",
        "resident_rendezvous_gateway_execution_authority": "NONE",
        "advertised_at": datetime.now(timezone.utc).isoformat(),
        "health_bound": True,
        "provider_enabled": os.getenv("STEGVERSE_PROVIDER_ENABLED", "false").lower() == "true",
        "hil_intake_enabled": os.getenv("STEGVERSE_HIL_INTAKE_ENABLED", "false").lower() == "true",
        "hil_sovereign_receiver_state": HIL_SOVEREIGN_RECEIVER_PROFILE.get("state"),
        "participant_machine_required": False,
        "developer_machine_required": False,
        "github_hosted_runtime_required": False,
        "third_party_runtime_required": False,
        "durable_storage": os.getenv(
            "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "false"
        ).lower() == "true",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_granted": False,
        "publication_authority": False,
        "execution_authority": False,
    }
    payload["advertisement_sha256"] = _canonical_hash(payload)
    return payload


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
        except Exception as exc:
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


allowed_origins = [
    value.strip()
    for value in os.getenv(
        "STEGVERSE_ALLOWED_ORIGINS",
        "https://stegverse.org,https://www.stegverse.org,https://stegverse-labs.github.io,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-SteGVerse-Session",
        "X-SteGVerse-HIL-Review-Token",
        "X-SteGVerse-HIL-Publication-Token",
        "X-StegVerse-Transport",
        "X-StegVerse-Authorization-Id",
        "X-StegVerse-Payload-SHA256",
        "X-StegVerse-Node-Ref",
    ],
)
