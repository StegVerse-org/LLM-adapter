#!/usr/bin/env python3
"""Materialize one exact ProviderRequest from resident-local admitted KV memory.

This is a source/application bridge only. It never reads provider credentials,
decides Interlock/InTr admission, calls a model provider, or writes KnowledgeVault.
The memory packet must already carry an exact externally-produced ALLOW receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from llm_adapter.kv_memory_context_bridge import build_provider_request_with_kv_memory
from llm_adapter.provider_request import ProviderRequest

SCHEMA = "stegverse.llm-adapter.kv-memory-provider-request-materialization/v1"
FORBIDDEN_KEYS = {
    "api_key", "apikey", "token", "access_token", "refresh_token", "password",
    "secret", "private_key", "seed", "mnemonic", "credential", "authorization",
}


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def reject_secret_keys(value: Any, *, path: str = "$" ) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_KEYS or normalized.endswith("_api_key") or normalized.endswith("_token") or normalized.endswith("_password"):
                raise ValueError(f"credential-like field forbidden in resident request material: {path}.{key}")
            reject_secret_keys(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            reject_secret_keys(item, path=f"{path}[{idx}]")


def materialize(packet: dict[str, Any], admission: dict[str, Any], request_input: dict[str, Any]) -> dict[str, Any]:
    reject_secret_keys(request_input)
    provider = request_input.get("provider")
    model = request_input.get("model")
    messages = request_input.get("messages")
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError("provider required")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model required")
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages required")
    for item in messages:
        if not isinstance(item, dict) or not isinstance(item.get("role"), str) or not isinstance(item.get("content"), str):
            raise ValueError("each message requires string role/content")

    created_at = request_input.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        raise ValueError("created_at required for exact replay")

    built = build_provider_request_with_kv_memory(
        provider=provider,
        model=model,
        messages=messages,
        memory_packet=packet,
        memory_packet_admission=admission,
        purpose=str(request_input.get("purpose") or "answer"),
        allowed_sources=tuple(request_input.get("allowed_sources") or ("model_knowledge",)),
        temperature=float(request_input.get("temperature", 0.0)),
        metadata=request_input.get("metadata") if isinstance(request_input.get("metadata"), dict) else {},
    )
    exact_request = ProviderRequest(
        provider=built.provider,
        model=built.model,
        messages=built.messages,
        purpose=built.purpose,
        allowed_sources=built.allowed_sources,
        temperature=built.temperature,
        metadata=built.metadata,
        created_at=created_at,
        schema_version=built.schema_version,
    )
    return {
        "schema": SCHEMA,
        "state": "PROVIDER_REQUEST_MATERIALIZED",
        "provider_request": exact_request.to_dict(),
        "provider_request_hash": exact_request.request_hash,
        "memory_packet_id": packet.get("packet_id"),
        "memory_packet_sha256": built.metadata["kv_memory_context"]["packet_sha256"],
        "memory_packet_intr_receipt_hash": built.metadata["kv_memory_context"]["intr_receipt_hash"],
        "provider_ingress_admission_observed": False,
        "provider_execution_observed": False,
        "provider_egress_admission_observed": False,
        "kv_writeback_observed": False,
        "credential_material_present": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_MATERIALIZATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize exact KV-memory ProviderRequest")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--request-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = materialize(load_object(args.packet), load_object(args.admission), load_object(args.request_input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
