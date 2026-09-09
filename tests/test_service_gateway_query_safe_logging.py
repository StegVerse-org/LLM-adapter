from __future__ import annotations

import asyncio
import io
import logging
from pathlib import Path

from llm_adapter.query_safe_access_log import QuerySecretSafeAccessLogMiddleware


async def _exercise(query: bytes) -> str:
    stream = io.StringIO()
    logger = logging.getLogger("test.service-gateway.safe-access")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = QuerySecretSafeAccessLogMiddleware(app, logger=logger)
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/tvc/google-drive/callback",
        "raw_path": b"/tvc/google-drive/callback",
        "query_string": query,
        "headers": [(b"authorization", b"Bearer must-never-log")],
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        return None

    await middleware(scope, receive, send)
    handler.flush()
    return stream.getvalue()


def test_oauth_callback_query_never_enters_access_log():
    protected = b"code=oauth-auth-code-123&state=owner-state-456&other=private-value"
    value = asyncio.run(_exercise(protected))
    assert value.strip() == "method=GET path=/tvc/google-drive/callback status=204"
    for prohibited in (
        "oauth-auth-code-123",
        "owner-state-456",
        "private-value",
        "code=",
        "state=",
        "Bearer",
        "must-never-log",
        "?",
    ):
        assert prohibited not in value


def test_arbitrary_query_bytes_do_not_change_logged_request_identity():
    one = asyncio.run(_exercise(b"a=1"))
    two = asyncio.run(_exercise(b"authorization_code=extremely-sensitive&x=2"))
    assert one == two


def test_runtime_entrypoint_disables_uvicorn_request_target_access_log():
    source = (Path(__file__).resolve().parents[1] / "llm_adapter" / "runtime_gateway.py").read_text(encoding="utf-8")
    assert "access_log=False" in source
    assert "QuerySecretSafeAccessLogMiddleware(_base_app)" in source


def test_render_deployed_entrypoint_suppresses_uvicorn_access_logger_and_wraps_app():
    source = (Path(__file__).resolve().parents[1] / "llm_adapter" / "deployed_gateway.py").read_text(encoding="utf-8")
    assert 'logging.getLogger("uvicorn.access").disabled = True' in source
    assert "app = QuerySecretSafeAccessLogMiddleware(app)" in source
    assert source.index('logging.getLogger("uvicorn.access").disabled = True') < source.index("app = QuerySecretSafeAccessLogMiddleware(app)")


def test_safe_middleware_never_reads_query_or_sensitive_request_surfaces():
    source = (Path(__file__).resolve().parents[1] / "llm_adapter" / "query_safe_access_log.py").read_text(encoding="utf-8")
    for prohibited in (
        'scope.get("query_string")',
        "scope['query_string']",
        'scope.get("raw_path")',
        "scope['raw_path']",
        'scope.get("headers")',
        "scope['headers']",
    ):
        assert prohibited not in source
