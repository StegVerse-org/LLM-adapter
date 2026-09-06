"""Interlock/InTr-bound transport for optional Z.ai inference.

This module is an interoperability transport only. It never grants transition,
route, credential, custody, heartbeat, scheduler, worker, or publication
authority. A Z.ai request may leave StegVerse only after a contemporaneous
Interlock/InTr ALLOW receipt has been bound to the exact ProviderRequest hash.
The returned provider response has authority effect NONE and requires a separate
egress Interlock/InTr evaluation before any state-changing consequence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional
from urllib.parse import urljoin

import requests

from .provider_client import ProviderResponse
from .provider_request import ProviderRequest, stable_hash


PROTOCOL_VERSION = "stegverse.intr.zai.transport.v1"
ZAI_GENERAL_BASE_URL = "https://api.z.ai/api/paas/v4"
ZAI_CODING_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
_ALLOWED_BASE_URLS = {ZAI_GENERAL_BASE_URL, ZAI_CODING_BASE_URL}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ZAITransportError(RuntimeError):
    """Base class for fail-closed Z.ai transport failures."""


class ZAITransportAdmissionError(ZAITransportError):
    """Raised when ingress governance does not admit the exact request."""


class ZAITransportConfigurationError(ZAITransportError):
    """Raised when transport configuration would escape the bounded Z.ai lane."""


@dataclass(frozen=True)
class ZAIInTrEnvelope:
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
class ZAITransportResult:
    envelope: ZAIInTrEnvelope
    response: ProviderResponse
    egress_intr_required: bool = True
    authority_effect: str = "NONE"

    def evidence(self) -> dict[str, Any]:
        return {
            "protocol_version": self.envelope.protocol_version,
            "transport_id": self.envelope.transport_id,
            "transition_id": self.envelope.transition_id,
            "request_hash": self.envelope.request_hash,
            "envelope_hash": self.envelope.envelope_hash,
            "ingress_receipt_hash": self.envelope.ingress_receipt_hash,
            "provider": self.response.provider,
            "model": self.response.model,
            "response_hash": stable_hash(
                {
                    "provider": self.response.provider,
                    "model": self.response.model,
                    "output": self.response.output,
                    "request_hash": self.response.request_hash,
                    "metadata": dict(self.response.metadata),
                }
            ),
            "egress_intr_required": True,
            "authority_effect": "NONE",
            "credential_material_present": False,
        }


def build_zai_intr_envelope(
    request: ProviderRequest,
    *,
    transition_id: str,
    ingress_disposition: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    endpoint_profile: str = "general",
    credential_class: str = "TV_TVC_PROVIDER_SECRET",
) -> ZAIInTrEnvelope:
    """Bind an exact provider request to already-observed ingress ALLOW evidence."""

    if ingress_disposition != "ALLOW":
        raise ZAITransportAdmissionError("Z.ai transport requires contemporaneous ingress InTr ALLOW")
    if not transition_id.strip():
        raise ZAITransportAdmissionError("transition_id is required")
    if not _SHA256_RE.fullmatch(ingress_receipt_hash):
        raise ZAITransportAdmissionError("ingress_receipt_hash must be an exact lowercase sha256")
    if not carrier_ref.strip():
        raise ZAITransportAdmissionError("carrier_ref is required for reconstruction")
    if request.provider.lower().strip() not in {"z.ai", "zai", "z_ai"}:
        raise ZAITransportAdmissionError("ProviderRequest must explicitly target Z.ai")
    if endpoint_profile not in {"general", "coding"}:
        raise ZAITransportConfigurationError("endpoint_profile must be 'general' or 'coding'")
    if credential_class != "TV_TVC_PROVIDER_SECRET":
        raise ZAITransportAdmissionError("hosted Z.ai credentials must remain under TV/TVC authority")

    transport_id = stable_hash(
        {
            "protocol_version": PROTOCOL_VERSION,
            "transition_id": transition_id,
            "request_hash": request.request_hash,
            "ingress_receipt_hash": ingress_receipt_hash,
            "carrier_ref": carrier_ref,
            "endpoint_profile": endpoint_profile,
        }
    )
    return ZAIInTrEnvelope(
        protocol_version=PROTOCOL_VERSION,
        transport_id=transport_id,
        transition_id=transition_id,
        request_hash=request.request_hash,
        provider="z.ai",
        model=request.model,
        endpoint_profile=endpoint_profile,
        ingress_receipt_hash=ingress_receipt_hash,
        credential_authority="TV/TVC",
        credential_class=credential_class,
        carrier_ref=carrier_ref,
    )


@dataclass(frozen=True)
class ZAIHTTPTransport:
    """OpenAI-compatible Z.ai transport executed only after ingress admission.

    `credential` is intentionally supplied per execution and is never serialized
    into the envelope, response metadata, or evidence. Production callers are
    responsible for obtaining it through the existing TV/TVC authority path.
    """

    credential: str
    base_url: str = ZAI_GENERAL_BASE_URL
    timeout_seconds: int = 120

    def __post_init__(self) -> None:
        normalized = self.base_url.rstrip("/")
        if normalized not in _ALLOWED_BASE_URLS:
            raise ZAITransportConfigurationError("Z.ai transport base_url is not an approved official endpoint")
        if not self.credential:
            raise ZAITransportConfigurationError("TV/TVC-resolved Z.ai credential is required")
        object.__setattr__(self, "base_url", normalized)

    def complete(self, envelope: ZAIInTrEnvelope, request: ProviderRequest) -> ZAITransportResult:
        if envelope.protocol_version != PROTOCOL_VERSION:
            raise ZAITransportAdmissionError("unsupported Z.ai InTr transport protocol version")
        if envelope.authority_effect != "NONE" or not envelope.egress_intr_required:
            raise ZAITransportAdmissionError("transport envelope attempts authority escalation")
        if envelope.request_hash != request.request_hash:
            raise ZAITransportAdmissionError("ProviderRequest hash does not match admitted transport envelope")
        expected_profile = "coding" if self.base_url == ZAI_CODING_BASE_URL else "general"
        if envelope.endpoint_profile != expected_profile:
            raise ZAITransportConfigurationError("transport endpoint profile does not match admitted envelope")

        payload = {
            "model": request.model,
            "messages": [message.to_dict() for message in request.messages],
            "temperature": request.temperature,
        }
        response = requests.post(
            urljoin(self.base_url + "/", "chat/completions"),
            headers={"Authorization": f"Bearer {self.credential}", "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices") or []
        if not choices or not isinstance(choices[0], Mapping):
            raise ZAITransportError("Z.ai response missing choices[0]")
        message = choices[0].get("message") or {}
        output = message.get("content")
        if not isinstance(output, str):
            raise ZAITransportError("Z.ai response missing text content")
        usage = body.get("usage") if isinstance(body.get("usage"), Mapping) else {}
        provider_response = ProviderResponse(
            provider="z.ai",
            model=request.model,
            output=output,
            request_hash=request.request_hash,
            metadata={
                "provider_mode": "zai_openai_compatible_intr_transport",
                "response_id": body.get("id", "unresolved"),
                "finish_reason": choices[0].get("finish_reason", "unresolved"),
                "runtime_model": body.get("model", request.model),
                "usage": dict(usage),
                "transport_id": envelope.transport_id,
                "ingress_receipt_hash": envelope.ingress_receipt_hash,
                "credential_authority": "TV/TVC",
                "credential_material_present": False,
                "egress_intr_required": True,
                "authority_effect": "NONE",
            },
        )
        return ZAITransportResult(envelope=envelope, response=provider_response)


__all__ = [
    "PROTOCOL_VERSION",
    "ZAI_GENERAL_BASE_URL",
    "ZAI_CODING_BASE_URL",
    "ZAITransportError",
    "ZAITransportAdmissionError",
    "ZAITransportConfigurationError",
    "ZAIInTrEnvelope",
    "ZAITransportResult",
    "ZAIHTTPTransport",
    "build_zai_intr_envelope",
]
