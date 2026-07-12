"""Provider-owned usage events compatible with the StegVerse usage ledger."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any, Dict, Mapping, Optional

SCHEMA_VERSION = "1.0.0"
EVIDENCE_CLASSES = {"MEASURED", "CONFIGURED", "DERIVED", "UNAVAILABLE"}


class ProviderUsageError(ValueError):
    """Raised when provider usage cannot be safely emitted."""


def _stable_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProviderMetric:
    value: Optional[str]
    unit: str
    evidence_class: str
    source_ref: Optional[str] = None

    def validate(self) -> None:
        if self.evidence_class not in EVIDENCE_CLASSES:
            raise ProviderUsageError(f"unsupported evidence class: {self.evidence_class}")
        if self.evidence_class == "UNAVAILABLE":
            if self.value is not None:
                raise ProviderUsageError("UNAVAILABLE metrics require null value")
            return
        if self.value is None or not self.unit:
            raise ProviderUsageError("available metrics require value and unit")
        try:
            Decimal(self.value)
        except (InvalidOperation, TypeError) as exc:
            raise ProviderUsageError("provider metric must be decimal-compatible") from exc


def build_provider_usage_event(
    *,
    measurement_id: str,
    session_id: str,
    transition_id: str,
    origin_entry_point: str,
    interaction_type: str,
    provider: str,
    model: str,
    metrics: Mapping[str, ProviderMetric],
    parent_transition_id: Optional[str] = None,
    receipt_refs: Optional[list[str]] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Emit one adapter-owned provider measurement without claiming authority."""
    for label, value in (
        ("measurement_id", measurement_id), ("session_id", session_id),
        ("transition_id", transition_id), ("origin_entry_point", origin_entry_point),
        ("interaction_type", interaction_type), ("provider", provider), ("model", model),
    ):
        if not value.strip():
            raise ProviderUsageError(f"{label} is required")
    if not metrics:
        raise ProviderUsageError("at least one provider metric is required")

    serialized: Dict[str, Dict[str, Any]] = {}
    for name, metric in metrics.items():
        if not name.strip():
            raise ProviderUsageError("metric names cannot be empty")
        metric.validate()
        serialized[name] = {
            "value": metric.value,
            "unit": metric.unit,
            "evidence_class": metric.evidence_class,
            "source_ref": metric.source_ref,
        }

    event: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_type": "TRANSITION_USAGE_RECORDED",
        "measurement_id": measurement_id,
        "session_id": session_id,
        "transition_id": transition_id,
        "parent_transition_id": parent_transition_id,
        "origin_entry_point": origin_entry_point,
        "entry_point": "llm_adapter",
        "entry_point_role": "machine_readable_translation_and_interoperability",
        "interaction_type": interaction_type,
        "metric_owner": "llm_adapter",
        "measurement_source": "provider_trace",
        "route_kind": "EXTERNAL_RECURSIVE",
        "provider": provider,
        "model": model,
        "metrics": serialized,
        "receipt_refs": list(receipt_refs or []),
        "timestamp": timestamp,
        "invariants": {
            "provider_output_is_authority": False,
            "usage_event_is_authority": False,
            "usage_event_is_admissibility": False,
            "session_identity_preserved": True,
            "transition_lineage_preserved": True,
        },
    }
    event["event_sha256"] = _stable_hash(event)
    return event
