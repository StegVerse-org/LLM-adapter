import json
from pathlib import Path
import socket

import pytest

from llm_adapter.local_model_runtime import launch_reference_runtime
from llm_adapter.sovereign_local_model_binding import (
    SovereignLocalModelBindingError,
    execute_verified_local_model,
    validate_runtime_proof,
)

ROOT = Path(__file__).resolve().parents[1]


def _micro_proof():
    return {
        "schema": "stegverse.sovereign-local-model-proof/v1",
        "goal_id": "SOVEREIGN-LOCAL-MODEL-001",
        "model_id": "stegverse-reference-lm-v1",
        "model_class": "reference_language_model",
        "production_llm_equivalent": False,
        "qualifies_as_large_production_llm": False,
        "model_hash": "model-hash-1",
        "proof_hash": "proof-hash-1",
        "state": "VERIFIED_REFERENCE_MODEL_RUNTIME",
        "authority_effect": "NONE",
        "predicates": {
            "real_model_process_observed": True,
            "private_endpoint_only": True,
            "real_inference_response_observed": True,
            "measured_usage_persistable": True,
            "local_training_observed": True,
            "third_party_inference_required": False,
            "model_output_grants_authority": False,
        },
        "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18, "latency_ms": 4.5},
    }


def _released_local_proof():
    return json.loads((ROOT / "receipts/local-runtime-model-proof.latest.json").read_text())


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_accepts_released_micro_node_proof_contract():
    proof = validate_runtime_proof(_micro_proof())
    assert proof["state"] == "VERIFIED_REFERENCE_MODEL_RUNTIME"
    assert proof["source_proof_schema"] == "stegverse.sovereign-local-model-proof/v1"


def test_accepts_released_llm_adapter_runtime_proof_contract():
    proof = validate_runtime_proof(_released_local_proof())
    assert proof["source_proof_schema"] == "stegverse.local-runtime-model-proof.v1"
    assert proof["model_id"] == "stegverse-local-reference-v1"
    assert proof["production_llm_equivalent"] is False


def test_rejects_static_or_unobserved_runtime_proof():
    proof = _micro_proof()
    proof["predicates"]["real_model_process_observed"] = False
    with pytest.raises(SovereignLocalModelBindingError, match="real_model_process_observed"):
        validate_runtime_proof(proof)


def test_executes_private_runtime_and_binds_exact_measured_usage(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "id": "chatcmpl-local-1",
                "model": "stegverse-reference-lm-v1",
                "choices": [{"message": {"role": "assistant", "content": "local model output"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 13, "completion_tokens": 9, "total_tokens": 22, "latency_ms": 6.25},
                "stegverse": {
                    "model_hash": "model-hash-1",
                    "training": {"external_training_service_required": False},
                    "third_party_inference_required": False,
                    "authority_effect": "NONE",
                },
            }

    monkeypatch.setattr("llm_adapter.http_provider_clients.requests.post", lambda *args, **kwargs: FakeResponse())
    captured = {}

    def submit_usage(event):
        captured["event"] = event
        return {
            "schema": "stegverse.usage.master_records_submission.v1",
            "status": "CUSTODY_RECORDED",
            "receipt_id": "mr-usage-1",
            "session_id": event["session_id"],
            "measurement_id": event["measurement_id"],
            "event_sha256": event["event_sha256"],
            "reconstructability": "PASS",
            "authority_granted": False,
            "custody_recorded": True,
        }

    result = execute_verified_local_model(
        runtime_proof=_micro_proof(),
        endpoint="http://127.0.0.1:11435/v1/chat/completions",
        session_id="session-1",
        transition_id="transition-1",
        measurement_id="measurement-1",
        messages=[{"role": "user", "content": "hello sovereign model"}],
        usage_submitter=submit_usage,
    )

    assert result.response.output == "local model output"
    assert result.response.metadata["model_hash"] == "model-hash-1"
    assert captured["event"]["metrics"]["prompt_tokens"]["value"] == "13"
    assert captured["event"]["metrics"]["completion_tokens"]["value"] == "9"
    assert captured["event"]["metrics"]["total_tokens"]["value"] == "22"
    assert captured["event"]["metrics"]["latency_ms"]["value"] == "6.25"
    assert all(metric["evidence_class"] == "MEASURED" for metric in captured["event"]["metrics"].values())
    assert result.binding_receipt["provider_usage_custody_recorded"] is True
    assert result.binding_receipt["provider_usage_reconstruction_pass"] is True
    assert result.binding_receipt["production_scale_llm_observed"] is False
    assert result.binding_receipt["reference_model_only"] is True
    assert result.binding_receipt["activation_complete"] is False
    assert "same_execution_transition_reconstruction_pass" in result.binding_receipt["remaining_activation_predicates"]
    assert all(value is False for value in result.binding_receipt["authority"].values())


def test_real_released_local_runtime_crosses_sovereign_provider_seam():
    runtime = launch_reference_runtime(_free_port())
    captured = {}

    def retain_without_false_custody(event):
        captured["event"] = event
        return {
            "schema": "stegverse.usage.master_records_submission.v1",
            "status": "NOT_CONFIGURED",
            "authority_granted": False,
            "custody_recorded": False,
        }

    try:
        result = execute_verified_local_model(
            runtime_proof=_released_local_proof(),
            endpoint=runtime.base_url + "/v1/chat/completions",
            session_id="hosted-real-local-session",
            transition_id="hosted-real-local-transition",
            measurement_id="hosted-real-local-measurement",
            messages=[{"role": "user", "content": "governed inference"}],
            usage_submitter=retain_without_false_custody,
        )
    finally:
        runtime.stop()

    assert result.response.output.strip()
    assert result.response.metadata["runtime_model"] == "stegverse-local-reference-v1"
    assert result.response.metadata["third_party_inference_required"] is False
    assert result.response.metadata["training"]["external_training_service_required"] is False
    assert captured["event"]["metrics"]["prompt_tokens"]["evidence_class"] == "MEASURED"
    assert int(captured["event"]["metrics"]["total_tokens"]["value"]) > 0
    assert DecimalLike(captured["event"]["metrics"]["latency_ms"]["value"]) >= 0
    assert result.binding_receipt["provider_usage_custody_recorded"] is False
    assert result.binding_receipt["provider_usage_reconstruction_pass"] is False
    assert result.binding_receipt["reference_model_only"] is True
    assert result.binding_receipt["activation_complete"] is False


def DecimalLike(value: str) -> float:
    return float(value)


def test_rejects_response_from_different_model_hash(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "id": "chatcmpl-local-2",
                "model": "stegverse-reference-lm-v1",
                "choices": [{"message": {"role": "assistant", "content": "output"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2, "latency_ms": 1},
                "stegverse": {"model_hash": "wrong-hash", "third_party_inference_required": False, "authority_effect": "NONE"},
            }

    monkeypatch.setattr("llm_adapter.http_provider_clients.requests.post", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(SovereignLocalModelBindingError, match="runtime_model_hash_mismatch"):
        execute_verified_local_model(
            runtime_proof=_micro_proof(),
            endpoint="http://127.0.0.1:11435/v1/chat/completions",
            session_id="session-1",
            transition_id="transition-1",
            measurement_id="measurement-1",
            messages=[{"role": "user", "content": "hello"}],
            usage_submitter=lambda event: {},
        )
