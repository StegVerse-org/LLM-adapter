"""In-process client for the ASGI application, on the standard library.

Replaces ``fastapi.testclient.TestClient`` for the calls the test suite makes:
``get``/``post``/``put``/``patch``/``delete``/``options``/``head``/``request``
with ``params``, ``json``, ``data``, ``files``, ``content``, ``headers`` and
``cookies``; redirects followed by default; cookies kept between calls; a server
exception re-raised (``raise_server_exceptions=True``) as Starlette does.
"""
from __future__ import annotations

import asyncio
import http.cookies
import io
import json as _json
import mimetypes
import secrets
from typing import Any, Mapping
from urllib.parse import urlencode, urljoin, urlsplit

from .app import Headers


class HTTPStatusError(Exception):
    def __init__(self, message: str, response: "Response") -> None:
        super().__init__(message)
        self.response = response


class Response:
    def __init__(self, status_code: int, headers: list[tuple[bytes, bytes]], content: bytes, url: str,
                 request: dict[str, Any]) -> None:
        self.status_code = status_code
        self.headers = Headers(headers)
        self.content = content
        self.url = url
        self.request = request

    @property
    def text(self) -> str:
        content_type = self.headers.get("content-type", "")
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=", 1)[1].split(";")[0].strip() or "utf-8"
        return self.content.decode(charset, errors="replace")

    def json(self) -> Any:
        return _json.loads(self.content)

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def is_redirect(self) -> bool:
        return self.status_code in (301, 302, 303, 307, 308) and "location" in self.headers

    @property
    def cookies(self) -> dict[str, str]:
        jar = http.cookies.SimpleCookie()
        for header in self.headers.getlist("set-cookie"):
            jar.load(header)
        return {k: m.value for k, m in jar.items()}

    def raise_for_status(self) -> "Response":
        if self.status_code >= 400:
            raise HTTPStatusError(f"HTTP {self.status_code} for {self.url}", self)
        return self

    def __repr__(self) -> str:
        return f"<Response [{self.status_code}]>"


class Cookies(dict):
    def set(self, name: str, value: str, domain: str = "", path: str = "/") -> None:  # type: ignore[override]
        self[name] = value


