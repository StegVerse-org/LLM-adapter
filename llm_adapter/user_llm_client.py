"""Typed client for the bounded StegVerse user-LLM runtime service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

import requests

from .user_llm_access import UserLLMIdentity


class HTTPSession(Protocol):
    def get(self, url: str, **kwargs: Any) -> Any: ...
    def post(self, url: str, **kwargs: Any) -> Any: ...


class UserLLMClientError(RuntimeError):
    """Raised when the bounded runtime cannot return a valid response."""


@dataclass(frozen=True)
class UserLLMClientConfig:
    base_url: str
    bearer_token: str | None = None
    timeout_seconds: float = 15.0

    def __post_init__(self) -> None:
        normalized = self.base_url.rstrip("/")
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("base_url must use http or https")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        object.__setattr__(self, "base_url", normalized)


class UserLLMClient:
    """Stable caller interface for Demo, sandbox, and HIL metadata routes."""

    def __init__(
        self,
        config: UserLLMClientConfig,
        identity: UserLLMIdentity,
        *,
        session: HTTPSession | None = None,
    ) -> None:
        self.config = config
        self.identity = identity
        self._session = session or requests.Session()

    def capabilities(self) -> tuple[dict[str, Any], ...]:
        response = self._request("GET", "/v1/user-llm/capabilities")
        capabilities = response.get("capabilities")
        if not isinstance(capabilities, list):
            raise UserLLMClientError("runtime returned malformed capabilities")
        return tuple(dict(item) for item in capabilities if isinstance(item, Mapping))

    def submit_demo(self, action: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._submit("demo_test_suite", action, payload)

    def submit_entity(self, action: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._submit("entity_sandbox_runner", action, payload)

    def submit_hil(
        self,
        *,
        filename: str,
        sha256_hex: str,
        size_bytes: int,
        trace_id: str,
        participant_review_status: str,
    ) -> dict[str, Any]:
        return self._submit(
            "hil_response_packet",
            "submit_pdf_metadata",
            {
                "filename": filename,
                "sha256": sha256_hex.lower(),
                "size_bytes": size_bytes,
                "trace_id": trace_id,
                "participant_review_status": participant_review_status,
            },
        )

    def _submit(self, route: str, action: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        body = {
            "identity": {
                "user_id": self.identity.user_id,
                "llm_id": self.identity.llm_id,
                "provider": self.identity.provider,
                "model": self.identity.model,
                "scopes": list(self.identity.scopes),
            },
            "route": route,
            "action": action,
            "payload": dict(payload),
        }
        return self._request("POST", "/v1/user-llm/requests", json=body)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = dict(kwargs.pop("headers", {}))
        if self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"
        kwargs["headers"] = headers
        kwargs["timeout"] = self.config.timeout_seconds
        url = f"{self.config.base_url}{path}"

        try:
            if method == "GET":
                response = self._session.get(url, **kwargs)
            else:
                response = self._session.post(url, **kwargs)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise UserLLMClientError(f"runtime request failed: {method} {path}") from exc

        if not isinstance(payload, dict):
            raise UserLLMClientError("runtime returned a non-object response")
        if payload.get("authority_attached") is True:
            raise UserLLMClientError("runtime response violated non-authority invariant")
        return payload
