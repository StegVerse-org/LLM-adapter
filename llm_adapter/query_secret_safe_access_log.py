from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, MutableMapping

ASGIApp = Callable[[MutableMapping[str, Any], Callable[..., Awaitable[Any]], Callable[..., Awaitable[Any]]], Awaitable[Any]]


class QuerySecretSafeAccessLogMiddleware:
    """Log only HTTP method, canonical path, and status.

    The ASGI ``query_string``, raw request target, headers, cookies, and body are
    intentionally never read or serialized by this middleware.
    """

    def __init__(self, app: ASGIApp, *, logger: logging.Logger | None = None) -> None:
        self.app = app
        self.logger = logger or logging.getLogger("stegverse.service_gateway.access")

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method") or "UNKNOWN")
        path = str(scope.get("path") or "/")
        status = 500

        async def safe_send(message) -> None:
            nonlocal status
            if message.get("type") == "http.response.start":
                status = int(message.get("status") or 500)
            await send(message)

        try:
            await self.app(scope, receive, safe_send)
        finally:
            self.logger.info("method=%s path=%s status=%s", method, path, status)
