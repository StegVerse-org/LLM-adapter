from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .va_claims_runtime_core import ChatRequest, execute_chat, readiness_record

ALLOWED_ORIGINS = {
    "https://stegverse.org",
    "https://www.stegverse.org",
    "https://stegverse-labs.github.io",
}


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "StegVerseVARuntime/1"

    def _cors(self) -> None:
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,X-SteGVerse-Session")

    def _reply(self, status: int, value: Any) -> None:
        body = _json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            try:
                ready = readiness_record()
                self._reply(200, {"state": "READY", "healthy": True, "va_runtime": ready})
            except Exception as exc:
                self._reply(503, {"state": "FAIL_CLOSED", "healthy": False, "detail": str(exc)})
            return
        if self.path == "/api/va-claims/v1/readiness":
            try:
                self._reply(200, readiness_record())
            except Exception as exc:
                self._reply(503, {"state": "FAIL_CLOSED", "detail": str(exc)})
            return
        self._reply(404, {"detail": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/va-claims/v1/chat":
            self._reply(404, {"detail": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._reply(400, {"detail": "invalid_content_length"})
            return
        if length <= 0 or length > 65536:
            self._reply(413 if length > 65536 else 400, {"detail": "invalid_request_size"})
            return
        try:
            raw = self.rfile.read(length)
            value = json.loads(raw.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError("request_must_be_object")
            request = ChatRequest.model_validate(value)
            result = execute_chat(request)
            self._reply(200, result)
        except Exception as exc:
            self._reply(503, {"state": "FAIL_CLOSED", "detail": str(exc), "authority_effect": False, "activation_effect": False})

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer((host, port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
