"""External recursive-route telemetry for governed-vs-recursive comparisons.

This module emits the external route half of the StegVerse SDK comparison
contract. Fixture-backed execution is supported now; live provider execution
remains an explicit downstream integration and must identify measured values.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any, Dict, Mapping

SCHEMA_VERSION = "1.0.0"
REQUIRED_METRICS = (
    "total_cost_usd",
    "latency_ms",
    "model_calls",
    "input_tokens",
    "output_tokens",
    "tool_calls",
    "retries",
    "node_or_cell_activations",
    "receipt_count",
    "reconstructable",
)


class RecursiveComparisonError(ValueError):
    """Raised when comparison identity or telemetry violates the contract."""


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Mapping[str, Any]) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RecursiveTrace:
    output: Mapping[str, Any]
    metrics: Mapping[str, Mapping[str, Any]]
    admissibility_result: str = "NOT_EVALUATED_BY_EXTERNAL_ROUTE"

    def validate(self) -> None:
        missing = set(REQUIRED_METRICS) - set(self.metrics)
        if missing:
            raise RecursiveComparisonError(f"missing required metrics: {sorted(missing)}")
        for name in REQUIRED_METRICS:
            metric = self.metrics[name]
            evidence = metric.get("evidence_class")
            value = metric.get("value")
            unit = metric.get("unit")
            if evidence not in {"MEASURED", "CONFIGURED", "DERIVED", "UNAVAILABLE"}:
                raise RecursiveComparisonError(f"invalid evidence class for {name}: {evidence}")
            if evidence == "UNAVAILABLE":
                if value is not None:
                    raise RecursiveComparisonError(f"UNAVAILABLE metric {name} must use null value")
                continue
            if value is None or not isinstance(unit, str):
                raise RecursiveComparisonError(f"metric {name} requires value and unit")
            try:
                Decimal(str(value))
            except (InvalidOperation, TypeError) as exc:
                raise RecursiveComparisonError(f"metric {name} must be decimal-compatible") from exc


def emit_external_recursive_result(
    comparison_package: Mapping[str, Any],
    trace: RecursiveTrace,
) -> Dict[str, Any]:
    """Return the EXTERNAL_RECURSIVE route result for one comparison package."""
    expected_sha = comparison_package.get("package_sha256")
    unsigned = dict(comparison_package)
    unsigned.pop("package_sha256", None)
    if not expected_sha or _hash(unsigned) != expected_sha:
        raise RecursiveComparisonError("comparison package SHA-256 mismatch")

    routes = comparison_package.get("routes", [])
    external = [route for route in routes if route.get("route_kind") == "EXTERNAL_RECURSIVE"]
    if len(external) != 1:
        raise RecursiveComparisonError("exactly one EXTERNAL_RECURSIVE route is required")

    trace.validate()
    output = dict(trace.output)
    result = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": comparison_package.get("comparison_id"),
        "route_result": {
            "route_id": external[0].get("route_id"),
            "task_identity": comparison_package.get("task_identity"),
            "output_sha256": _hash(output),
            "metrics": dict(trace.metrics),
            "admissibility_result": trace.admissibility_result,
            "receipt_refs": [],
            "warnings": [
                "external provider output is not authority",
                "fixture telemetry is not live-provider measurement",
            ],
        },
        "invariants": {
            "provider_output_is_authority": False,
            "adapter_observation_is_admissibility": False,
            "returned_to_sdk": True,
        },
    }
    result["result_sha256"] = _hash(result)
    return result
