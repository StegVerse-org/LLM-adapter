"""HTTP provider client seams for governed LLM adapter.

These clients are optional live-provider adapters. They fail closed when API keys
are absent and always return provider output through the same ProviderResponse
envelope used by fixture providers. The governed session must still evaluate the
response before any user-visible or downstream effect.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import requests

from .provider_client import ProviderResponse
from .provider_request import ProviderRequest


class ProviderConfigurationError(RuntimeError):
    """Raised when a live provider client is not configured."""


@dataclass(frozen=True)
class OpenAIHTTPProviderClient:
    """Minimal OpenAI-compatible chat completions client.

    This client only performs a provider call when an API key is explicitly
    supplied or available in the environment. It does not bypass governance.
    """

    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com/v1/chat/completions"
    timeout_seconds: int = 60

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is required for OpenAIHTTPProviderClient")

        payload = {
            "model": request.model,
            "messages": [message.to_dict() for message in request.messages],
            "temperature": request.temperature,
        }
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        output = body["choices"][0]["message"]["content"]
        return ProviderResponse(
            provider=request.provider,
            model=request.model,
            output=output,
            request_hash=request.request_hash,
            metadata={
                "provider_mode": "openai_http",
                "response_id": body.get("id", "unresolved"),
                "finish_reason": body.get("choices", [{}])[0].get("finish_reason", "unresolved"),
            },
        )


@dataclass(frozen=True)
class AnthropicHTTPProviderClient:
    """Minimal Anthropic-compatible messages client.

    This client only performs a provider call when an API key is explicitly
    supplied or available in the environment. It does not bypass governance.
    """

    api_key: Optional[str] = None
    base_url: str = "https://api.anthropic.com/v1/messages"
    anthropic_version: str = "2023-06-01"
    max_tokens: int = 1024
    timeout_seconds: int = 60

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is required for AnthropicHTTPProviderClient")

        system_messages = [message.content for message in request.messages if message.role == "system"]
        conversation = [message.to_dict() for message in request.messages if message.role != "system"]
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": conversation,
            "temperature": request.temperature,
            "max_tokens": self.max_tokens,
        }
        if system_messages:
            payload["system"] = "\n".join(system_messages)

        response = requests.post(
            self.base_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": self.anthropic_version,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        output = "".join(block.get("text", "") for block in body.get("content", []) if block.get("type") == "text")
        return ProviderResponse(
            provider=request.provider,
            model=request.model,
            output=output,
            request_hash=request.request_hash,
            metadata={
                "provider_mode": "anthropic_http",
                "response_id": body.get("id", "unresolved"),
                "stop_reason": body.get("stop_reason", "unresolved"),
            },
        )


def build_http_provider_client(
    provider: str,
    *,
    api_key: Optional[str] = None,
) -> OpenAIHTTPProviderClient | AnthropicHTTPProviderClient:
    """Build a live HTTP provider client by provider name."""

    normalized = provider.lower().strip()
    if normalized in {"openai", "chatgpt", "openai_http"}:
        return OpenAIHTTPProviderClient(api_key=api_key)
    if normalized in {"anthropic", "claude", "anthropic_http"}:
        return AnthropicHTTPProviderClient(api_key=api_key)
    raise ValueError(f"unsupported provider for HTTP client: {provider}")


__all__ = [
    "AnthropicHTTPProviderClient",
    "OpenAIHTTPProviderClient",
    "ProviderConfigurationError",
    "build_http_provider_client",
]
