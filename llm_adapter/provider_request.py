"""Provider-facing request normalization for governed LLM adapter.

This module keeps provider calls outside the governance core. It turns provider
and model metadata plus prompt content into a deterministic request envelope that
can be governed before any external call is made.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence


REQUEST_SCHEMA_VERSION = "stegverse.llm_adapter.provider_request.v0.1"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ProviderMessage:
    """Normalized chat-style message prepared for a model provider."""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderRequest:
    """Transport-neutral model request envelope.

    The request envelope is hashable and can be attached to a query packet
    without exposing provider credentials or executing a provider call.
    """

    provider: str
    model: str
    messages: tuple[ProviderMessage, ...]
    purpose: str = "answer"
    allowed_sources: tuple[str, ...] = ("model_knowledge",)
    temperature: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    schema_version: str = REQUEST_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "provider": self.provider,
            "model": self.model,
            "messages": [message.to_dict() for message in self.messages],
            "purpose": self.purpose,
            "allowed_sources": list(self.allowed_sources),
            "temperature": self.temperature,
            "metadata": dict(self.metadata),
        }

    @property
    def request_hash(self) -> str:
        return stable_hash(self.to_dict())

    @property
    def user_query(self) -> str:
        for message in reversed(self.messages):
            if message.role == "user":
                return message.content
        return "\n".join(message.content for message in self.messages)


def normalize_messages(messages: Sequence[Mapping[str, str] | ProviderMessage]) -> tuple[ProviderMessage, ...]:
    normalized = []
    for message in messages:
        if isinstance(message, ProviderMessage):
            normalized.append(message)
            continue
        role = str(message.get("role", "user")).strip() or "user"
        content = str(message.get("content", ""))
        normalized.append(ProviderMessage(role=role, content=content))
    return tuple(normalized)


def build_provider_request(
    *,
    provider: str,
    model: str,
    messages: Sequence[Mapping[str, str] | ProviderMessage],
    purpose: str = "answer",
    allowed_sources: Sequence[str] = ("model_knowledge",),
    temperature: float = 0.0,
    metadata: Optional[Mapping[str, Any]] = None,
) -> ProviderRequest:
    """Create a normalized provider request envelope."""

    return ProviderRequest(
        provider=provider,
        model=model,
        messages=normalize_messages(messages),
        purpose=purpose,
        allowed_sources=tuple(allowed_sources),
        temperature=temperature,
        metadata=metadata or {},
    )


__all__ = [
    "REQUEST_SCHEMA_VERSION",
    "ProviderMessage",
    "ProviderRequest",
    "build_provider_request",
    "normalize_messages",
    "stable_hash",
    "stable_json",
]
