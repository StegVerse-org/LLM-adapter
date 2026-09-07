"""Bridge the provider-neutral adapter request to canonical Anthropic #288.

This module does not define another Anthropic transport contract.  It projects
``llm_adapter.provider_request.ProviderRequest`` into the canonical
``stegverse.intr.anthropic.transport.v1`` primitives and returns a small
read-only view used by the existing TVC broker path.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .anthropic_intr_transport import (
    AUTHORITY_EFFECT,
    CREDENTIAL_CLASS,
    ENDPOINT_PROFILE,
    PROTOCOL_VERSION,
    IngressDecision,
    ProviderRequest as CanonicalAnthropicRequest,
    TransportConfig,
    build_transport_envelope,
    compute_request_hash,
    envelope_hash,
)
from .provider_request import ProviderRequest


class AnthropicConvergenceBridgeError(RuntimeError):
    pass


def _canonical_payload(request: ProviderRequest, *, max_tokens: int) -> dict[str, Any]:
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise AnthropicConvergenceBridgeError("positive max_tokens required")
    systems = [message.content for message in request.messages if message.role == "system"]
    messages = [message.to_dict() for message in request.messages if message.role != "system"]
    payload: dict[str, Any] = {"messages": messages, "max_tokens": max_tokens}
    if systems:
        payload["system"] = "\n".join(systems)
    # Claude 5 only admits its default temperature.  Omitting the field is the
    # exact canonical representation for the provider-neutral default of 0.0.
    if request.temperature == 1:
        payload["temperature"] = 1
    elif request.temperature != 0:
        raise AnthropicConvergenceBridgeError(
            "non-default Claude temperature is not admitted by the canonical transport"
        )
    return payload


def canonical_anthropic_request(
    request: ProviderRequest,
    *,
    transition_id: str = "pending-intr-transition",
    session_id: str = "pending-governed-session",
    max_tokens: int = 2048,
) -> CanonicalAnthropicRequest:
    if request.provider.lower().strip() not in {"anthropic", "claude", "anthropic_http"}:
        raise AnthropicConvergenceBridgeError("provider-neutral request must target Anthropic")
    projected = CanonicalAnthropicRequest(
        provider="anthropic",
        model=request.model,
        endpoint_profile=ENDPOINT_PROFILE,
        payload=_canonical_payload(request, max_tokens=max_tokens),
        request_hash="",
        transition_id=transition_id,
        session_id=session_id,
    )
    return replace(projected, request_hash=compute_request_hash(projected))


def anthropic_wire_request_hash(request: ProviderRequest, *, max_tokens: int = 2048) -> str:
    """Return the canonical #288 request hash used for ingress binding."""
    return canonical_anthropic_request(request, max_tokens=max_tokens).request_hash


@dataclass(frozen=True)
class AnthropicConvergenceEnvelope:
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
    envelope_hash: str
    authority_effect: str = AUTHORITY_EFFECT
    egress_intr_required: bool = True
    credential_material_present: bool = False


def build_anthropic_convergence_envelope(
    request: ProviderRequest,
    *,
    session_id: str,
    transition_id: str,
    ingress_disposition: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    max_tokens: int = 2048,
) -> AnthropicConvergenceEnvelope:
    canonical = canonical_anthropic_request(
        request,
        transition_id=transition_id,
        session_id=session_id,
        max_tokens=max_tokens,
    )
    ingress = IngressDecision(
        disposition=ingress_disposition,
        request_hash=canonical.request_hash,
        transition_id=transition_id,
        ingress_receipt_hash=ingress_receipt_hash,
        carrier_ref=carrier_ref,
    )
    material = build_transport_envelope(canonical, ingress, TransportConfig())
    return AnthropicConvergenceEnvelope(
        protocol_version=PROTOCOL_VERSION,
        transport_id=material["transport_id"],
        transition_id=transition_id,
        request_hash=canonical.request_hash,
        provider="anthropic",
        model=request.model,
        endpoint_profile=ENDPOINT_PROFILE,
        ingress_receipt_hash=ingress_receipt_hash,
        credential_authority="TV/TVC",
        credential_class=CREDENTIAL_CLASS,
        carrier_ref=carrier_ref,
        envelope_hash=envelope_hash(material),
    )


__all__ = [
    "AnthropicConvergenceBridgeError",
    "AnthropicConvergenceEnvelope",
    "anthropic_wire_request_hash",
    "build_anthropic_convergence_envelope",
    "canonical_anthropic_request",
]