def encode_multipart(data: Mapping[str, Any] | None, files: Any) -> tuple[bytes, str]:
    boundary = secrets.token_hex(16)
    parts: list[bytes] = []
    for key, value in (data or {}).items():
        values = value if isinstance(value, (list, tuple)) else [value]
        for item in values:
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
                         + (item if isinstance(item, bytes) else str(item).encode()) + b"\r\n")
    items = files.items() if isinstance(files, Mapping) else files
    for key, spec in items:
        if isinstance(spec, tuple):
            filename = spec[0]
            payload = spec[1]
            content_type = spec[2] if len(spec) > 2 and spec[2] else None
        else:
            payload = spec
            filename = getattr(spec, "name", key)
            content_type = None
        if hasattr(payload, "read"):
            payload = payload.read()
        if isinstance(payload, str):
            payload = payload.encode()
        content_type = content_type or mimetypes.guess_type(str(filename or ""))[0] or "application/octet-stream"
        header = f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"'
        if filename is not None:
            header += f'; filename="{filename}"'
        header += f"\r\nContent-Type: {content_type}\r\n\r\n"
        parts.append(header.encode() + payload + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


class TestClient:
    __test__ = False

    def __init__(self, app: Any, base_url: str = "http://testserver", raise_server_exceptions: bool = True,
                 root_path: str = "", follow_redirects: bool = True, cookies: Mapping[str, str] | None = None,
                 headers: Mapping[str, str] | None = None) -> None:
        self.app = app
        self.base_url = base_url.rstrip("/")
        self.raise_server_exceptions = raise_server_exceptions
        self.root_path = root_path
        self.follow_redirects = follow_redirects
        self.cookies = Cookies(cookies or {})
        self.headers = dict(headers or {})

    def __enter__(self) -> "TestClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def request(self, method: str, url: str, *, params: Mapping[str, Any] | None = None, json: Any = None,
                data: Any = None, files: Any = None, content: bytes | str | None = None,
                headers: Mapping[str, str] | None = None, cookies: Mapping[str, str] | None = None,
                follow_redirects: bool | None = None, **_: Any) -> Response:
        method = method.upper()
        target = url if url.startswith(("http://", "https://")) else urljoin(self.base_url + "/", url.lstrip("/"))
        if params:
            target += ("&" if "?" in target else "?") + urlencode(params, doseq=True)
        body = b""
        request_headers = {"user-agent": "testclient", "accept": "*/*", "accept-encoding": "gzip, deflate",
                           "connection": "keep-alive"}
        request_headers.update({k.lower(): v for k, v in self.headers.items()})
        if files is not None:
            body, content_type = encode_multipart(data if isinstance(data, Mapping) else None, files)
            request_headers["content-type"] = content_type
        elif json is not None:
            body = _json.dumps(json).encode("utf-8")
            request_headers["content-type"] = "application/json"
        elif isinstance(data, Mapping):
            body = urlencode(data, doseq=True).encode()
            request_headers["content-type"] = "application/x-www-form-urlencoded"
        elif data is not None:
            body = data.encode() if isinstance(data, str) else bytes(data)
        elif content is not None:
            body = content.encode() if isinstance(content, str) else bytes(content)
        if body or method in ("POST", "PUT", "PATCH"):
            request_headers["content-length"] = str(len(body))
        for key, value in (headers or {}).items():
            request_headers[key.lower()] = value
        jar = dict(self.cookies)
        jar.update(cookies or {})
        if jar and "cookie" not in request_headers:
            request_headers["cookie"] = "; ".join(f"{k}={v}" for k, v in jar.items())
        response = self._send(method, target, request_headers, body)
        follow = self.follow_redirects if follow_redirects is None else follow_redirects
        hops = 0
        while follow and response.is_redirect and hops < 20:
            hops += 1
            location = urljoin(target, response.headers["location"])
            if response.status_code in (301, 302, 303) and method != "HEAD":
                method, body = "GET", b""
                request_headers.pop("content-type", None)
                request_headers.pop("content-length", None)
            target = location
            response = self._send(method, target, request_headers, body)
        return response

    def _send(self, method: str, url: str, headers: dict[str, str], body: bytes) -> Response:
        parts = urlsplit(url)
        scheme = parts.scheme or "http"
        host = parts.hostname or "testserver"
        port = parts.port or (443 if scheme == "https" else 80)
        host_header = headers.get("host") or parts.netloc or host
        raw_headers = [(b"host", host_header.encode("latin-1"))]
        raw_headers += [(k.encode("latin-1"), str(v).encode("latin-1")) for k, v in headers.items() if k != "host"]
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": scheme,
            "path": parts.path or "/",
            "raw_path": (parts.path or "/").encode(),
            "root_path": self.root_path,
            "query_string": parts.query.encode("latin-1"),
            "headers": raw_headers,
            "client": ("testclient", 50000),
            "server": (host, port),
            "state": {},
        }
        status = 500
        response_headers: list[tuple[bytes, bytes]] = []
        chunks: list[bytes] = []
        delivered = False

        async def receive() -> dict[str, Any]:
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message: dict[str, Any]) -> None:
            nonlocal status, response_headers
            if message["type"] == "http.response.start":
                status = int(message["status"])
                response_headers = list(message.get("headers") or [])
            elif message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))

        try:
            asyncio.run(self.app(scope, receive, send))
        except Exception:
            if self.raise_server_exceptions:
                raise
            status, response_headers, chunks = 500, [(b"content-type", b"text/plain; charset=utf-8")], [b"Internal Server Error"]
        response = Response(status, response_headers, b"".join(chunks), url,
                            {"method": method, "url": url, "headers": headers})
        for name, value in response.cookies.items():
            self.cookies[name] = value
        return response

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self.request("DELETE", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> Response:
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> Response:
        return self.request("HEAD", url, **kwargs)


__all__ = ["HTTPStatusError", "Response", "TestClient", "encode_multipart"]
