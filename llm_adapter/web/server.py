"""HTTP/1.1 server for the ASGI application, on the standard library.

Replaces ``uvicorn.run`` for the gateway: ``run(app, host=, port=,
ssl_certfile=, ssl_keyfile=)``. One request per connection (``Connection:
close``); ``Content-Length`` and chunked request bodies; optional TLS from a
certificate/key pair. The server writes no access log of its own, so the raw
request target is never logged; the application's query-safe middleware logs
instead. A request that cannot be read in ``READ_TIMEOUT`` seconds is dropped;
an application error that escapes before a response starts answers 500.
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import ssl
from http import HTTPStatus
from typing import Any

READ_TIMEOUT = 30.0
MAX_HEADER_BYTES = 64 * 1024
MAX_BODY_BYTES = 64 * 1024 * 1024

logger = logging.getLogger("stegverse.web.server")


class _BadRequest(Exception):
    pass


def load_app(target: Any) -> Any:
    if not isinstance(target, str):
        return target
    module_name, _, attr = target.partition(":")
    module = importlib.import_module(module_name)
    obj: Any = module
    for part in (attr or "app").split("."):
        obj = getattr(obj, part)
    return obj


async def _read_request(reader: asyncio.StreamReader) -> tuple[str, str, str, list[tuple[bytes, bytes]], bytes]:
    head = await reader.readuntil(b"\r\n\r\n")
    if len(head) > MAX_HEADER_BYTES:
        raise _BadRequest("header_too_large")
    lines = head[:-4].split(b"\r\n")
    try:
        method, target, version = lines[0].decode("latin-1").split(" ", 2)
    except ValueError as exc:
        raise _BadRequest("request_line_invalid") from exc
    headers: list[tuple[bytes, bytes]] = []
    for line in lines[1:]:
        if b":" not in line:
            raise _BadRequest("header_invalid")
        name, value = line.split(b":", 1)
        headers.append((name.strip().lower(), value.strip()))
    lookup = {k: v for k, v in headers}
    body = b""
    if lookup.get(b"transfer-encoding", b"").lower() == b"chunked":
        chunks = []
        total = 0
        while True:
            size_line = await reader.readuntil(b"\r\n")
            size = int(size_line.split(b";", 1)[0].strip() or b"0", 16)
            if size == 0:
                await reader.readuntil(b"\r\n")
                break
            total += size
            if total > MAX_BODY_BYTES:
                raise _BadRequest("body_too_large")
            chunks.append(await reader.readexactly(size))
            await reader.readexactly(2)
        body = b"".join(chunks)
    elif b"content-length" in lookup:
        length = int(lookup[b"content-length"])
        if length < 0 or length > MAX_BODY_BYTES:
            raise _BadRequest("body_too_large")
        body = await reader.readexactly(length)
    return method.upper(), target, version, headers, body


async def _serve_connection(app: Any, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, scheme: str) -> None:
    started = False
    try:
        try:
            method, target, version, headers, body = await asyncio.wait_for(_read_request(reader), READ_TIMEOUT)
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, ConnectionError):
            return
        except (_BadRequest, ValueError):
            writer.write(b"HTTP/1.1 400 Bad Request\r\ncontent-length: 0\r\nconnection: close\r\n\r\n")
            await writer.drain()
            return
        path, _, query = target.partition("?")
        peer = writer.get_extra_info("peername") or ("", 0)
        sock = writer.get_extra_info("sockname") or ("", 0)
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": version.split("/")[-1],
            "method": method, "scheme": scheme, "path": path or "/", "raw_path": (path or "/").encode("latin-1"),
            "root_path": "", "query_string": query.encode("latin-1"), "headers": headers,
            "client": (peer[0], peer[1]), "server": (sock[0], sock[1]), "state": {},
        }
        delivered = False

        async def receive() -> dict[str, Any]:
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}

        status = 500
        response_headers: list[tuple[bytes, bytes]] = []
        chunks: list[bytes] = []

        async def send(message: dict[str, Any]) -> None:
            nonlocal status, response_headers, started
            if message["type"] == "http.response.start":
                started = True
                status = int(message["status"])
                response_headers = list(message.get("headers") or [])
            elif message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))

        try:
            await app(scope, receive, send)
        except Exception:
            logger.exception("application error")
            if not started:
                status, response_headers, chunks = 500, [(b"content-type", b"text/plain; charset=utf-8")], [b"Internal Server Error"]
        payload = b"".join(chunks)
        names = {k.lower() for k, _ in response_headers}
        if b"content-length" not in names and status >= 200 and status not in (204, 304):
            response_headers.append((b"content-length", str(len(payload)).encode()))
        response_headers = [(k, v) for k, v in response_headers if k.lower() != b"connection"]
        response_headers.append((b"connection", b"close"))
        try:
            reason = HTTPStatus(status).phrase
        except ValueError:
            reason = ""
        out = [f"HTTP/1.1 {status} {reason}\r\n".encode("latin-1")]
        out += [k + b": " + v + b"\r\n" for k, v in response_headers]
        out.append(b"\r\n")
        if method != "HEAD":
            out.append(payload)
        writer.write(b"".join(out))
        await writer.drain()
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def serve(app: Any, host: str, port: int, ssl_context: ssl.SSLContext | None = None) -> None:
    app = load_app(app)
    scheme = "https" if ssl_context else "http"

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await _serve_connection(app, reader, writer, scheme)

    server = await asyncio.start_server(handle, host, port, ssl=ssl_context, limit=MAX_HEADER_BYTES)
    async with server:
        await server.serve_forever()


def run(app: Any, host: str = "127.0.0.1", port: int = 8000, *, ssl_certfile: str | None = None,
        ssl_keyfile: str | None = None, **_: Any) -> None:
    """Serve ``app`` (an ASGI callable or ``"module:attr"``) until interrupted.

    Extra keyword arguments that uvicorn accepted (``access_log``, ``proxy_headers``,
    ``server_header``, ``log_level`` ...) are accepted and ignored: this server
    keeps no access log, adds no server header and trusts no proxy headers.
    """
    context = None
    if ssl_certfile:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(certfile=ssl_certfile, keyfile=ssl_keyfile)
    try:
        asyncio.run(serve(app, host, port, context))
    except KeyboardInterrupt:
        pass


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m llm_adapter.web.server")
    parser.add_argument("app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--ssl-certfile")
    parser.add_argument("--ssl-keyfile")
    args, _unknown = parser.parse_known_args(argv)
    run(args.app, host=args.host, port=args.port, ssl_certfile=args.ssl_certfile, ssl_keyfile=args.ssl_keyfile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
