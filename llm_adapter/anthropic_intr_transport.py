"""Interlock/InTr-bound transport for optional Anthropic inference.

Provider execution is non-authoritative. Exact outbound bytes require a
contemporaneous ingress InTr ALLOW. Provider output requires a separate egress
InTr ALLOW before consequence. Credential material is resolved at send time by
TV/TVC and is never serialized into evidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import requests

from .provider_client import ProviderResponse
from .provider_request import ProviderRequest, stable_hash, stable_json

PROTOCOL_VERSION = "stegverse.intr.anthropic.transport.v1"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

class AnthropicTransportError(RuntimeError): pass
class AnthropicTransportAdmissionError(AnthropicTransportError): pass
class AnthropicTransportConfigurationError(AnthropicTransportError): pass


def anthropic_wire_payload(request: ProviderRequest, *, max_tokens: int = 1024) -> dict[str, Any]:
    systems = [m.content for m in request.messages if m.role == "system"]
    conversation = [m.to_dict() for m in request.messages if m.role != "system"]
    payload: dict[str, Any] = {
        "model": request.model,
        "messages": conversation,
        "temperature": request.temperature,
        "max_tokens": max_tokens,
    }
    if systems:
        payload["system"] = "\n".join(systems)
    return payload


def anthropic_wire_bytes(request: ProviderRequest, *, max_tokens: int = 1024) -> bytes:
    return stable_json(anthropic_wire_payload(request, max_tokens=max_tokens)).encode("utf-8")


def anthropic_wire_request_hash(request: ProviderRequest, *, max_tokens: int = 1024) -> str:
    return stable_hash(anthropic_wire_payload(request, max_tokens=max_tokens))


def _no_secret(secret: str, **structures: Any) -> None:
    if not isinstance(secret, str) or not secret.strip():
        raise AnthropicTransportConfigurationError("TV/TVC-resolved Anthropic credential is required")
    for name, value in structures.items():
        if secret in stable_json(value):
            raise AnthropicTransportError(f"credential material detected in {name}")

@dataclass(frozen=True)
class AnthropicInTrEnvelope:
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
    def to_dict(self) -> dict[str, Any]: return dict(self.__dict__)
    @property
    def envelope_hash(self) -> str: return stable_hash(self.to_dict())

@dataclass(frozen=True)
class AnthropicTransportResult:
    envelope: AnthropicInTrEnvelope
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


def build_anthropic_intr_envelope(request: ProviderRequest, *, transition_id: str,
    ingress_disposition: str, ingress_receipt_hash: str, carrier_ref: str,
    endpoint_profile: str = "anthropic_messages_v1", credential_class: str = "TV_TVC_PROVIDER_SECRET",
    max_tokens: int = 1024) -> AnthropicInTrEnvelope:
    if ingress_disposition != "ALLOW": raise AnthropicTransportAdmissionError("Anthropic transport requires ingress InTr ALLOW")
    if not transition_id.strip(): raise AnthropicTransportAdmissionError("transition_id is required")
    if not _SHA256_RE.fullmatch(ingress_receipt_hash): raise AnthropicTransportAdmissionError("ingress_receipt_hash must be lowercase sha256")
    if not carrier_ref.strip(): raise AnthropicTransportAdmissionError("carrier_ref is required")
    if request.provider.lower().strip() not in {"anthropic", "claude", "anthropic_http"}: raise AnthropicTransportAdmissionError("ProviderRequest must explicitly target Anthropic")
    if endpoint_profile != "anthropic_messages_v1": raise AnthropicTransportConfigurationError("unsupported Anthropic endpoint profile")
    if credential_class != "TV_TVC_PROVIDER_SECRET": raise AnthropicTransportAdmissionError("Anthropic credential must remain under TV/TVC authority")
    wire_hash = anthropic_wire_request_hash(request, max_tokens=max_tokens)
    transport_id = "anit-" + stable_hash({"protocol_version":PROTOCOL_VERSION,"transition_id":transition_id,"request_hash":wire_hash,"ingress_receipt_hash":ingress_receipt_hash,"carrier_ref":carrier_ref,"endpoint_profile":endpoint_profile})
    return AnthropicInTrEnvelope(PROTOCOL_VERSION, transport_id, transition_id, wire_hash, "anthropic", request.model, endpoint_profile, ingress_receipt_hash, "TV/TVC", credential_class, carrier_ref)

@dataclass(frozen=True)
class AnthropicHTTPTransport:
    credential_resolver: Callable[[], str]
    base_url: str = ANTHROPIC_URL
    anthropic_version: str = ANTHROPIC_VERSION
    max_tokens: int = 1024
    timeout_seconds: int = 120
    def __post_init__(self) -> None:
        if self.base_url != ANTHROPIC_URL: raise AnthropicTransportConfigurationError("Anthropic base_url is not approved official endpoint")
        if not callable(self.credential_resolver): raise AnthropicTransportConfigurationError("TV/TVC credential resolver is required")
    def complete(self, envelope: AnthropicInTrEnvelope, request: ProviderRequest) -> AnthropicTransportResult:
        if envelope.protocol_version != PROTOCOL_VERSION or envelope.authority_effect != "NONE" or not envelope.egress_intr_required:
            raise AnthropicTransportAdmissionError("invalid Anthropic transport envelope")
        if envelope.request_hash != anthropic_wire_request_hash(request, max_tokens=self.max_tokens):
            raise AnthropicTransportAdmissionError("exact Anthropic request hash mismatch")
        credential = self.credential_resolver()
        payload = anthropic_wire_payload(request, max_tokens=self.max_tokens)
        _no_secret(credential, envelope=envelope.to_dict(), outbound_payload=payload)
        response = requests.post(self.base_url, headers={"x-api-key":credential,"anthropic-version":self.anthropic_version,"Content-Type":"application/json","Accept":"application/json"}, data=anthropic_wire_bytes(request, max_tokens=self.max_tokens), timeout=self.timeout_seconds)
        response.raise_for_status(); body = response.json()
        if not isinstance(body, Mapping): raise AnthropicTransportError("Anthropic response body must be object")
        blocks = body.get("content") or []
        output = "".join(b.get("text","") for b in blocks if isinstance(b, Mapping) and b.get("type") == "text")
        if not output.strip(): raise AnthropicTransportError("Anthropic response missing usable text")
        usage = body.get("usage") if isinstance(body.get("usage"), Mapping) else {}
        provider_response = ProviderResponse(provider="anthropic", model=request.model, output=output, request_hash=envelope.request_hash, metadata={"provider_mode":"anthropic_messages_intr_transport","response_id":body.get("id"),"stop_reason":body.get("stop_reason"),"runtime_model":body.get("model"),"usage":dict(usage),"transport_id":envelope.transport_id,"ingress_receipt_hash":envelope.ingress_receipt_hash,"credential_authority":"TV/TVC","credential_material_present":False,"egress_intr_required":True,"authority_effect":"NONE"})
        result = AnthropicTransportResult(envelope, provider_response, request.request_hash)
        _no_secret(credential, raw_provider_body=body, provider_response=provider_response.to_dict(), transport_evidence=result.evidence())
        return result

__all__ = ["PROTOCOL_VERSION","ANTHROPIC_URL","ANTHROPIC_VERSION","AnthropicTransportError","AnthropicTransportAdmissionError","AnthropicTransportConfigurationError","AnthropicInTrEnvelope","AnthropicTransportResult","AnthropicHTTPTransport","build_anthropic_intr_envelope","anthropic_wire_payload","anthropic_wire_bytes","anthropic_wire_request_hash"]
