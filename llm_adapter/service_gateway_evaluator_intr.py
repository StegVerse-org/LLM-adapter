"""Transport-only Service Gateway adapter for evaluator Interlock/InTr.

The shared public Gateway forwards exact admitted browser bytes to a same-host
sovereign evaluator runtime. It does not mint receipts or interpret evaluator
state.
"""
from __future__ import annotations

import hashlib
import json
import os
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

router = APIRouter()
MAX_BODY = 2 * 1024 * 1024
ALLOWED_ORIGINS = {"https://stegverse.org", "https://www.stegverse.org"}
FORBIDDEN_REQUEST_HEADERS = ("authorization", "cookie")
FORWARDED_HEADERS = (
    "origin",
    "content-type",
    "x-stegverse-transport",
    "x-stegverse-authorization-id",
    "x-stegverse-payload-sha256",
)


def _enabled() -> bool:
    return os.getenv("STEGVERSE_EVALUATOR_INTR_ENABLED", "false").strip().lower() == "true"


def _upstream() -> str:
    raw = os.getenv("STEGVERSE_EVALUATOR_INTR_UPSTREAM", "").strip()
    if not raw:
        raise ValueError("evaluator InTr upstream is not configured")
    parsed = urlsplit(raw)
    if parsed.scheme != "http":
        raise ValueError("evaluator InTr upstream must use same-host http")
    if parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("evaluator InTr upstream must be loopback-only")
    if parsed.path != "/intr/evaluator" or parsed.query or parsed.fragment:
        raise ValueError("evaluator InTr upstream path must be /intr/evaluator")
    return raw


def _hash_body(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _validate_browser_request(request: Request, body: bytes) -> dict[str, str]:
    if request.headers.get("origin") not in ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="origin_not_admitted")
    if any(request.headers.get(name) for name in FORBIDDEN_REQUEST_HEADERS):
        raise HTTPException(status_code=400, detail="credential_header_rejected")
    if not body or len(body) > MAX_BODY:
        raise HTTPException(status_code=413, detail="request_size_invalid")
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        raise HTTPException(status_code=415, detail="json_required")
    if request.headers.get("x-stegverse-transport") != "InTr":
        raise HTTPException(status_code=400, detail="transport_header_mismatch")
    authority = request.headers.get("x-stegverse-authorization-id", "").strip()
    if not authority:
        raise HTTPException(status_code=400, detail="authorization_id_required")
    claimed = request.headers.get("x-stegverse-payload-sha256", "").strip()
    if claimed != _hash_body(body):
        raise HTTPException(status_code=400, detail="request_payload_hash_mismatch")
    try:
        payload = json.loads(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid_json") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="request_object_required")
    if payload.get("schema_version") != "stegverse.evaluator_review.interlock_request.v1":
        raise HTTPException(status_code=400, detail="request_schema_mismatch")
    if payload.get("request_class") != "EVALUATOR_REVIEW" or payload.get("transport") != "InTr":
        raise HTTPException(status_code=400, detail="request_class_transport_mismatch")
    if payload.get("authority_transfer") is not False:
        raise HTTPException(status_code=400, detail="authority_transfer_rejected")
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
                raise ValueError("evaluator runtime response too large")
            return response.status, raw, response.headers.get_content_type()
    except urlerror.HTTPError as exc:
        raw = exc.read(MAX_BODY + 1)
        return exc.code, raw, exc.headers.get_content_type()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"evaluator_runtime_unavailable:{type(exc).__name__}") from exc


@router.get("/intr/evaluator/readiness")
def evaluator_intr_readiness() -> dict:
    configured = False
    reason = None
    try:
        _upstream()
        configured = True
    except ValueError as exc:
        reason = str(exc)
    return {
        "schema": "stegverse.service-gateway.evaluator-intr-readiness/v1",
        "enabled": _enabled(),
        "loopback_upstream_configured": configured,
        "state": "READY" if _enabled() and configured else "NOT_READY",
        "reason": reason,
        "transport": "InTr",
        "credential_authority": "TV/TVC",
        "gateway_receipt_authority": False,
        "gateway_evaluator_authority": False,
        "authority_effect": "NONE",
    }


@router.post("/intr/evaluator")
async def evaluator_intr_proxy(request: Request) -> Response:
    if not _enabled():
        raise HTTPException(status_code=503, detail="evaluator_intr_disabled")
    body = await request.body()
    headers = _validate_browser_request(request, body)
    status, raw, content_type = _forward(body, headers)
    return Response(
        content=raw,
        status_code=status,
        media_type=content_type or "application/json",
        headers={"Cache-Control": "no-store"},
    )
