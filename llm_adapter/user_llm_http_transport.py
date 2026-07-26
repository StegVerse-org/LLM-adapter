"""Fail-closed HTTP transport bindings for user-LLM routes."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .user_llm_router import RouteTransports, Transport


class TransportError(RuntimeError):
    """Raised when a configured downstream route cannot return a valid response."""


@dataclass(frozen=True)
class HTTPRouteConfig:
    demo_test_suite_url: str | None = None
    entity_sandbox_runner_url: str | None = None
    hil_response_packet_url: str | None = None
    bearer_token: str | None = None
    timeout_seconds: float = 20.0

    @classmethod
    def from_environment(cls) -> "HTTPRouteConfig":
        timeout_raw = os.getenv("STEGVERSE_USER_LLM_HTTP_TIMEOUT_SECONDS", "20")
        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise TransportError("invalid STEGVERSE_USER_LLM_HTTP_TIMEOUT_SECONDS") from exc
        if timeout <= 0:
            raise TransportError("HTTP timeout must be positive")
        return cls(
            demo_test_suite_url=_clean_url(os.getenv("STEGVERSE_DEMO_TEST_SUITE_URL")),
            entity_sandbox_runner_url=_clean_url(os.getenv("STEGVERSE_ENTITY_SANDBOX_RUNNER_URL")),
            hil_response_packet_url=_clean_url(os.getenv("STEGVERSE_HIL_RESPONSE_PACKET_URL")),
            bearer_token=os.getenv("STEGVERSE_USER_LLM_BEARER_TOKEN") or None,
            timeout_seconds=timeout,
        )


def _clean_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    cleaned = value.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise TransportError("route URL must be an absolute http or https URL")
    return cleaned


def make_http_transport(
    url: str,
    *,
    bearer_token: str | None = None,
    timeout_seconds: float = 20.0,
) -> Transport:
    target = _clean_url(url)
    if target is None:
        raise TransportError("route URL is required")
    if timeout_seconds <= 0:
        raise TransportError("HTTP timeout must be positive")

    def transport(envelope: Mapping[str, Any]) -> Mapping[str, Any]:
        body = json.dumps(dict(envelope), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "stegverse-llm-adapter/user-llm-access-v1",
        }
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        request = Request(target, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read()
                status = getattr(response, "status", 200)
        except HTTPError as exc:
            raise TransportError(f"downstream HTTP error: {exc.code}") from exc
        except URLError as exc:
            raise TransportError("downstream route unavailable") from exc
        except TimeoutError as exc:
            raise TransportError("downstream route timed out") from exc

        if status < 200 or status >= 300:
            raise TransportError(f"downstream returned non-success status: {status}")
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TransportError("downstream response is not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise TransportError("downstream response must be a JSON object")
        return parsed

    return transport


def build_http_route_transports(config: HTTPRouteConfig | None = None) -> RouteTransports:
    active = config or HTTPRouteConfig.from_environment()
    def configured(url: str | None) -> Transport | None:
        return make_http_transport(
            url,
            bearer_token=active.bearer_token,
            timeout_seconds=active.timeout_seconds,
        ) if url else None
    return RouteTransports(
        demo_test_suite=configured(active.demo_test_suite_url),
        entity_sandbox_runner=configured(active.entity_sandbox_runner_url),
        hil_response_packet=configured(active.hil_response_packet_url),
    )


def configured_route_status(config: HTTPRouteConfig | None = None) -> dict[str, bool]:
    active = config or HTTPRouteConfig.from_environment()
    return {
        "demo_test_suite": bool(active.demo_test_suite_url),
        "entity_sandbox_runner": bool(active.entity_sandbox_runner_url),
        "hil_response_packet": bool(active.hil_response_packet_url),
    }