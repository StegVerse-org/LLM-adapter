from __future__ import annotations

from typing import Dict
from urllib.parse import parse_qsl

import requests
from fastapi import HTTPException, Request, Response

from llm_adapter.math_solver_gateway import app

UPSTREAM_ORIGIN = "http://127.0.0.1:8786"
UPSTREAM_TIMEOUT_SECONDS = 5
CALLBACK_ALLOWED_QUERY_KEYS = {"state", "code", "error", "error_description"}
FORWARDED_RESPONSE_HEADERS = {
    "content-type",
    "location",
    "cache-control",
    "pragma",
    "expires",
    "retry-after",
}

ROUTES = {
    "/tvc/external-collaboration/google-drive/consent/begin": "FORBIDDEN",
    "/tvc/google-drive/external-collaboration/callback": "CALLBACK_ALLOWLIST",
    "/tvc/external-collaboration/google-drive/consent/health": "FORBIDDEN",
}


def _raw_query(request: Request) -> str:
    raw = request.scope.get("query_string", b"")
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="query_string_not_ascii") from exc


def _validate_query(*, path: str, raw_query: str) -> None:
    policy = ROUTES[path]
    if policy == "FORBIDDEN":
        if raw_query:
            raise HTTPException(status_code=400, detail="query_string_forbidden")
        return

    try:
        items = parse_qsl(raw_query, keep_blank_values=True, strict_parsing=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="query_string_invalid") from exc
    disallowed = sorted({key for key, _ in items if key not in CALLBACK_ALLOWED_QUERY_KEYS})
    if disallowed:
        raise HTTPException(status_code=400, detail="callback_query_key_not_admitted")


def _forward_headers(headers: requests.structures.CaseInsensitiveDict) -> Dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() in FORWARDED_RESPONSE_HEADERS
    }


def _forward_get(*, request: Request, path: str) -> Response:
    raw_query = _raw_query(request)
    _validate_query(path=path, raw_query=raw_query)
    upstream_url = UPSTREAM_ORIGIN + path + (("?" + raw_query) if raw_query else "")

    try:
        upstream = requests.get(
            upstream_url,
            allow_redirects=False,
            timeout=UPSTREAM_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail="external_collaboration_listener_unreachable") from exc

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=_forward_headers(upstream.headers),
        media_type=None,
    )


@app.get("/tvc/external-collaboration/google-drive/consent/begin")
def external_collaboration_consent_begin(request: Request) -> Response:
    return _forward_get(
        request=request,
        path="/tvc/external-collaboration/google-drive/consent/begin",
    )


@app.get("/tvc/google-drive/external-collaboration/callback")
def external_collaboration_consent_callback(request: Request) -> Response:
    return _forward_get(
        request=request,
        path="/tvc/google-drive/external-collaboration/callback",
    )


@app.get("/tvc/external-collaboration/google-drive/consent/health")
def external_collaboration_consent_health(request: Request) -> Response:
    return _forward_get(
        request=request,
        path="/tvc/external-collaboration/google-drive/consent/health",
    )
