#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_adapter.sovereign_local_model_binding import (
    SovereignLocalModelBindingError,
    execute_verified_local_model,
)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def validate_tvc_route(route: dict, proof: dict) -> tuple[str, str]:
    if route.get("state") != "ROUTE_ADMITTED":
        raise SovereignLocalModelBindingError("tvc_route_not_admitted")
    if route.get("route_authority") != "StegVerse-Labs/TVC":
        raise SovereignLocalModelBindingError("tvc_route_authority_mismatch")
    endpoint = str(route.get("endpoint") or "").strip().rstrip("/")
    if not endpoint:
        raise SovereignLocalModelBindingError("tvc_route_endpoint_missing")
    if route.get("runtime_proof_hash") != stable_hash(proof):
        raise SovereignLocalModelBindingError("tvc_route_runtime_proof_hash_mismatch")
    if route.get("canonical_micro_node_proof_consumed") is not True:
        raise SovereignLocalModelBindingError("tvc_route_noncanonical_proof")
    if route.get("credential_requirement") != "NONE":
        raise SovereignLocalModelBindingError("tvc_route_credential_requirement_not_none")
    if route.get("github_token_required") is not False:
        raise SovereignLocalModelBindingError("tvc_route_github_token_dependency")
    if route.get("third_party_execution_platform_required") is not False:
        raise SovereignLocalModelBindingError("tvc_route_third_party_platform_dependency")
    if route.get("execution_authority") is not False or route.get("authority_effect") != "NONE":
        raise SovereignLocalModelBindingError("tvc_route_authority_escalation")
    return endpoint, endpoint + "/v1/chat/completions"


def execute(
    *,
    proof: dict,
    route: dict,
    session_id: str,
    transition_id: str,
    measurement_id: str,
    prompt: str,
) -> dict:
    route_base, transport_endpoint = validate_tvc_route(route, proof)
    execution = execute_verified_local_model(
        runtime_proof=proof,
        endpoint=transport_endpoint,
        session_id=session_id,
        transition_id=transition_id,
        measurement_id=measurement_id,
        messages=[{"role": "user", "content": prompt}],
    )
    output = execution.response.output
    result = {
        "schema": "stegverse.llm_adapter.canonical_sovereign_route_execution/v1",
        "task_id": "LLMA-SOVEREIGN-CARRIER-EXECUTION-020",
        "state": "EXECUTED" if output.strip() else "FAILED",
        "session_id": session_id,
        "transition_id": transition_id,
        "measurement_id": measurement_id,
        "route_authority": "StegVerse-Labs/TVC",
        "route_receipt_hash": route.get("receipt_hash"),
        "runtime_proof_hash": stable_hash(proof),
        "route_base_endpoint": route_base,
        "transport_endpoint": transport_endpoint,
        "model_id": execution.binding_receipt["model_id"],
        "model_hash": execution.binding_receipt["model_hash"],
        "request_hash": execution.binding_receipt["request_hash"],
        "response_hash": execution.binding_receipt["response_hash"],
        "response_text_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "measured_usage": execution.binding_receipt["measured_usage"],
        "provider_usage_event": execution.usage_event,
        "master_records_usage": execution.master_records_usage,
        "binding_receipt": execution.binding_receipt,
        "provider_usage_custody_recorded": execution.binding_receipt["provider_usage_custody_recorded"],
        "provider_usage_reconstruction_pass": execution.binding_receipt["provider_usage_reconstruction_pass"],
        "reference_model_only": execution.binding_receipt["reference_model_only"],
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "execution_authority": False,
        "authority_effect": "NONE",
        "next_transition": "MASTER_RECORDS_SAME_EXECUTION_TRANSITION_RECONSTRUCTION",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the exact TVC-admitted canonical sovereign local-model route.")
    parser.add_argument("--proof", required=True, type=Path)
    parser.add_argument("--route", required=True, type=Path)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--transition-id", required=True)
    parser.add_argument("--measurement-id", required=True)
    parser.add_argument("--prompt", default="Execute one governed sovereign Ecosystem Chat inference and preserve measured usage.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        proof = json.loads(args.proof.read_text(encoding="utf-8"))
        route = json.loads(args.route.read_text(encoding="utf-8"))
        if not isinstance(proof, dict) or not isinstance(route, dict):
            raise SovereignLocalModelBindingError("proof_or_route_not_object")
        result = execute(
            proof=proof,
            route=route,
            session_id=args.session_id,
            transition_id=args.transition_id,
            measurement_id=args.measurement_id,
            prompt=args.prompt,
        )
    except Exception as exc:
        result = {
            "schema": "stegverse.llm_adapter.canonical_sovereign_route_execution/v1",
            "task_id": "LLMA-SOVEREIGN-CARRIER-EXECUTION-020",
            "state": "FAILED",
            "reason": str(exc),
            "credential_requirement": "NONE",
            "github_token_required": False,
            "third_party_execution_platform_required": False,
            "execution_authority": False,
            "authority_effect": "NONE",
        }

    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if result.get("state") == "EXECUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
