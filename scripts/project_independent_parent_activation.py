#!/usr/bin/env python3
"""Project a terminal independent-parent activation into LLM-adapter evidence.

This is a non-authorizing local projection step. It consumes the canonical terminal
receipts emitted by StegVerse-Labs/.github after same-execution reconstruction and
writes an immutable LLM-adapter-owned sovereign activation evidence record. It does
not execute inference, route authority, custody, GitHub mutation, or Site activation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "receipts" / "ecosystem-chat-sovereign-activation.verified.json"
REL = Path("receipts/ecosystem-chat-sovereign-inference")
ACTIVATION = REL / "independent_parent_activation.latest.json"
BASE = REL / "SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json"
ROUTE = REL / "tvc_local_model_route.json"
EXECUTION = REL / "llm_adapter_sovereign_execution.json"
RECONSTRUCTION = REL / "master_records_same_execution_reconstruction.json"

REQUIRED_TRUE = (
    "real_model_process_observed",
    "private_endpoint_only",
    "ephemeral_e1_e2_execution_observed",
    "measured_usage_persisted",
    "provider_usage_reconstruction_pass",
    "transition_reconstruction_pass",
    "same_execution",
    "persistent_conversational_runtime_ready",
)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def verify_chain(control_root: Path) -> dict[str, Any]:
    activation = load(control_root / ACTIVATION)
    base = load(control_root / BASE)
    route = load(control_root / ROUTE)
    execution = load(control_root / EXECUTION)
    reconstruction = load(control_root / RECONSTRUCTION)

    errors: list[str] = []
    if activation.get("schema") != "stegverse.ecosystem-chat-independent-parent-activation/v1":
        errors.append("activation_schema")
    if activation.get("state") != "PASS":
        errors.append("activation_state")
    if activation.get("task_id") != "SHWP-ECOSYSTEM-CHAT-INFERENCE-001":
        errors.append("activation_task")
    if not isinstance(activation.get("fencing_token"), int) or activation["fencing_token"] <= 22:
        errors.append("fresh_parent_fence_gt22")
    if any(activation.get(key) is not True for key in REQUIRED_TRUE):
        errors.append("terminal_predicates")
    if activation.get("credential_authority") != "TV/TVC":
        errors.append("credential_authority")
    if activation.get("credential_requirement") != "NONE":
        errors.append("credential_requirement")
    if activation.get("github_token_required") is not False:
        errors.append("github_token_required")
    if activation.get("github_actions_activation_role") is not False:
        errors.append("github_actions_activation_role")
    if activation.get("third_party_inference_required") is not False:
        errors.append("third_party_inference_required")
    if activation.get("authority_effect") != "NONE_BEYOND_ADMITTED_PARENT_TASK_CONTROL":
        errors.append("authority_effect")

    binding = dict(activation)
    expected_activation_hash = binding.pop("activation_receipt_hash", None)
    if not isinstance(expected_activation_hash, str) or stable_hash(binding) != expected_activation_hash:
        errors.append("activation_hash")

    if base.get("completed") is not True or base.get("same_execution") is not True:
        errors.append("base_terminal_state")
    if base.get("github_token_required") is not False or base.get("third_party_inference_required") is not False:
        errors.append("base_authority_boundary")

    if route.get("receipt_hash") != activation.get("tvc_route_receipt_hash"):
        errors.append("route_hash_binding")
    usage = execution.get("provider_usage_event")
    usage = usage if isinstance(usage, dict) else {}
    if usage.get("event_sha256") != activation.get("provider_usage_event_sha256"):
        errors.append("provider_usage_binding")
    if execution.get("state") != "EXECUTED":
        errors.append("execution_state")
    if reconstruction.get("reconstruction_receipt_hash") != activation.get("reconstruction_receipt_hash"):
        errors.append("reconstruction_hash_binding")
    if reconstruction.get("provider_usage_reconstruction_pass") is not True:
        errors.append("provider_usage_reconstruction")
    if reconstruction.get("transition_reconstruction_pass") is not True:
        errors.append("transition_reconstruction")
    if reconstruction.get("same_execution") is not True:
        errors.append("reconstruction_same_execution")

    if errors:
        raise ValueError("terminal parent chain rejected: " + ",".join(sorted(set(errors))))

    return {
        "activation": activation,
        "base": base,
        "route": route,
        "execution": execution,
        "reconstruction": reconstruction,
    }


def build_projection(chain: dict[str, Any]) -> dict[str, Any]:
    activation = chain["activation"]
    execution = chain["execution"]
    reconstruction = chain["reconstruction"]
    usage = execution.get("provider_usage_event") or {}
    projection: dict[str, Any] = {
        "schema": "stegverse.ecosystem_chat.sovereign_activation_projection.v1",
        "state": "VERIFIED",
        "source_task_id": activation["task_id"],
        "source_activation_receipt_hash": activation["activation_receipt_hash"],
        "fencing_token": activation["fencing_token"],
        "heartbeat_reference_epoch": activation.get("heartbeat_reference_epoch"),
        "heartbeat_reference_is_causal": False,
        "predicates": {key: True for key in REQUIRED_TRUE},
        "bindings": {
            "runtime_proof_hash": activation.get("runtime_proof_hash"),
            "tvc_route_receipt_hash": activation.get("tvc_route_receipt_hash"),
            "provider_usage_event_sha256": usage.get("event_sha256"),
            "reconstruction_receipt_hash": reconstruction.get("reconstruction_receipt_hash"),
        },
        "provider_usage": {
            "measured": isinstance(execution.get("measured_usage"), dict),
            "event_sha256": usage.get("event_sha256"),
            "custody_recorded": reconstruction.get("provider_usage_reconstruction_pass") is True,
            "reconstructability": "PASS",
            "authority_granted": False,
        },
        "transition": {
            "custody_recorded": True,
            "reconstructability": "PASS",
            "same_execution": True,
        },
        "runtime": {
            "private_endpoint_only": True,
            "persistent_conversational_runtime_ready": True,
            "third_party_inference_required": False,
        },
        "credential_boundary": {
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "github_token_required": False,
            "github_actions_activation_role": False,
        },
        "authority_boundary": {
            "projection_grants_activation_authority": False,
            "projection_grants_execution_authority": False,
            "projection_grants_custody_authority": False,
            "projection_grants_release_authority": False,
            "projection_grants_publication_authority": False,
        },
    }
    projection["projection_sha256"] = stable_hash(projection)
    return projection


def immutable_write(path: Path, value: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists():
        existing = load(path)
        if existing != value:
            raise ValueError("immutable sovereign activation projection already exists with different content")
        return "UNCHANGED"
    path.write_text(encoded, encoding="utf-8")
    return "CREATED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--control-root",
        default=os.getenv("STEGVERSE_ORG_CONTROL_ROOT", ""),
        help="Nonsecret local path to the materialized StegVerse-Labs/.github control repository.",
    )
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()
    if not args.control_root:
        raise SystemExit("STEGVERSE_ORG_CONTROL_ROOT_OR_CONTROL_ROOT_REQUIRED")
    control_root = Path(args.control_root).expanduser().resolve()
    chain = verify_chain(control_root)
    projection = build_projection(chain)
    result = immutable_write(Path(args.output).expanduser().resolve(), projection)
    print(json.dumps({
        "state": "VERIFIED",
        "write_result": result,
        "source_activation_receipt_hash": projection["source_activation_receipt_hash"],
        "projection_sha256": projection["projection_sha256"],
        "authority_effect": "NONE",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
