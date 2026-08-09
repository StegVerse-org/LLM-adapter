"""Sovereign local-model runtime binding for the canonical LLM-adapter path."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence

from .http_provider_clients import StegVerseLocalHTTPProviderClient
from .provider_client import ProviderResponse
from .provider_request import ProviderMessage, ProviderRequest
from .provider_usage import ProviderMetric, build_provider_usage_event
from .master_records_usage_submission import submit_provider_usage_to_master_records


class SovereignLocalModelBindingError(RuntimeError):
    pass


REQUIRED_RUNTIME_PREDICATES = (
    "real_model_process_observed",
    "private_endpoint_only",
    "real_inference_response_observed",
    "measured_usage_persistable",
    "local_training_observed",
)
MEASURED_USAGE_KEYS = ("prompt_tokens", "completion_tokens", "total_tokens", "latency_ms")


@dataclass(frozen=True)
class SovereignLocalModelExecution:
    response: ProviderResponse
    usage_event: dict[str, Any]
    master_records_usage: dict[str, Any]
    binding_receipt: dict[str, Any]


def _validate_micro_node_proof(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("goal_id") != "SOVEREIGN-LOCAL-MODEL-001":
        raise SovereignLocalModelBindingError("local_model_goal_identity_mismatch")
    if proof.get("state") != "VERIFIED_REFERENCE_MODEL_RUNTIME":
        raise SovereignLocalModelBindingError("local_model_runtime_not_verified")
    if proof.get("authority_effect") != "NONE":
        raise SovereignLocalModelBindingError("local_model_proof_authority_escalation")
    predicates = proof.get("predicates")
    if not isinstance(predicates, Mapping):
        raise SovereignLocalModelBindingError("local_model_predicates_missing")
    missing = [name for name in REQUIRED_RUNTIME_PREDICATES if predicates.get(name) is not True]
    if missing:
        raise SovereignLocalModelBindingError("local_model_runtime_predicates_failed:" + ",".join(missing))
    if predicates.get("third_party_inference_required") is not False:
        raise SovereignLocalModelBindingError("third_party_inference_dependency_detected")
    if predicates.get("model_output_grants_authority") is not False:
        raise SovereignLocalModelBindingError("model_output_authority_detected")
    usage = proof.get("usage")
    if not isinstance(usage, Mapping) or not all(isinstance(usage.get(k), (int, float)) for k in MEASURED_USAGE_KEYS):
        raise SovereignLocalModelBindingError("local_model_measured_usage_invalid")
    if not str(proof.get("proof_hash", "")).strip() or not str(proof.get("model_hash", "")).strip():
        raise SovereignLocalModelBindingError("local_model_hash_evidence_missing")
    normalized = dict(proof)
    normalized["source_proof_schema"] = proof["schema"]
    return normalized


def _validate_llm_adapter_proof(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("state") != "COMPLETE":
        raise SovereignLocalModelBindingError("local_adapter_runtime_not_complete")
    if proof.get("real_local_inference_observed") is not True:
        raise SovereignLocalModelBindingError("local_adapter_real_inference_not_observed")
    if proof.get("external_provider_used") is not False or proof.get("network_required_for_model") is not False:
        raise SovereignLocalModelBindingError("local_adapter_external_dependency_detected")
    if proof.get("authority_attached") is not False or proof.get("execution_authority") is not False:
        raise SovereignLocalModelBindingError("local_adapter_proof_authority_escalation")
    identity = proof.get("runtime_identity")
    inference = proof.get("inference")
    if not isinstance(identity, Mapping) or not isinstance(inference, Mapping):
        raise SovereignLocalModelBindingError("local_adapter_identity_or_inference_missing")
    if identity.get("protocol") != "stegverse.local-runtime.v1" or inference.get("protocol") != "stegverse.local-runtime.v1":
        raise SovereignLocalModelBindingError("local_adapter_protocol_mismatch")
    if identity.get("authority_attached") is not False or inference.get("authority_attached") is not False or inference.get("execution_authority") is not False:
        raise SovereignLocalModelBindingError("local_adapter_runtime_authority_escalation")
    model_id = str(identity.get("model_id", "")).strip()
    model_hash = str(identity.get("weights_sha256", "")).strip()
    proof_hash = str(proof.get("receipt_hash", "")).strip()
    if not model_id or not model_hash or not proof_hash:
        raise SovereignLocalModelBindingError("local_adapter_hash_evidence_missing")
    if inference.get("model_id") != model_id or inference.get("weights_sha256") != model_hash:
        raise SovereignLocalModelBindingError("local_adapter_model_identity_mismatch")
    return {
        "source_proof_schema": proof["schema_version"],
        "model_id": model_id,
        "model_hash": model_hash,
        "proof_hash": proof_hash,
        "production_llm_equivalent": False,
        "qualifies_as_large_production_llm": False,
        "authority_effect": "NONE",
        "source_proof": dict(proof),
    }


def validate_runtime_proof(proof: Mapping[str, Any]) -> dict[str, Any]:
    """Accept canonical micro-node proof or the released LLM-adapter conformance proof."""
    if proof.get("schema") == "stegverse.sovereign-local-model-proof/v1":
        return _validate_micro_node_proof(proof)
    if proof.get("schema_version") == "stegverse.local-runtime-model-proof.v1":
        return _validate_llm_adapter_proof(proof)
    raise SovereignLocalModelBindingError("unsupported_sovereign_local_model_proof")


def _measured_metrics(response: ProviderResponse) -> dict[str, ProviderMetric]:
    usage = response.metadata.get("usage")
    if not isinstance(usage, Mapping):
        raise SovereignLocalModelBindingError("provider_response_measured_usage_missing")
    metrics: dict[str, ProviderMetric] = {}
    for name in MEASURED_USAGE_KEYS:
        value = usage.get(name)
        if not isinstance(value, (int, float)):
            raise SovereignLocalModelBindingError(f"provider_response_usage_invalid:{name}")
        metrics[name] = ProviderMetric(
            value=str(Decimal(str(value))),
            unit="milliseconds" if name == "latency_ms" else "tokens",
            evidence_class="MEASURED",
            source_ref=f"provider_response:{response.response_hash}",
        )
    return metrics


def execute_verified_local_model(
    *,
    runtime_proof: Mapping[str, Any],
    endpoint: str,
    session_id: str,
    transition_id: str,
    measurement_id: str,
    messages: Sequence[Mapping[str, str] | ProviderMessage],
    origin_entry_point: str = "ecosystem_chat",
    interaction_type: str = "sovereign_local_model_inference",
    usage_submitter: Callable[[dict[str, Any]], dict[str, Any]] = submit_provider_usage_to_master_records,
) -> SovereignLocalModelExecution:
    proof = validate_runtime_proof(runtime_proof)
    model_id = str(proof.get("model_id", "")).strip()
    if not model_id:
        raise SovereignLocalModelBindingError("local_model_id_missing")
    normalized_messages = tuple(
        m if isinstance(m, ProviderMessage) else ProviderMessage(role=str(m.get("role", "user")), content=str(m.get("content", "")))
        for m in messages
    )
    request = ProviderRequest(
        provider="stegverse-local",
        model=model_id,
        messages=normalized_messages,
        metadata={
            "session_id": session_id,
            "transition_id": transition_id,
            "runtime_proof_hash": proof["proof_hash"],
            "runtime_model_hash": proof["model_hash"],
            "runtime_proof_schema": proof["source_proof_schema"],
            "production_llm_equivalent": bool(proof.get("production_llm_equivalent", False)),
        },
    )
    response = StegVerseLocalHTTPProviderClient(base_url=endpoint).complete(request)
    if response.metadata.get("sovereign_endpoint") is not True:
        raise SovereignLocalModelBindingError("provider_response_not_sovereign")
    if response.metadata.get("third_party_execution_platform_required") is not False:
        raise SovereignLocalModelBindingError("provider_response_third_party_dependency")
    if response.metadata.get("authority_effect", "NONE") != "NONE":
        raise SovereignLocalModelBindingError("provider_response_authority_escalation")
    if response.metadata.get("model_hash") != proof.get("model_hash"):
        raise SovereignLocalModelBindingError("runtime_model_hash_mismatch")

    usage_event = build_provider_usage_event(
        measurement_id=measurement_id,
        session_id=session_id,
        transition_id=transition_id,
        origin_entry_point=origin_entry_point,
        interaction_type=interaction_type,
        provider="stegverse-local",
        model=model_id,
        metrics=_measured_metrics(response),
        receipt_refs=[f"local-runtime-proof:{proof['proof_hash']}", f"provider-response:{response.response_hash}"],
    )
    mr_usage = usage_submitter(usage_event)
    production_scale = bool(proof.get("production_llm_equivalent", False)) and bool(proof.get("qualifies_as_large_production_llm", False))
    custody = mr_usage.get("custody_recorded") is True
    reconstructed = mr_usage.get("reconstructability") == "PASS"
    remaining = []
    if not custody:
        remaining.append("provider_usage_master_records_custody")
    if not reconstructed:
        remaining.append("provider_usage_master_records_reconstruction_pass")
    if not production_scale:
        remaining.append("production_scale_sovereign_llm")
    remaining.append("same_execution_transition_reconstruction_pass")
    binding_receipt = {
        "schema": "stegverse.llm_adapter.sovereign_local_model_binding/v1",
        "task_id": "LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019",
        "source_proof_schema": proof["source_proof_schema"],
        "session_id": session_id,
        "transition_id": transition_id,
        "measurement_id": measurement_id,
        "provider": "stegverse-local",
        "model_id": model_id,
        "model_hash": proof["model_hash"],
        "runtime_proof_hash": proof["proof_hash"],
        "request_hash": request.request_hash,
        "response_hash": response.response_hash,
        "provider_usage_event_sha256": usage_event["event_sha256"],
        "measured_usage": {name: usage_event["metrics"][name] for name in MEASURED_USAGE_KEYS},
        "provider_usage_custody_recorded": custody,
        "provider_usage_reconstruction_pass": reconstructed,
        "production_scale_llm_observed": production_scale,
        "reference_model_only": not production_scale,
        "activation_complete": False,
        "remaining_activation_predicates": remaining,
        "authority": {
            "provider_output_grants_authority": False,
            "usage_event_grants_authority": False,
            "binding_receipt_grants_authority": False,
        },
    }
    return SovereignLocalModelExecution(response, usage_event, mr_usage, binding_receipt)


__all__ = ["SovereignLocalModelBindingError", "SovereignLocalModelExecution", "execute_verified_local_model", "validate_runtime_proof"]
