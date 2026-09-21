"""Transport-only projection of the existing machine-owned HIL receiver through Service Gateway."""
from __future__ import annotations

import os
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlsplit, urlunsplit

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

ENABLED_ENV = "STEGVERSE_HIL_RECEIVER_PROXY_ENABLED"
UPSTREAM_ENV = "STEGVERSE_HIL_RECEIVER_UPSTREAM"
MAX_REQUEST_BYTES = 16 * 1024 * 1024
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
FORBIDDEN_REQUEST_HEADERS = {"authorization", "cookie"}
FORWARDED_REQUEST_HEADERS = {
    "accept",
    "content-type",
    "origin",
    "x-stegverse-hil-review-token",
    "x-stegverse-hil-publication-token",
}
FORWARDED_RESPONSE_HEADERS = {
    "cache-control",
    "content-disposition",
    "x-stegverse-hil-reconstruction-state",
}


def enabled() -> bool:
    return os.getenv(ENABLED_ENV, "false").strip().lower() == "true"


def upstream_base() -> str:
    raw = os.getenv(UPSTREAM_ENV, "").strip().rstrip("/")
    if not raw:
        raise ValueError("HIL receiver upstream is not configured")
    parsed = urlsplit(raw)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("HIL receiver upstream must be loopback http")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("HIL receiver upstream must be an origin without path/query/credentials")
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", "")).rstrip("/")


def target_url(path: str, query: str = "") -> str:
    if not (path == "/api/hil" or path.startswith("/api/hil/")):
        raise ValueError("HIL receiver proxy path outside /api/hil")
    return upstream_base() + path + (("?" + query) if query else "")


def _forward(method: str, target: str, body: bytes, headers: dict[str, str]) -> tuple[int, bytes, str, dict[str, str]]:
    req = urlrequest.Request(target, data=body if method != "GET" else None, method=method)
    for name, value in headers.items():
        req.add_header(name, value)
    try:
        with urlrequest.urlopen(req, timeout=30) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError("HIL receiver response too large")
            return response.status, raw, response.headers.get_content_type(), {
                name.lower(): value for name, value in response.headers.items()
            }
    except urlerror.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        return exc.code, raw, exc.headers.get_content_type(), {
            name.lower(): value for name, value in exc.headers.items()
        }


class HILMachineReceiverProxyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not enabled() or request.method == "OPTIONS" or not (path == "/api/hil" or path.startswith("/api/hil/")):
            return await call_next(request)
        if request.method not in {"GET", "POST"}:
            return Response(status_code=405, headers={"Cache-Control": "no-store"})
        if any(request.headers.get(name) for name in FORBIDDEN_REQUEST_HEADERS):
            return Response(content=b'{"detail":"credential_header_rejected"}', status_code=400, media_type="application/json", headers={"Cache-Control":"no-store"})
        body = await request.body()
        if len(body) > MAX_REQUEST_BYTES:
            return Response(content=b'{"detail":"request_size_invalid"}', status_code=413, media_type="application/json", headers={"Cache-Control":"no-store"})
        headers = {
            name: request.headers[name]
            for name in FORWARDED_REQUEST_HEADERS
            if name in request.headers
        }
        try:
            status, raw, content_type, upstream_headers = _forward(
                request.method,
                target_url(path, request.url.query),
                body,
                headers,
            )
        except Exception as exc:
            return Response(
                content=(
                    '{"detail":"hil_machine_receiver_unavailable","error_class":"'
                    + type(exc).__name__ + '"}'
                ).encode("utf-8"),
                status_code=503,
                media_type="application/json",
                headers={"Cache-Control":"no-store"},
            )
        response_headers = {
            name: upstream_headers[name]
            for name in FORWARDED_RESPONSE_HEADERS
            if name in upstream_headers
        }
        response_headers["Cache-Control"] = "no-store"
        return Response(
            content=raw,
            status_code=status,
            media_type=content_type or "application/octet-stream",
            headers=response_headers,
        )
