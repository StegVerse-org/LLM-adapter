"""The governed provider call an S1 ephemeral-lease transition injects.

StegBrowser `execute_governed_provider_lease_transition(lease, provider_call=...)`
calls `provider_call(governed_transition)` with the lease's named transition
(transition_id, request_hash, runtime_profile_id) and expects
`{"egress_handoff": ..., "egress_admission": ...}` back. This builds that callable
over the existing route: InTr ingress -> TV/TVC lease -> non-exportable provider
operation -> egress handoff -> exact-response egress ALLOW.

Before any provider operation it checks that the lease names this request: the
same runtime profile and the same envelope request hash. A mismatch is refused,
so no provider call is spent on a lease that could never bind. The egress
decision is injected; nothing here decides, issues a lease, holds a credential or
records anything.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from .anthropic_convergence_bridge import build_anthropic_convergence_envelope
from .anthropic_tvc_broker import RUNTIME_PROFILE_ID as ANTHROPIC_RUNTIME_PROFILE_ID
from .external_llm_connection import admit_external_llm_egress, execute_governed_external_llm, normalize_provider
from .openai_intr_transport import build_openai_intr_envelope
from .openai_tvc_broker import RUNTIME_PROFILE_ID as OPENAI_RUNTIME_PROFILE_ID
from .provider_request import ProviderRequest

# The S1 routes: S1_CHATGPT (OpenAI) and S1_CLAUDE (Anthropic).
S1_RUNTIME_PROFILES = {"openai": OPENAI_RUNTIME_PROFILE_ID, "anthropic": ANTHROPIC_RUNTIME_PROFILE_ID}


class S1LeaseProviderCallError(ValueError):
    pass


def _envelope_request_hash(provider: str, request: ProviderRequest, *, session_id: str, transition_id: str,
                           ingress_disposition: str, ingress_receipt_hash: str, carrier_ref: str,
                           max_output_tokens: int) -> str:
    """The request hash the governed route will bind, computed without a provider call."""
    if provider == "openai":
        return build_openai_intr_envelope(request, transition_id=transition_id, ingress_disposition=ingress_disposition,
                                          ingress_receipt_hash=ingress_receipt_hash, carrier_ref=carrier_ref).request_hash
    return build_anthropic_convergence_envelope(request, session_id=session_id, transition_id=transition_id,
                                                ingress_disposition=ingress_disposition,
                                                ingress_receipt_hash=ingress_receipt_hash, carrier_ref=carrier_ref,
                                                max_tokens=max_output_tokens).request_hash


def build_s1_provider_call(
    request: ProviderRequest,
    *,
    session_id: str,
    measurement_id: str,
    ingress_disposition: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    lease_receipt: Mapping[str, Any],
    broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    egress_decider: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    max_output_tokens: int = 2048,
) -> Callable[[Mapping[str, Any]], dict[str, Any]]:
    """Return the `provider_call` for one S1 lease transition.

    `egress_decider(egress_handoff)` is the existing Interlock/InTr egress decision
    and returns `{"disposition": ..., "egress_receipt_hash": ...}`. A refused lease
    binding or a non-ALLOW egress raises PermissionError, which the StegBrowser
    entrypoint records as DENY; anything malformed raises a ValueError (FAIL_CLOSED).
    """
    provider = normalize_provider(request.provider)
    if provider not in S1_RUNTIME_PROFILES:
        raise S1LeaseProviderCallError(f"{provider} is not an S1 governed provider route")
    if not callable(egress_decider):
        raise S1LeaseProviderCallError("egress_decider required")

    def provider_call(governed: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(governed, Mapping):
            raise S1LeaseProviderCallError("governed transition must be an object")
        transition_id = governed.get("transition_id")
        if not isinstance(transition_id, str) or not transition_id:
            raise S1LeaseProviderCallError("governed transition_id required")
        if governed.get("runtime_profile_id") != S1_RUNTIME_PROFILES[provider]:
            raise PermissionError("lease runtime_profile_id does not name this provider route")
        expected = _envelope_request_hash(provider, request, session_id=session_id, transition_id=transition_id,
                                          ingress_disposition=ingress_disposition,
                                          ingress_receipt_hash=ingress_receipt_hash, carrier_ref=carrier_ref,
                                          max_output_tokens=max_output_tokens)
        if governed.get("request_hash") != expected:
            raise PermissionError("lease request_hash does not name this request")

        result = execute_governed_external_llm(
            request, session_id=session_id, transition_id=transition_id, measurement_id=measurement_id,
            ingress_disposition=ingress_disposition, ingress_receipt_hash=ingress_receipt_hash, carrier_ref=carrier_ref,
            lease_receipt=lease_receipt, broker_submitter=broker_submitter, max_output_tokens=max_output_tokens)
        handoff = dict(result.egress_handoff)
        decision = egress_decider(dict(handoff))
        if not isinstance(decision, Mapping):
            raise S1LeaseProviderCallError("egress decision malformed")
        if decision.get("disposition") != "ALLOW":
            raise PermissionError("egress InTr " + str(decision.get("disposition")))
        # An egress authority cannot approve a different transition or response.
        for field, expected in (("transition_id", transition_id), ("request_hash", expected),
                                ("response_hash", result.response_hash)):
            if field in decision and decision[field] != expected:
                raise PermissionError("egress InTr " + field + " binding mismatch")
        admission = admit_external_llm_egress(result, egress_disposition="ALLOW",
                                              egress_receipt_hash=str(decision.get("egress_receipt_hash")),
                                              admitted_response_hash=result.response_hash)
        return {"egress_handoff": handoff, "egress_admission": admission.to_dict()}

    return provider_call


__all__ = ["S1_RUNTIME_PROFILES", "S1LeaseProviderCallError", "build_s1_provider_call"]
