#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_adapter.local_model_runtime import launch_reference_runtime
from llm_adapter.sovereign_local_model_binding import execute_verified_local_model


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def prove() -> dict:
    source_proof = json.loads((ROOT / "receipts/local-runtime-model-proof.latest.json").read_text())
    runtime = launch_reference_runtime(_free_port())
    try:
        execution = execute_verified_local_model(
            runtime_proof=source_proof,
            endpoint=runtime.base_url + "/v1/chat/completions",
            session_id="llma-sovereign-local-binding-proof",
            transition_id="llma-sovereign-local-binding-transition",
            measurement_id="llma-sovereign-local-binding-measurement",
            messages=[{"role": "user", "content": "governed inference"}],
            usage_submitter=lambda event: {
                "schema": "stegverse.usage.master_records_submission.v1",
                "status": "NOT_CONFIGURED",
                "authority_granted": False,
                "custody_recorded": False,
            },
        )
    finally:
        runtime.stop()

    metrics = execution.usage_event["metrics"]
    passed = (
        bool(execution.response.output.strip())
        and execution.response.metadata.get("sovereign_endpoint") is True
        and execution.response.metadata.get("third_party_execution_platform_required") is False
        and execution.response.metadata.get("authority_effect") == "NONE"
        and all(metrics[name]["evidence_class"] == "MEASURED" for name in ("prompt_tokens", "completion_tokens", "total_tokens", "latency_ms"))
        and execution.binding_receipt["provider_usage_custody_recorded"] is False
        and execution.binding_receipt["provider_usage_reconstruction_pass"] is False
        and execution.binding_receipt["reference_model_only"] is True
        and execution.binding_receipt["activation_complete"] is False
    )
    return {
        "schema": "stegverse.llm_adapter.sovereign_local_model_binding_proof/v1",
        "task_id": "LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019",
        "state": "PASS" if passed else "FAIL",
        "source_runtime_proof_receipt_hash": source_proof["receipt_hash"],
        "source_runtime_protocol": source_proof["runtime_identity"]["protocol"],
        "source_runtime_model_id": source_proof["runtime_identity"]["model_id"],
        "source_runtime_model_hash": source_proof["runtime_identity"]["weights_sha256"],
        "real_local_process_executed": True,
        "private_provider_seam_executed": execution.response.metadata.get("sovereign_endpoint") is True,
        "third_party_execution_platform_required": execution.response.metadata.get("third_party_execution_platform_required"),
        "provider_response_hash": execution.response.response_hash,
        "provider_usage_event": execution.usage_event,
        "master_records_usage_submission": execution.master_records_usage,
        "binding_receipt": execution.binding_receipt,
        "authority_effect": "NONE",
        "product_activation_granted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = prove()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded, end="")
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
