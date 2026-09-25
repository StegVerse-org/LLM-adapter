"""HTTP provider clients for governed LLM execution.

Third-party provider clients remain optional interoperability adapters. The
StegVerse-local client is the sovereign production seam: it can only target a
loopback/private node endpoint and requires no external provider credential.
Governance remains outside provider execution in every mode.
"""

from __future__ import annotations

import ipaddress
import os
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
    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com/v1/chat/completions"
    timeout_seconds: int = 60

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is required for OpenAIHTTPProviderClient")
        payload = {"model": request.model, "messages": [m.to_dict() for m in request.messages], "temperature": request.temperature}
        response = requests.post(self.base_url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=self.timeout_seconds)
        response.raise_for_status(); body = response.json(); output = body["choices"][0]["message"]["content"]
        return ProviderResponse(provider=request.provider, model=request.model, output=output, request_hash=request.request_hash, metadata={"provider_mode":"openai_http","response_id":body.get("id","unresolved"),"finish_reason":body.get("choices",[{}])[0].get("finish_reason","unresolved")})


@dataclass(frozen=True)
class AnthropicHTTPProviderClient:
    api_key: Optional[str] = None
    base_url: str = "https://api.anthropic.com/v1/messages"
    anthropic_version: str = "2023-06-01"
    max_tokens: int = 1024
    timeout_seconds: int = 60

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is required for AnthropicHTTPProviderClient")
        system_messages=[m.content for m in request.messages if m.role=="system"]; conversation=[m.to_dict() for m in request.messages if m.role!="system"]
        payload:dict[str,Any]={"model":request.model,"messages":conversation,"temperature":request.temperature,"max_tokens":self.max_tokens}
        if system_messages: payload["system"]="\n".join(system_messages)
        response=requests.post(self.base_url,headers={"x-api-key":api_key,"anthropic-version":self.anthropic_version,"Content-Type":"application/json"},json=payload,timeout=self.timeout_seconds)
        response.raise_for_status(); body=response.json(); output="".join(b.get("text","") for b in body.get("content",[]) if b.get("type")=="text")
        return ProviderResponse(provider=request.provider,model=request.model,output=output,request_hash=request.request_hash,metadata={"provider_mode":"anthropic_http","response_id":body.get("id","unresolved"),"stop_reason":body.get("stop_reason","unresolved")})



@dataclass(frozen=True)
class XAIHTTPProviderClient:
    """Optional, manifest-selected xAI/Grok transport; no admission or credential authority.

    The caller supplies a scoped credential at the existing TV/TVC+SKAP execution
    edge. No environment fallback, browser credentials or stored API keys.
    """

    api_key: Optional[str] = None
    base_url: str = "https://api.x.ai/v1/chat/completions"
    timeout_seconds: int = 60

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or parsed.hostname not in {"api.x.ai", "mtls.api.x.ai"} or parsed.path != "/v1/chat/completions" or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.port:
            raise ProviderConfigurationError("XAI_ENDPOINT_NOT_ALLOWED: xAI chat completions HTTPS endpoint required")

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        if request.provider.lower().strip() not in {"xai", "grok"}:
            raise ProviderConfigurationError("XAI_PROVIDER_MISMATCH: manifest must select xai or grok")
        if not self.api_key:
            raise ProviderConfigurationError("XAI_CREDENTIAL_UNAVAILABLE: execution-scoped TV/TVC credential required")
        payload = {
            "model": request.model,
            "messages": [message.to_dict() for message in request.messages],
            "stream": False,
        }
        response = requests.post(
            self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        try:
            choice = body["choices"][0]
            output = choice["message"]["content"]
            actual_model = body["model"]
            usage = body["usage"]
            if not isinstance(output, str) or not isinstance(actual_model, str) or not actual_model:
                raise ValueError("output/model missing")
            if not isinstance(usage, dict) or not all(isinstance(usage.get(k), int) and not isinstance(usage[k], bool) and usage[k] >= 0 for k in ("prompt_tokens", "completion_tokens", "total_tokens")):
                raise ValueError("measured token usage missing")
            if not isinstance(body.get("id"), str) or not body["id"]:
                raise ValueError("provider response id missing")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderConfigurationError("XAI_RESPONSE_INVALID: missing output, model, response id or measured usage") from exc
        return ProviderResponse(
            provider=request.provider,
            model=request.model,
            output=output,
            request_hash=request.request_hash,
            metadata={
                "provider_mode": "xai_chat_completions",
                "response_id": body["id"],
                "runtime_model": actual_model,
                "finish_reason": choice.get("finish_reason"),
                "usage": usage,
                "credential_authority": "TV/TVC",
                "governance_authority": False,
            },
        )


def build_http_provider_client(provider: str, *, api_key: Optional[str] = None, base_url: Optional[str] = None) -> Union[StegVerseLocalHTTPProviderClient, OpenAIHTTPProviderClient, AnthropicHTTPProviderClient, XAIHTTPProviderClient]:
    normalized = provider.lower().strip()
    if normalized in {"stegverse", "stegverse-local", "stegverse_local", "local-sovereign"}:
        return StegVerseLocalHTTPProviderClient(base_url=base_url or "http://127.0.0.1:11434/v1/chat/completions")
    if normalized in {"openai", "chatgpt", "openai_http"}:
        return OpenAIHTTPProviderClient(api_key=api_key, base_url=base_url or "https://api.openai.com/v1/chat/completions")
    if normalized in {"anthropic", "claude", "anthropic_http"}:
        return AnthropicHTTPProviderClient(api_key=api_key, base_url=base_url or "https://api.anthropic.com/v1/messages")
    if normalized in {"xai", "grok", "xai_http"}:
        return XAIHTTPProviderClient(api_key=api_key, base_url=base_url or "https://api.x.ai/v1/chat/completions")
    raise ValueError(f"unsupported provider for HTTP client: {provider}")


__all__ = ["AnthropicHTTPProviderClient", "OpenAIHTTPProviderClient", "StegVerseLocalHTTPProviderClient", "XAIHTTPProviderClient", "ProviderConfigurationError", "build_http_provider_client"]
