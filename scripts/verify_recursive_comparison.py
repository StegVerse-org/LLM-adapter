#!/usr/bin/env python3
"""Verify the fixture-bound external recursive comparison producer."""
from __future__ import annotations

import json
from pathlib import Path

from llm_adapter.recursive_comparison import RecursiveTrace, emit_external_recursive_result

ROOT = Path(__file__).resolve().parents[1]


def canonical_hash(payload: dict) -> str:
    from hashlib import sha256
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def main() -> int:
    package = {
        "schema_version": "1.1.0",
        "comparison_id": "cmp-fixture-001",
        "task_identity": "transition-admissibility-assessment",
        "normalized_input": {"prompt": "Assess whether this transition may execute."},
        "output_requirements": {"format": "json", "decision_required": True},
        "routes": [
            {"route_id": "stegverse-governed", "route_kind": "STEGVERSE_GOVERNED"},
            {"route_id": "external-recursive", "route_kind": "EXTERNAL_RECURSIVE"}
        ],
        "metrics_requested": [
            "total_cost_usd", "latency_ms", "model_calls", "input_tokens",
            "output_tokens", "tool_calls", "retries", "node_or_cell_activations",
            "receipt_count", "reconstructable"
        ],
        "claim_boundary": "fixture verification",
        "invariants": {
            "sdk_preparation_is_execution": False,
            "sdk_preparation_is_authority": False,
            "route_outputs_must_share_task_identity": True,
            "configured_values_must_not_be_reported_as_measured": True
        }
    }
    package["package_sha256"] = canonical_hash(package)
    fixture = json.loads((ROOT / "examples/llm_route_comparison/external_recursive_fixture.json").read_text())
    result = emit_external_recursive_result(
        package,
        RecursiveTrace(
            output=fixture["output"],
            metrics=fixture["metrics"],
            admissibility_result=fixture["admissibility_result"],
        ),
    )
    assert result["comparison_id"] == package["comparison_id"]
    assert result["route_result"]["route_id"] == "external-recursive"
    assert result["invariants"]["provider_output_is_authority"] is False
    assert len(result["result_sha256"]) == 64
    print("External recursive comparison fixture verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
