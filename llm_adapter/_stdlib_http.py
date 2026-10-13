"""Minimal JSON-over-HTTP client on the standard library.

Replaces the third-party ``requests`` package for the call shapes this
repository uses: ``post``/``get`` with ``json=``, ``headers=`` and ``timeout=``,
a ``Session`` (with ``trust_env`` and ``allow_redirects=False`` for the direct
loopback consent forward), and a ``Response`` with ``status_code``, ``content``,
``text``, case-insensitive ``headers``, ``json()`` and ``raise_for_status()``.
One attempt per call, no retries. Any HTTP status is returned as a response;
``raise_for_status()`` raises ``HTTPError`` for 4xx/5xx; a transport failure
raises ``RequestException``. TLS is verified against the system trust store or,
as ``requests`` did, against the CA bundle named by ``REQUESTS_CA_BUNDLE`` or
``CURL_CA_BUNDLE`` when the session trusts the environment.
"""
from __future__ import annotations

import json as _json
import os
import ssl
from email.message import Message
from typing import Any, Mapping, Optional
from urllib import error as urlerror
from urllib import request as urlrequest

MAX_RESPONSE_BYTES = 64 * 1024 * 1024


class RequestException(OSError):
    """The request did not complete (transport failure or HTTP error status)."""


class HTTPError(RequestException):
    def __init__(self, message: str, response: "Optional[Response]" = None) -> None:
        super().__init__(message)
        self.response = response


class Response:
    def __init__(self, status_code: int, body: bytes, headers: Optional[Message], url: str) -> None:
        self.status_code = status_code
        self.content = body
        self.url = url
        self.headers: Message = headers if headers is not None else Message()

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return _json.loads(self.content.decode("utf-8"))

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPError(f"HTTP {self.status_code} for {self.url}", self)


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


class Session:
    """Per-call opener settings; holds no connections or cookies between calls."""

    def __init__(self) -> None:
        self.trust_env = True

    def _opener(self, allow_redirects: bool) -> urlrequest.OpenerDirector:
        handlers: list = []
        if not self.trust_env:
            handlers.append(urlrequest.ProxyHandler({}))
        else:
            bundle = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("CURL_CA_BUNDLE")
            if bundle:
                handlers.append(urlrequest.HTTPSHandler(context=ssl.create_default_context(cafile=bundle)))
        if not allow_redirects:
            handlers.append(_NoRedirect())
        return urlrequest.build_opener(*handlers)

    def request(self, method: str, url: str, *, json: Any = None, data: Any = None,
                headers: Optional[Mapping[str, str]] = None, timeout: float = 30,
                allow_redirects: bool = True) -> Response:
        if not url.startswith(("http://", "https://")):
            raise RequestException("url must use http:// or https://")
        if isinstance(data, str):
            data = data.encode("utf-8")
        all_headers = dict(headers or {})
        if json is not None:
            data = _json.dumps(json).encode("utf-8")
            if not any(k.lower() == "content-type" for k in all_headers):
                all_headers["Content-Type"] = "application/json"
        req = urlrequest.Request(url, data=data, method=method, headers=all_headers)
        try:
            with self._opener(allow_redirects).open(req, timeout=timeout) as response:
                return Response(response.status, response.read(MAX_RESPONSE_BYTES), response.headers, url)
        except urlerror.HTTPError as exc:
            return Response(exc.code, exc.read(MAX_RESPONSE_BYTES), exc.headers, url)
        except (urlerror.URLError, OSError, ValueError) as exc:
            raise RequestException(str(exc)) from exc

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)

    def close(self) -> None:
        return None


def post(url: str, **kwargs: Any) -> Response:
    return Session().post(url, **kwargs)


def get(url: str, **kwargs: Any) -> Response:
    return Session().get(url, **kwargs)


__all__ = ["RequestException", "HTTPError", "Response", "Session", "post", "get"]
