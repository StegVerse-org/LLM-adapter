"""ProviderClient bridge that completes the full governed external-LLM round trip.

The injected callbacks are adapters to existing Interlock/InTr and TV/TVC
surfaces. They are not implemented or authorized here. A ProviderResponse is
returned to Ecosystem Chat only after ingress ALLOW, provider execution,
Master Records usage submission, and exact-response egress ALLOW all validate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .provider_request import ProviderRequest
from .provider_client import ProviderResponse
from .external_llm_connection import execute_governed_external_llm, admit_external_llm_egress, normalize_provider
from .zai_intr_transport import zai_wire_request_hash
from .deepseek_intr_transport import deepseek_wire_request_hash
from .kimi_intr_transport import kimi_wire_request_hash
from .anthropic_intr_transport import anthropic_wire_request_hash

class GovernedExternalProviderClientError(RuntimeError): pass


def external_wire_request_hash(request: ProviderRequest) -> str:
    provider = normalize_provider(request.provider)
    if provider == "zai": return zai_wire_request_hash(request)
    if provider == "deepseek": return deepseek_wire_request_hash(request)
    if provider == "kimi": return kimi_wire_request_hash(request)
    if provider == "anthropic": return anthropic_wire_request_hash(request)
    raise GovernedExternalProviderClientError("unsupported provider wire hash")


def _required(mapping: Mapping[str, Any], key: str) -> Any:
    value = mapping.get(key)
    if value is None or value == "": raise GovernedExternalProviderClientError(f"missing required governed material: {key}")
    return value

@dataclass(frozen=True)
class GovernedExternalProviderClient:
    """ProviderClient-compatible adapter for Ecosystem Chat distributed execution."""

    session_id: str
    measurement_id_factory: Callable[[ProviderRequest], str]
    ingress_evaluator: Callable[[ProviderRequest, str], Mapping[str, Any]]
    tvc_material_resolver: Callable[[ProviderRequest, Mapping[str, Any]], Mapping[str, Any]]
    egress_evaluator: Callable[[Mapping[str, Any]], Mapping[str, Any]]

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        if not all(callable(x) for x in (self.measurement_id_factory, self.ingress_evaluator, self.tvc_material_resolver, self.egress_evaluator)):
            raise GovernedExternalProviderClientError("governed callback surface incomplete")
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise GovernedExternalProviderClientError("session_id required")

        wire_hash = external_wire_request_hash(request)
        ingress = self.ingress_evaluator(request, wire_hash)
        if not isinstance(ingress, Mapping): raise GovernedExternalProviderClientError("ingress evaluator reply malformed")
        if ingress.get("disposition") != "ALLOW": raise GovernedExternalProviderClientError("ingress InTr did not ALLOW exact request")
        if ingress.get("request_hash") != wire_hash: raise GovernedExternalProviderClientError("ingress InTr exact request hash mismatch")
        transition_id = str(_required(ingress, "transition_id"))
        receipt_hash = str(_required(ingress, "receipt_hash"))
        carrier_ref = str(_required(ingress, "carrier_ref"))

        tvc = self.tvc_material_resolver(request, ingress)
        if not isinstance(tvc, Mapping): raise GovernedExternalProviderClientError("TV/TVC material resolver reply malformed")
        if tvc.get("credential_authority") != "TV/TVC": raise GovernedExternalProviderClientError("TV/TVC credential authority mismatch")
        if tvc.get("credential_material_present") is not False: raise GovernedExternalProviderClientError("credential material may not cross into connection bridge")

        execution_kwargs: dict[str, Any] = {}
        if tvc.get("lease_receipt") is not None or tvc.get("broker_submitter") is not None:
            execution_kwargs["lease_receipt"] = _required(tvc, "lease_receipt")
            execution_kwargs["broker_submitter"] = _required(tvc, "broker_submitter")
        else:
            execution_kwargs["credential_resolver"] = _required(tvc, "credential_resolver")

        result = execute_governed_external_llm(
            request,
            session_id=self.session_id,
            transition_id=transition_id,
            measurement_id=self.measurement_id_factory(request),
            ingress_disposition="ALLOW",
            ingress_receipt_hash=receipt_hash,
            carrier_ref=carrier_ref,
            **execution_kwargs,
        )

        egress = self.egress_evaluator(result.egress_handoff)
        if not isinstance(egress, Mapping): raise GovernedExternalProviderClientError("egress evaluator reply malformed")
        if egress.get("disposition") != "ALLOW": raise GovernedExternalProviderClientError("egress InTr did not ALLOW exact response")
        if egress.get("response_hash") != result.response_hash: raise GovernedExternalProviderClientError("egress InTr exact response hash mismatch")
        admit_external_llm_egress(
            result,
            egress_disposition="ALLOW",
            egress_receipt_hash=str(_required(egress, "receipt_hash")),
            admitted_response_hash=result.response_hash,
        )
        response = result.response
        metadata = dict(response.metadata)
        metadata.update({
            "governed_external_connection": True,
            "ingress_intr_admitted": True,
            "egress_intr_admitted": True,
            "execution_path": result.execution_path,
            "credential_authority": "TV/TVC",
            "credential_material_present": False,
            "authority_effect": "NONE",
        })
        return ProviderResponse(provider=response.provider, model=response.model, output=response.output, request_hash=response.request_hash, metadata=metadata)

__all__ = ["GovernedExternalProviderClientError","GovernedExternalProviderClient","external_wire_request_hash"]
