"""Machine-readable LLM Adapter entry-point role declaration.

The declaration describes interaction responsibilities. It does not grant
execution authority, admissibility, standing, or publication authority.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, Mapping

SCHEMA_VERSION = "1.0.0"


class AdapterRoleError(ValueError):
    """Raised when the adapter role declaration violates required boundaries."""


def _stable_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


LLM_ADAPTER_ROLE: Dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "entry_point_id": "llm_adapter",
    "display_name": "StegVerse LLM Adapter",
    "primary_role": (
        "Machine-readable translation and interoperability boundary for LLMs, "
        "agents, tools, providers, and external frameworks."
    ),
    "related_roles": [
        "provider abstraction",
        "normalization layer",
        "compatibility bridge",
        "telemetry capture boundary",
        "receipt-ready result packager",
    ],
    "primary_audiences": [
        "LLM providers",
        "agent frameworks",
        "developers",
        "external systems",
    ],
    "interaction_types": [
        "provider_output_normalization",
        "agent_trace_conversion",
        "recursive_call_telemetry",
        "external_framework_intake",
        "machine_readable_governance_conversion",
        "provider_neutral_response_packaging",
        "governed_data_testing",
        "module_compatibility_testing",
    ],
    "accepted_inputs": [
        "prompts",
        "provider responses",
        "tool traces",
        "agent traces",
        "external framework packages",
        "SDK comparison packages",
    ],
    "produced_outputs": [
        "canonical intent",
        "transition packages",
        "telemetry envelopes",
        "machine-readable route results",
        "receipt-ready records",
    ],
    "authority_boundaries": {
        "acceptance_is_authority": False,
        "translation_is_admissibility": False,
        "provider_output_is_authority": False,
        "usage_event_is_authority": False,
        "usage_event_is_admissibility": False,
    },
    "usage_reporting": {
        "emits_usage_events": True,
        "metric_owner": "llm_adapter",
        "measurement_id_required": True,
        "owns": [
            "provider calls",
            "provider tokens",
            "provider latency",
            "provider tool calls",
            "provider retries",
        ],
    },
    "session_continuity": {
        "preserves_session_id": True,
        "preserves_transition_lineage": True,
        "preserves_origin_entry_point": True,
        "supports_return_to_origin": True,
    },
}


def validate_llm_adapter_role(role: Mapping[str, Any]) -> None:
    required = {
        "schema_version", "entry_point_id", "display_name", "primary_role",
        "related_roles", "primary_audiences", "interaction_types",
        "accepted_inputs", "produced_outputs", "authority_boundaries",
        "usage_reporting", "session_continuity",
    }
    missing = required - set(role)
    if missing:
        raise AdapterRoleError(f"missing adapter role fields: {sorted(missing)}")
    if role["schema_version"] != SCHEMA_VERSION or role["entry_point_id"] != "llm_adapter":
        raise AdapterRoleError("unsupported adapter role identity")
    boundaries = role["authority_boundaries"]
    if any(value is not False for value in boundaries.values()):
        raise AdapterRoleError("adapter role may not self-grant authority or admissibility")
    usage = role["usage_reporting"]
    if usage.get("metric_owner") != "llm_adapter" or usage.get("measurement_id_required") is not True:
        raise AdapterRoleError("adapter usage requires stable llm_adapter ownership")
    continuity = role["session_continuity"]
    for key in (
        "preserves_session_id", "preserves_transition_lineage",
        "preserves_origin_entry_point", "supports_return_to_origin",
    ):
        if continuity.get(key) is not True:
            raise AdapterRoleError(f"adapter continuity requirement failed: {key}")


def get_llm_adapter_role() -> Dict[str, Any]:
    role = deepcopy(LLM_ADAPTER_ROLE)
    validate_llm_adapter_role(role)
    role["role_sha256"] = _stable_hash(role)
    return role
