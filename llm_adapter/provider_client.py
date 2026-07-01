"""Provider client boundary for governed LLM adapter.

This module defines the provider seam without performing network calls. Live
provider implementations should satisfy the same interface and remain wrapped by
the governed session path before their output can be returned or acted on.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol

from .provider_request import ProviderRequest


PROVIDER_RESPONSE_SCHEMA_VERSION = "stegverse.llm_adapter.provider_response.v0.1"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProviderResponse:
    """Provider output envelope before adapter governance."""

    provider: str
    model: str
    output: str
    request_hash: str
    metadata: Mapping[str, Any]
    schema_version: str = PROVIDER_RESPONSE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "provider": self.provider,
            "model": self.model,
            "output": self.output,
            "request_hash": self.request_hash,
            "metadata": dict(self.metadata),
            "response_hash": self.response_hash,
        }

    @property
    def response_hash(self) -> str:
        return stable_hash(
            {
                "schema_version": self.schema_version,
                "provider": self.provider,
                "model": self.model,
                "output": self.output,
                "request_hash": self.request_hash,
                "metadata": dict(self.metadata),
            }
        )


class ProviderClient(Protocol):
    """Provider client protocol.

    Implementations may call live models, but their output still enters the
    governed adapter before being returned to a user or downstream system.
    """

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Return provider output for a normalized request."""


@dataclass(frozen=True)
class FixtureProviderClient:
    """Deterministic provider for local tests and governed fixture sessions."""

    output: str
    metadata: Optional[Mapping[str, Any]] = None

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            provider=request.provider,
            model=request.model,
            output=self.output,
            request_hash=request.request_hash,
            metadata=self.metadata or {"provider_mode": "fixture"},
        )


__all__ = [
    "PROVIDER_RESPONSE_SCHEMA_VERSION",
    "FixtureProviderClient",
    "ProviderClient",
    "ProviderResponse",
]
