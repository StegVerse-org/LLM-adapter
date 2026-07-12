from hashlib import sha256
import json

import pytest

from llm_adapter.recursive_comparison import (
    RecursiveComparisonError,
    RecursiveTrace,
    emit_external_recursive_result,
)


def _hash(payload: dict) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _package() -> dict:
    package = {
        "schema_version": "1.1.0",
        "comparison_id": "cmp-test-001",
        "task_identity": "shared-task",
        "normalized_input": {"prompt": "test"},
        "output_requirements": {"format": "json"},
        "routes": [
            {"route_id": "governed", "route_kind": "STEGVERSE_GOVERNED"},
            {"route_id": "recursive", "route_kind": "EXTERNAL_RECURSIVE"},
        ],
        "metrics_requested": [],
        "claim_boundary": "test",
        "invariants": {},
    }
    package["package_sha256"] = _hash(package)
    return package


def _metrics() -> dict:
    names = [
        "total_cost_usd", "latency_ms", "model_calls", "input_tokens",
        "output_tokens", "tool_calls", "retries", "node_or_cell_activations",
        "receipt_count", "reconstructable",
    ]
    return {
        name: {"value": "1", "unit": "count", "evidence_class": "MEASURED", "source_ref": "trace"}
        for name in names
    }


def test_emits_external_recursive_result() -> None:
    result = emit_external_recursive_result(
        _package(), RecursiveTrace(output={"answer": "ok"}, metrics=_metrics())
    )
    assert result["route_result"]["route_id"] == "recursive"
    assert result["route_result"]["task_identity"] == "shared-task"
    assert result["invariants"]["adapter_observation_is_admissibility"] is False
    assert len(result["result_sha256"]) == 64


def test_rejects_package_hash_drift() -> None:
    package = _package()
    package["task_identity"] = "changed"
    with pytest.raises(RecursiveComparisonError, match="SHA-256 mismatch"):
        emit_external_recursive_result(
            package, RecursiveTrace(output={"answer": "ok"}, metrics=_metrics())
        )


def test_rejects_missing_telemetry() -> None:
    metrics = _metrics()
    metrics.pop("latency_ms")
    with pytest.raises(RecursiveComparisonError, match="missing required metrics"):
        emit_external_recursive_result(
            _package(), RecursiveTrace(output={"answer": "ok"}, metrics=metrics)
        )
