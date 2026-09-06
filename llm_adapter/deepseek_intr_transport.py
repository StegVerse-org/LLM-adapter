"""Interlock/InTr-bound transport for optional DeepSeek inference.

This interoperability lane is non-authoritative. A DeepSeek request may leave
StegVerse only after a contemporaneous Interlock/InTr ALLOW receipt is bound to
the exact canonical outbound bytes. Provider output has authority effect NONE
and requires a separate egress Interlock/InTr ALLOW before consequence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import requests

from .provider_client import ProviderResponse
from .provider_request import ProviderRequest, stable_hash, stable_json

PROTOCOL_VERSION = "stegverse.intr.deepseek.transport.v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_CHAT_URL = f"{DEEPSEEK_BASE_URL}/chat/completions"
SUPPORTED_MODELS = frozenset({"deepseek-v4-flash", "deepseek-v4-pro"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class DeepSeekTransportError(RuntimeError):
    """Base class for fail-closed DeepSeek transport failures."""


class DeepSeekTransportAdmissionError(DeepSeekTransportError):
    """Raised when ingress/egress evidence does not admit exact bytes."""


class DeepSeekTransportConfigurationError(DeepSeekTransportError):
    """Raised when runtime configuration escapes the bounded DeepSeek lane."""


def deepseek_wire_payload(request: ProviderRequest) -> dict[str, Any]:
    if request.model not in SUPPORTED_MODELS:
        raise DeepSeekTransportConfigurationError(f"unsupported DeepSeek model: {request.model}")
    return {
        "model": request.model,
        "messages": [message.to_dict() for message in request.messages],
        "temperature": request.temperature,
        "stream": False,
    }


def deepseek_wire_bytes(request: ProviderRequest) -> bytes:
    return stable_json(deepseek_wire_payload(request)).encode("utf-8")


def deepseek_wire_request_hash(request: ProviderRequest) -> str:
    return stable_hash(deepseek_wire_payload(request))


def assert_no_deepseek_secret_material(secret: str, /, **structures: Any) -> None:
    if not isinstance(secret, str) or not secret.strip():
        raise DeepSeekTransportConfigurationError("TV/TVC-resolved DeepSeek credential is required")
    for name, value in structures.items():
        if secret in stable_json(value):
            raise DeepSeekTransportError(f"credential material detected in {name}")


@dataclass(frozen=True)
class DeepSeekInTrEnvelope:
    protocol_version: str
    transport_id: str
    transition_id: str
    request_hash: str
    provider: str
    model: str
    endpoint_profile: str
    ingress_receipt_hash: str
    credential_authority: str
    credential_class: str
    carrier_ref: str
    authority_effect: str = "NONE"
    egress_intr_required: bool = True
    credential_material_present: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "transport_id": self.transport_id,
            "transition_id": self.transition_id,
            "request_hash": self.request_hash,
            "provider": self.provider,
            "model": self.model,
            "endpoint_profile": self.endpoint_profile,
            "ingress_receipt_hash": self.ingress_receipt_hash,
            "credential_authority": self.credential_authority,
            "credential_class": self.credential_class,
            "carrier_ref": self.carrier_ref,
            "authority_effect": self.authority_effect,
            "egress_intr_required": self.egress_intr_required,
            "credential_material_present": self.credential_material_present,
        }

    @property
    def envelope_hash(self) -> str:
        return stable_hash(self.to_dict())


@dataclass(frozen=True)
class DeepSeekTransportResult:
    envelope: DeepSeekInTrEnvelope
    response: ProviderResponse
    provider_request_hash: str
    authority_effect: str = "NONE"
    egress_intr_required: bool = True

    def evidence(self) -> dict[str, Any]:
        return {
            "protocol_version": self.envelope.protocol_version,
            "transport_id": self.envelope.transport_id,
            "transition_id": self.envelope.transition_id,
            "request_hash": self.envelope.request_hash,
            "provider_request_hash": self.provider_request_hash,
            "envelope_hash": self.envelope.envelope_hash,
            "ingress_receipt_hash": self.envelope.ingress_receipt_hash,
            "provider": self.response.provider,
            "model": self.response.model,
            "response_hash": self.response.response_hash,
            "egress_intr_required": True,
            "authority_effect": "NONE",
            "credential_material_present": False,
        }


def build_deepseek_intr_envelope(
    request: ProviderRequest,
    *,
    transition_id: str,
    ingress_disposition: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    endpoint_profile: str = "deepseek_openai_compatible",
    credential_class: str = "TV_TVC_PROVIDER_SECRET",
) -> DeepSeekInTrEnvelope:
    if ingress_disposition != "ALLOW":
        raise DeepSeekTransportAdmissionError("DeepSeek transport requires contemporaneous ingress InTr ALLOW")
    if not transition_id.strip():
        raise DeepSeekTransportAdmissionError("transition_id is required")
    if not _SHA256_RE.fullmatch(ingress_receipt_hash):
        raise DeepSeekTransportAdmissionError("ingress_receipt_hash must be an exact lowercase sha256")
    if not carrier_ref.strip():
        raise DeepSeekTransportAdmissionError("carrier_ref is required for reconstruction")
    if request.provider.lower().strip() not in {"deepseek", "deepseek_http"}:
        raise DeepSeekTransportAdmissionError("ProviderRequest must explicitly target DeepSeek")
    if endpoint_profile != "deepseek_openai_compatible":
        raise DeepSeekTransportConfigurationError("unsupported DeepSeek endpoint profile")
    if credential_class != "TV_TVC_PROVIDER_SECRET":
        raise DeepSeekTransportAdmissionError("hosted DeepSeek credentials must remain under TV/TVC authority")

    wire_hash = deepseek_wire_request_hash(request)
    transport_id = "dsit-" + stable_hash({
        "protocol_version": PROTOCOL_VERSION,
        "transition_id": transition_id,
        "request_hash": wire_hash,
        "ingress_receipt_hash": ingress_receipt_hash,
        "carrier_ref": carrier_ref,
        "endpoint_profile": endpoint_profile,
    })
    return DeepSeekInTrEnvelope(
        protocol_version=PROTOCOL_VERSION,
        transport_id=transport_id,
        transition_id=transition_id,
        request_hash=wire_hash,
        provider="deepseek",
        model=request.model,
        endpoint_profile=endpoint_profile,
        ingress_receipt_hash=ingress_receipt_hash,
        credential_authority="TV/TVC",
        credential_class=credential_class,
        carrier_ref=carrier_ref,
    )


@dataclass(frozen=True)
class DeepSeekHTTPTransport:
    credential_resolver: Callable[[], str]
    base_url: str = DEEPSEEK_BASE_URL
    timeout_seconds: int = 120

    def __post_init__(self) -> None:
        normalized = self.base_url.rstrip("/")
        if normalized != DEEPSEEK_BASE_URL:
            raise DeepSeekTransportConfigurationError("DeepSeek transport base_url is not the approved official endpoint")
        if not callable(self.credential_resolver):
            raise DeepSeekTransportConfigurationError("TV/TVC credential resolver is required")
        object.__setattr__(self, "base_url", normalized)

    def complete(self, envelope: DeepSeekInTrEnvelope, request: ProviderRequest) -> DeepSeekTransportResult:
        if envelope.protocol_version != PROTOCOL_VERSION:
            raise DeepSeekTransportAdmissionError("unsupported DeepSeek InTr protocol version")
        if envelope.authority_effect != "NONE" or not envelope.egress_intr_required or envelope.credential_material_present:
            raise DeepSeekTransportAdmissionError("transport envelope attempts authority escalation")
        if envelope.endpoint_profile != "deepseek_openai_compatible":
            raise DeepSeekTransportConfigurationError("runtime endpoint profile does not match admitted envelope")
        if envelope.request_hash != deepseek_wire_request_hash(request):
            raise DeepSeekTransportAdmissionError("exact outbound DeepSeek request hash does not match admitted envelope")

        credential = self.credential_resolver()
        payload = deepseek_wire_payload(request)
        assert_no_deepseek_secret_material(credential, envelope=envelope.to_dict(), outbound_payload=payload)
        response = requests.post(
            DEEPSEEK_CHAT_URL,
            headers={"Authorization": f"Bearer {credential}", "Content-Type": "application/json", "Accept": "application/json"},
            data=deepseek_wire_bytes(request),
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, Mapping):
            raise DeepSeekTransportError("DeepSeek response body must be an object")
        choices = body.get("choices") or []
        if not choices or not isinstance(choices[0], Mapping):
            raise DeepSeekTransportError("DeepSeek response missing choices[0]")
        message = choices[0].get("message") or {}
        output = message.get("content") if isinstance(message, Mapping) else None
        if not isinstance(output, str) or not output.strip():
            raise DeepSeekTransportError("DeepSeek response missing usable text content")
        response_id = body.get("id")
        runtime_model = body.get("model")
        finish_reason = choices[0].get("finish_reason")
        if not isinstance(response_id, str) or not response_id:
            raise DeepSeekTransportError("DeepSeek response missing id")
        if not isinstance(runtime_model, str) or not runtime_model:
            raise DeepSeekTransportError("DeepSeek response missing model")
        if not isinstance(finish_reason, str):
            raise DeepSeekTransportError("DeepSeek response missing finish_reason")
        usage = body.get("usage")
        if usage is not None:
            if not isinstance(usage, Mapping):
                raise DeepSeekTransportError("DeepSeek usage must be an object")
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                if not isinstance(usage.get(key), int) or isinstance(usage.get(key), bool):
                    raise DeepSeekTransportError("DeepSeek usage token counts must be integers")

        provider_response = ProviderResponse(
            provider="deepseek",
            model=request.model,
            output=output,
            request_hash=envelope.request_hash,
            metadata={
                "provider_mode": "deepseek_openai_compatible_intr_transport",
                "response_id": response_id,
                "finish_reason": finish_reason,
                "runtime_model": runtime_model,
                "usage": dict(usage) if usage is not None else None,
                "transport_id": envelope.transport_id,
                "ingress_receipt_hash": envelope.ingress_receipt_hash,
                "credential_authority": "TV/TVC",
                "credential_material_present": False,
                "egress_intr_required": True,
                "authority_effect": "NONE",
            },
        )
        result = DeepSeekTransportResult(envelope=envelope, response=provider_response, provider_request_hash=request.request_hash)
        assert_no_deepseek_secret_material(
            credential,
            raw_provider_body=body,
            provider_response=provider_response.to_dict(),
            transport_evidence=result.evidence(),
        )
        del credential
        return result


__all__ = [
    "PROTOCOL_VERSION", "DEEPSEEK_BASE_URL", "DEEPSEEK_CHAT_URL", "SUPPORTED_MODELS",
    "DeepSeekTransportError", "DeepSeekTransportAdmissionError", "DeepSeekTransportConfigurationError",
    "DeepSeekInTrEnvelope", "DeepSeekTransportResult", "DeepSeekHTTPTransport",
    "build_deepseek_intr_envelope", "deepseek_wire_payload", "deepseek_wire_bytes",
    "deepseek_wire_request_hash", "assert_no_deepseek_secret_material",
]
