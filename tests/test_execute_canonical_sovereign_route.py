from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "execute_canonical_sovereign_route",
    ROOT / "scripts" / "execute_canonical_sovereign_route.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def proof() -> dict:
    return {
        "schema": "stegverse.sovereign-local-model-proof/v1",
        "goal_id": "SOVEREIGN-LOCAL-MODEL-001",
        "state": "VERIFIED_REFERENCE_MODEL_RUNTIME",
        "model_id": "stegverse-reference-lm-v1",
        "model_hash": "model-hash",
        "proof_hash": "proof-hash",
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
        "usage": {"prompt_tokens": 4, "completion_tokens": 5, "total_tokens": 9, "latency_ms": 1.5},
    }


def route(runtime_proof: dict) -> dict:
    return {
        "state": "ROUTE_ADMITTED",
        "route_authority": "StegVerse-Labs/TVC",
        "endpoint": "http://127.0.0.1:31415",
        "runtime_proof_hash": mod.stable_hash(runtime_proof),
        "canonical_micro_node_proof_consumed": True,
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "execution_authority": False,
        "authority_effect": "NONE",
        "receipt_hash": "route-hash",
    }


class CanonicalSovereignRouteExecutionTests(unittest.TestCase):
    def test_route_validation_rejects_any_github_token_dependency(self) -> None:
        runtime_proof = proof()
        value = route(runtime_proof)
        value["github_token_required"] = True
        with self.assertRaisesRegex(Exception, "tvc_route_github_token_dependency"):
            mod.validate_tvc_route(value, runtime_proof)

    def test_route_validation_binds_exact_proof_hash_and_private_base(self) -> None:
        runtime_proof = proof()
        base, transport = mod.validate_tvc_route(route(runtime_proof), runtime_proof)
        self.assertEqual(base, "http://127.0.0.1:31415")
        self.assertEqual(transport, "http://127.0.0.1:31415/v1/chat/completions")

    def test_executor_consumes_tvc_endpoint_through_canonical_binding(self) -> None:
        runtime_proof = proof()
        route_receipt = route(runtime_proof)
        fake_execution = SimpleNamespace(
            response=SimpleNamespace(output="governed local response"),
            usage_event={"event_sha256": "usage-event", "metrics": {}},
            master_records_usage={"status": "NOT_CONFIGURED", "custody_recorded": False},
            binding_receipt={
                "model_id": "stegverse-reference-lm-v1",
                "model_hash": "model-hash",
                "request_hash": "request-hash",
                "response_hash": "response-hash",
                "measured_usage": {"prompt_tokens": {}, "completion_tokens": {}, "total_tokens": {}, "latency_ms": {}},
                "provider_usage_custody_recorded": False,
                "provider_usage_reconstruction_pass": False,
                "reference_model_only": True,
            },
        )
        with mock.patch.object(mod, "execute_verified_local_model", return_value=fake_execution) as execute:
            result = mod.execute(
                proof=runtime_proof,
                route=route_receipt,
                session_id="session-1",
                transition_id="transition-1",
                measurement_id="measurement-1",
                prompt="governed inference",
            )
        self.assertEqual(result["state"], "EXECUTED")
        self.assertEqual(result["transport_endpoint"], "http://127.0.0.1:31415/v1/chat/completions")
        self.assertEqual(result["credential_requirement"], "NONE")
        self.assertFalse(result["github_token_required"])
        self.assertFalse(result["execution_authority"])
        self.assertEqual(result["next_transition"], "MASTER_RECORDS_SAME_EXECUTION_TRANSITION_RECONSTRUCTION")
        self.assertEqual(execute.call_args.kwargs["endpoint"], "http://127.0.0.1:31415/v1/chat/completions")


if __name__ == "__main__":
    unittest.main()
