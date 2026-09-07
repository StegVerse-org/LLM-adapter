"""HTTP provider clients for governed LLM execution.

Third-party direct-key HTTP clients are retained only as explicit legacy test
shims. Production hosted-provider execution must use the canonical TV/TVC
non-exportable provider-operation path. The StegVerse-local OpenAI-compatible
client remains the sovereign ProviderClient seam and requires no external
credential.

Governance remains outside provider execution in every mode.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Any, Optional, Union
from urllib.parse import urlparse

import requests

from .provider_client import ProviderResponse
from .provider_request import ProviderRequest


class ProviderConfigurationError(RuntimeError):
    """Raised when a provider client is not safely configured."""


def _sovereign_endpoint(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"}:
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return host.endswith(".stegverse") or host.endswith(".stegverse.local")
    return address.is_loopback or address.is_private or address.is_link_local


def _require_legacy_test_mode(enabled: bool, provider: str) -> None:
    if not enabled:
        raise ProviderConfigurationError(
            f"direct {provider} credential execution is legacy test-only; "
            "production hosted-provider execution requires canonical TV/TVC non-exportable operation"
        )


@dataclass(frozen=True)
class StegVerseLocalHTTPProviderClient:
    """OpenAI-compatible provider bound to a StegVerse-owned/federated node.

    The endpoint is local/private by construction. No GitHub token, cloud
    provider key, hosted model API, or public provider endpoint is accepted.
    This class does not install or authorize model weights; it only removes the
    external execution platform from the adapter/provider seam.

    Exact usage/model evidence returned by a sovereign runtime is retained in
    response metadata so the canonical provider-usage and Master Records paths
    can consume measured evidence without re-estimating it.
    """

    base_url: str = "http://127.0.0.1:11434/v1/chat/completions"
    timeout_seconds: int = 120

    def __post_init__(self) -> None:
        if not _sovereign_endpoint(self.base_url):
            raise ProviderConfigurationError(
                "StegVerseLocalHTTPProviderClient requires loopback/private/StegVerse-local endpoint"
            )

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        payload = {
            "model": request.model,
            "messages": [message.to_dict() for message in request.messages],
            "temperature": request.temperature,
        }
        response = requests.post(
            self.base_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        output = body["choices"][0]["message"]["content"]
        usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        stegverse = body.get("stegverse") if isinstance(body.get("stegverse"), dict) else {}
        return ProviderResponse(
            provider=request.provider,
            model=request.model,
            output=output,
            request_hash=request.request_hash,
            metadata={
                "provider_mode": "stegverse_local_openai_compatible",
                "sovereign_endpoint": True,
                "third_party_execution_platform_required": False,
                "provider_credential_required": False,
                "response_id": body.get("id", "unresolved"),
                "finish_reason": body.get("choices", [{}])[0].get("finish_reason", "unresolved"),
                "usage": usage,
                "runtime_model": body.get("model", request.model),
                "model_hash": stegverse.get("model_hash"),
                "training": stegverse.get("training"),
                "third_party_inference_required": stegverse.get("third_party_inference_required", False),
                "authority_effect": stegverse.get("authority_effect", "NONE"),
            },
        )


@dataclass(frozen=True)
class OpenAIHTTPProviderClient:
    """Legacy direct-key OpenAI test shim; never a production credential path."""

    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com/v1/chat/completions"
    timeout_seconds: int = 60
    compatibility_test_mode: bool = False

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        _require_legacy_test_mode(self.compatibility_test_mode, "OpenAI")
        if not self.api_key:
            raise ProviderConfigurationError("explicit test API key is required in legacy OpenAI compatibility mode")
        payload = {
            "model": request.model,
            "messages": [m.to_dict() for m in request.messages],
            "temperature": request.temperature,
        }
        response = requests.post(
            self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
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
                "provider_mode": "openai_http_legacy_test_only",
                "credential_authority": "NONE_PRODUCTION",
                "production_path": "TVC_NON_EXPORTABLE_REQUIRED",
                "response_id": body.get("id", "unresolved"),
                "finish_reason": body.get("choices", [{}])[0].get("finish_reason", "unresolved"),
            },
        )


@dataclass(frozen=True)
class AnthropicHTTPProviderClient:
    """Legacy direct-key Anthropic test shim; canonical production path is TVC."""

    api_key: Optional[str] = None
    base_url: str = "https://api.anthropic.com/v1/messages"
    anthropic_version: str = "2023-06-01"
    max_tokens: int = 1024
    timeout_seconds: int = 60
    compatibility_test_mode: bool = False

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        _require_legacy_test_mode(self.compatibility_test_mode, "Anthropic")
        if not self.api_key:
            raise ProviderConfigurationError("explicit test API key is required in legacy Anthropic compatibility mode")
        system_messages = [m.content for m in request.messages if m.role == "system"]
        conversation = [m.to_dict() for m in request.messages if m.role != "system"]
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
                "x-api-key": self.api_key,
                "anthropic-version": self.anthropic_version,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        output = "".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        )
        return ProviderResponse(
            provider=request.provider,
            model=request.model,
            output=output,
            request_hash=request.request_hash,
            metadata={
                "provider_mode": "anthropic_http_legacy_test_only",
                "credential_authority": "NONE_PRODUCTION",
                "production_path": "TVC_NON_EXPORTABLE_REQUIRED",
                "response_id": body.get("id", "unresolved"),
                "stop_reason": body.get("stop_reason", "unresolved"),
            },
        )


def build_http_provider_client(
    provider: str,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    allow_legacy_direct_credentials: bool = False,
) -> Union[StegVerseLocalHTTPProviderClient, OpenAIHTTPProviderClient, AnthropicHTTPProviderClient]:
    """Build an HTTP edge adapter without creating an alternate credential authority.

    Sovereign/local construction is production-admissible at this seam and uses
    credential requirement NONE. Hosted OpenAI/Anthropic direct-key clients are
    returned only when the caller explicitly requests legacy test compatibility;
    otherwise construction fails closed so production code cannot accidentally
    bypass TV/TVC.
    """

    normalized = provider.lower().strip()
    if normalized in {"stegverse", "stegverse-local", "stegverse_local", "local-sovereign"}:
        return StegVerseLocalHTTPProviderClient(
            base_url=base_url or "http://127.0.0.1:11434/v1/chat/completions"
        )
    if normalized in {"openai", "chatgpt", "openai_http"}:
        _require_legacy_test_mode(allow_legacy_direct_credentials, "OpenAI")
        return OpenAIHTTPProviderClient(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1/chat/completions",
            compatibility_test_mode=True,
        )
    if normalized in {"anthropic", "claude", "anthropic_http"}:
        _require_legacy_test_mode(allow_legacy_direct_credentials, "Anthropic")
        return AnthropicHTTPProviderClient(
            api_key=api_key,
            base_url=base_url or "https://api.anthropic.com/v1/messages",
            compatibility_test_mode=True,
        )
    raise ValueError(f"unsupported provider for HTTP client: {provider}")


__all__ = [
    "AnthropicHTTPProviderClient",
    "OpenAIHTTPProviderClient",
    "StegVerseLocalHTTPProviderClient",
    "ProviderConfigurationError",
    "build_http_provider_client",
]
