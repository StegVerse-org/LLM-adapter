"""Transport-only shared Service Gateway adapter for HIL Universal InTr.

The public Gateway forwards exact admitted HIL trigger bytes to the same-host
loopback sovereign HIL ingress. It never mints receipts, claims/fences,
credentials, custody, review, publication, or lifecycle authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

router = APIRouter()
MAX_BODY = 512 * 1024
ALLOWED_ORIGINS = {"https://stegverse.org", "https://www.stegverse.org"}
FORBIDDEN_REQUEST_HEADERS = ("authorization", "cookie")
FORWARDED_HEADERS = (
    "origin",
    "content-type",
    "x-stegverse-transport",
    "x-stegverse-transport-origin",
    "x-stegverse-authorization-id",
    "x-stegverse-payload-sha256",
)


def _enabled() -> bool:
    return os.getenv("STEGVERSE_HIL_INTR_ENABLED", "false").strip().lower() == "true"


def _upstream() -> str:
    raw = os.getenv("STEGVERSE_HIL_INTR_UPSTREAM", "").strip()
    if not raw:
        raise ValueError("HIL InTr upstream is not configured")
    parsed = urlsplit(raw)
    if parsed.scheme != "http":
        raise ValueError("HIL InTr upstream must use same-host http")
    if parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("HIL InTr upstream must be loopback-only")
    if parsed.path != "/intr/materialization" or parsed.query or parsed.fragment:
        raise ValueError("HIL InTr upstream path must be /intr/materialization")
    return raw


def _profile_upstream() -> str:
    parsed = urlsplit(_upstream())
    return urlunsplit((parsed.scheme, parsed.netloc, "/intr/profile", "", ""))


def _read_profile() -> dict:
    req = urlrequest.Request(_profile_upstream(), method="GET")
    try:
        with urlrequest.urlopen(req, timeout=15) as response:
            raw = response.read(MAX_BODY + 1)
            if len(raw) > MAX_BODY:
                raise ValueError("Universal InTr profile response too large")
            if response.status != 200:
                raise ValueError(f"Universal InTr profile status invalid:{response.status}")
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"universal_intr_profile_unavailable:{type(exc).__name__}",
        ) from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=502, detail="universal_intr_profile_invalid_json") from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=502, detail="universal_intr_profile_object_required")
    return value


def _validate_profile(profile: dict) -> None:
    schema = profile.get("schema")
    if schema not in {
        "stegverse.universal-intr-profiled-ingress/v1",
        "stegverse.hil-intr-materialization-ingress-profile/v1",
    }:
        raise HTTPException(status_code=502, detail="universal_intr_profile_schema_invalid")
    expected = {
        "state": "ACTIVE_SOVEREIGN_INTR_INGRESS",
        "protocol": "InTr",
        "profile_path": "/intr/profile",
        "materialization_path": "/intr/materialization",
        "event_triggered": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
    }
    for field, required in expected.items():
        if profile.get(field) != required:
            raise HTTPException(status_code=502, detail=f"universal_intr_profile_{field}_mismatch")
    if schema == "stegverse.universal-intr-profiled-ingress/v1":
        if profile.get("always_on_application_receiver_required") is not False:
            raise HTTPException(status_code=502, detail="universal_intr_profile_always_on_receiver_forbidden")
        profiles = profile.get("profiles")
    else:
        if profile.get("always_on_receiver_required") is not False:
            raise HTTPException(status_code=502, detail="universal_intr_profile_always_on_receiver_forbidden")
        profiles = profile.get("additional_materialization_profiles")
    if not isinstance(profiles, list) or not all(isinstance(value, str) and value for value in profiles):
        raise HTTPException(status_code=502, detail="universal_intr_profile_profiles_invalid")


def _public_https(request: Request) -> bool:
    forwarded = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower()
    return request.url.scheme == "https" or forwarded == "https"


def _hash_body(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _validate_request(request: Request, body: bytes) -> dict[str, str]:
    origin = request.headers.get("origin")
    if origin not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="origin_not_admitted")
    if any(request.headers.get(name) for name in FORBIDDEN_REQUEST_HEADERS):
        raise HTTPException(status_code=400, detail="credential_header_rejected")
    if not body or len(body) > MAX_BODY:
        raise HTTPException(status_code=413, detail="request_size_invalid")
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type not in {"application/json", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="content_type_not_supported")
    if request.headers.get("x-stegverse-transport") != "InTr":
        raise HTTPException(status_code=400, detail="transport_header_mismatch")
    transport_origin = request.headers.get("x-stegverse-transport-origin", "")
    if transport_origin not in {"STEGOS_NODE_OUTBOX", "TVC_RELAY_EGRESS"}:
        raise HTTPException(status_code=400, detail="transport_origin_header_invalid")
    authorization_id = request.headers.get("x-stegverse-authorization-id", "").strip()
    if transport_origin == "STEGOS_NODE_OUTBOX" and authorization_id:
        raise HTTPException(status_code=400, detail="node_outbox_cannot_claim_tvc_authorization")
    if transport_origin == "TVC_RELAY_EGRESS" and not authorization_id:
        raise HTTPException(status_code=400, detail="relay_authorization_id_required")
    claimed = request.headers.get("x-stegverse-payload-sha256", "").strip().lower()
    if claimed != _hash_body(body):
        raise HTTPException(status_code=400, detail="request_payload_hash_mismatch")
    return {name: request.headers[name] for name in FORWARDED_HEADERS if name in request.headers}


def _forward(body: bytes, headers: dict[str, str]) -> tuple[int, bytes, str]:
    target = _upstream()
    req = urlrequest.Request(target, data=body, method="POST")
    for name, value in headers.items():
        req.add_header(name, value)
    try:
        with urlrequest.urlopen(req, timeout=15) as response:
            raw = response.read(MAX_BODY + 1)
            if len(raw) > MAX_BODY:
                raise ValueError("HIL ingress response too large")
            return response.status, raw, response.headers.get_content_type()
    except urlerror.HTTPError as exc:
        raw = exc.read(MAX_BODY + 1)
        return exc.code, raw, exc.headers.get_content_type()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"hil_intr_runtime_unavailable:{type(exc).__name__}") from exc


@router.get("/intr/profile")
def universal_intr_profile(request: Request) -> dict:
    if not _enabled():
        raise HTTPException(status_code=503, detail="hil_intr_disabled")
    if not _public_https(request):
        raise HTTPException(status_code=400, detail="public_https_required")
    profile = _read_profile()
    _validate_profile(profile)
    projected = dict(profile)
    projected["tls_enabled"] = True
    projected["public_tls_terminated_by"] = "STEGVERSE_SHARED_SERVICE_GATEWAY"
    projected["profile_projection"] = "SHARED_GATEWAY_PUBLIC_HTTPS"
    projected["source_loopback_tls_enabled"] = profile.get("tls_enabled") is True
    return projected


@router.get("/intr/materialization/readiness")
def hil_intr_readiness() -> dict:
    configured = False
    reason = None
    try:
        _upstream()
        configured = True
    except ValueError as exc:
        reason = str(exc)
    return {
        "schema": "stegverse.service-gateway.hil-intr-readiness/v1",
        "enabled": _enabled(),
        "loopback_upstream_configured": configured,
        "state": "READY" if _enabled() and configured else "NOT_READY",
        "transport": "InTr",
        "supported_origins": ["STEGOS_NODE_OUTBOX", "TVC_RELAY_EGRESS"],
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "g18_completion_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "gateway_receipt_authority": False,
        "gateway_execution_authority": False,
        "gateway_custody_authority": False,
        "authority_effect": "NONE",
        "reason": reason,
    }


@router.post("/intr/materialization")
async def hil_intr_proxy(request: Request) -> Response:
    if not _enabled():
        raise HTTPException(status_code=503, detail="hil_intr_disabled")
    body = await request.body()
    headers = _validate_request(request, body)
    status, raw, content_type = _forward(body, headers)
    return Response(
        content=raw,
        status_code=status,
        media_type=content_type or "application/json",
        headers={"Cache-Control": "no-store"},
    )
