"""Interlock/InTr ingress envelope for governed OpenAI (ChatGPT) inference.

Interoperability only: this module grants no transition, route, credential,
custody, heartbeat, scheduler, worker or publication authority. An OpenAI request
may leave StegVerse only after a contemporaneous Interlock/InTr ALLOW receipt is
bound to the exact canonical outbound request bytes. There is no direct-credential
transport here: execution goes only through the TV/TVC non-exportable broker
(``openai_tvc_broker``), and the returned response requires a separate egress
Interlock/InTr ALLOW before any state-changing consequence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .provider_request import ProviderRequest, stable_hash, stable_json

PROTOCOL_VERSION = "stegverse.intr.openai.transport.v1"
OPENAI_PROVIDER_ALIASES = {"openai", "chatgpt", "openai_http"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class OpenAITransportError(RuntimeError):
    """Base class for fail-closed OpenAI transport failures."""


class OpenAITransportAdmissionError(OpenAITransportError):
    """Raised when ingress governance does not admit the exact request."""


def openai_wire_payload(request: ProviderRequest) -> dict[str, Any]:
    return {
        "model": request.model,
        "messages": [message.to_dict() for message in request.messages],
        "temperature": request.temperature,
    }


def openai_wire_bytes(request: ProviderRequest) -> bytes:
    return stable_json(openai_wire_payload(request)).encode("utf-8")


def openai_wire_request_hash(request: ProviderRequest) -> str:
    return stable_hash(openai_wire_payload(request))


@dataclass(frozen=True)
class OpenAIInTrEnvelope:
    protocol_version: str
    transport_id: str
    transition_id: str
    request_hash: str
    provider: str
    model: str
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


def build_openai_intr_envelope(
    request: ProviderRequest,
    *,
    transition_id: str,
    ingress_disposition: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    credential_class: str = "TV_TVC_PROVIDER_SECRET",
) -> OpenAIInTrEnvelope:
    if ingress_disposition != "ALLOW":
        raise OpenAITransportAdmissionError("OpenAI transport requires contemporaneous ingress InTr ALLOW")
    if not transition_id.strip():
        raise OpenAITransportAdmissionError("transition_id is required")
    if not _SHA256_RE.fullmatch(ingress_receipt_hash):
        raise OpenAITransportAdmissionError("ingress_receipt_hash must be an exact lowercase sha256")
    if not carrier_ref.strip():
        raise OpenAITransportAdmissionError("carrier_ref is required for reconstruction")
    if request.provider.lower().strip() not in OPENAI_PROVIDER_ALIASES:
        raise OpenAITransportAdmissionError("ProviderRequest must explicitly target OpenAI")
    if credential_class != "TV_TVC_PROVIDER_SECRET":
        raise OpenAITransportAdmissionError("hosted OpenAI credentials must remain under TV/TVC authority")

    wire_hash = openai_wire_request_hash(request)
    transport_id = "oait-" + stable_hash({
        "protocol_version": PROTOCOL_VERSION,
        "transition_id": transition_id,
        "request_hash": wire_hash,
        "ingress_receipt_hash": ingress_receipt_hash,
        "carrier_ref": carrier_ref,
    })
    return OpenAIInTrEnvelope(
        protocol_version=PROTOCOL_VERSION,
        transport_id=transport_id,
        transition_id=transition_id,
        request_hash=wire_hash,
        provider="openai",
        model=request.model,
        ingress_receipt_hash=ingress_receipt_hash,
        credential_authority="TV/TVC",
        credential_class=credential_class,
        carrier_ref=carrier_ref,
    )


__all__ = [
    "PROTOCOL_VERSION",
    "OPENAI_PROVIDER_ALIASES",
    "OpenAITransportError",
    "OpenAITransportAdmissionError",
    "OpenAIInTrEnvelope",
    "build_openai_intr_envelope",
    "openai_wire_payload",
    "openai_wire_bytes",
    "openai_wire_request_hash",
]
