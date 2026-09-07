"""Canonical exact provider payload bytes for the TVC Kimi operation.

This mirrors the admitted `openai_chat_completions` payload emitted by the
TVC-owned vault broker.  It intentionally excludes credentials and HTTP headers.
"""
from __future__ import annotations

from typing import Any

from .kimi_intr_transport import KimiTransportConfigurationError, SUPPORTED_MODELS
from .provider_request import ProviderRequest, stable_hash, stable_json


def canonical_kimi_tvc_provider_payload(
    request: ProviderRequest,
    *,
    max_output_tokens: int = 2048,
    response_format: str = "text",
) -> dict[str, Any]:
    if request.provider.lower().strip() not in {"kimi", "moonshot", "kimi_http"}:
        raise KimiTransportConfigurationError("canonical TVC provider wire requires Kimi provider")
    if request.model not in SUPPORTED_MODELS:
        raise KimiTransportConfigurationError(f"unsupported Kimi model: {request.model}")
    if len(request.messages) != 1 or request.messages[0].role != "user":
        raise KimiTransportConfigurationError("canonical TVC Kimi v1 requires exactly one user message")
    if not isinstance(max_output_tokens, int) or max_output_tokens < 1 or max_output_tokens > 16384:
        raise KimiTransportConfigurationError("max_output_tokens outside TVC boundary")
    if response_format not in {"text", "json"}:
        raise KimiTransportConfigurationError("unsupported response format")
    payload: dict[str, Any] = {
        "model": request.model,
        "messages": [{"role": "user", "content": request.messages[0].content}],
        "max_tokens": max_output_tokens,
        "stream": False,
    }
    if response_format == "json":
        payload["response_format"] = {"type": "json_object"}
    return payload


def canonical_kimi_tvc_provider_wire_bytes(
    request: ProviderRequest,
    *,
    max_output_tokens: int = 2048,
    response_format: str = "text",
) -> bytes:
    return stable_json(
        canonical_kimi_tvc_provider_payload(
            request,
            max_output_tokens=max_output_tokens,
            response_format=response_format,
        )
    ).encode("utf-8")


def canonical_kimi_tvc_provider_request_hash(
    request: ProviderRequest,
    *,
    max_output_tokens: int = 2048,
    response_format: str = "text",
) -> str:
    return stable_hash(
        canonical_kimi_tvc_provider_payload(
            request,
            max_output_tokens=max_output_tokens,
            response_format=response_format,
        )
    )


__all__ = [
    "canonical_kimi_tvc_provider_payload",
    "canonical_kimi_tvc_provider_wire_bytes",
    "canonical_kimi_tvc_provider_request_hash",
]
