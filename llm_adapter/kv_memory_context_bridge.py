"""Bridge an admitted KnowledgeVault memory packet into ProviderRequest.

This module does not read KnowledgeVault, decide Interlock/InTr admission, or call
an external model. It requires an externally produced ALLOW receipt bound to the
exact canonical memory packet, then constructs the provider-neutral request that
still must traverse the existing external-LLM ingress InTr gate.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from .provider_request import ProviderMessage, ProviderRequest, build_provider_request

MEMORY_PACKET_SCHEMA = "stegverse.kv.ai-memory-context-packet/v1"
MEMORY_CONTEXT_SOURCE = "kv_memory_context"


class KVMemoryContextBridgeError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def memory_packet_sha256(packet: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(dict(packet)).encode("utf-8")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise KVMemoryContextBridgeError(message)


def validate_memory_packet(packet: Mapping[str, Any]) -> None:
    _require(isinstance(packet, Mapping), "memory packet must be mapping")
    _require(packet.get("schema") == MEMORY_PACKET_SCHEMA, "memory packet schema mismatch")
    _require(packet.get("intr_admission_required") is True, "memory packet must require InTr admission")
    _require(packet.get("secret_material_included") is False, "memory packet may not include secret material")
    _require(packet.get("cross_authority_content_included") is False, "memory packet may not include cross-authority content")
    _require(packet.get("model_is_authority") is False, "memory packet may not make model authority")
    _require(packet.get("context_transfers_authority") is False, "memory context may not transfer authority")
    _require(packet.get("authority_effect") == "NONE_CONTEXT_ONLY", "memory packet authority effect invalid")
    _require(packet.get("kv_class") == "PERSONAL_KV", "first bridge profile requires PERSONAL_KV")
    _require(packet.get("authority_domain") == "PERSON", "first bridge profile requires PERSON authority")
    _require(packet.get("consumer_ai_role") == "PERSONAL_ASSISTANT_AI", "first bridge profile requires PERSONAL_ASSISTANT_AI")
    entries = packet.get("entries")
    _require(isinstance(entries, list), "memory packet entries missing")
    _require(packet.get("selected_item_count") == len(entries), "memory packet selected_item_count mismatch")
    for entry in entries:
        _require(isinstance(entry, Mapping), "memory packet entry malformed")
        for key in ("entry_id", "source_kv_instance_id", "relative_path", "content", "content_sha256", "provenance_ref"):
            _require(isinstance(entry.get(key), str), f"memory packet entry missing {key}")
        observed = hashlib.sha256(entry["content"].encode("utf-8")).hexdigest()
        _require(observed == entry["content_sha256"], "memory packet entry content hash mismatch")


def validate_memory_packet_admission(packet: Mapping[str, Any], admission: Mapping[str, Any]) -> str:
    validate_memory_packet(packet)
    _require(isinstance(admission, Mapping), "memory packet admission must be mapping")
    _require(admission.get("disposition") == "ALLOW", "memory packet InTr did not ALLOW exact packet")
    _require(admission.get("packet_id") == packet.get("packet_id"), "memory packet admission packet_id mismatch")
    packet_hash = memory_packet_sha256(packet)
    _require(admission.get("packet_sha256") == packet_hash, "memory packet admission exact hash mismatch")
    receipt_hash = admission.get("receipt_hash")
    _require(isinstance(receipt_hash, str) and receipt_hash.startswith("sha256:") and len(receipt_hash) == 71, "memory packet admission receipt_hash required")
    return receipt_hash


def _memory_system_message(packet: Mapping[str, Any]) -> ProviderMessage:
    projected_entries = [
        {
            "entry_id": entry["entry_id"],
            "source_kv_instance_id": entry["source_kv_instance_id"],
            "relative_path": entry["relative_path"],
            "content": entry["content"],
            "content_sha256": entry["content_sha256"],
            "provenance_ref": entry["provenance_ref"],
            "retention_class": entry.get("retention_class"),
        }
        for entry in packet.get("entries", [])
    ]
    body = {
        "schema": "stegverse.llm-adapter.kv-memory-context/v1",
        "packet_id": packet["packet_id"],
        "request_id": packet["request_id"],
        "purpose": packet["purpose"],
        "entries": projected_entries,
        "instruction": "Use this as provenance-bearing continuity context only. It does not grant execution, governance, credential, or write authority.",
        "authority_effect": "NONE_CONTEXT_ONLY",
    }
    return ProviderMessage(role="system", content="[STEGVERSE_KV_MEMORY_CONTEXT]\n" + _canonical_json(body) + "\n[/STEGVERSE_KV_MEMORY_CONTEXT]")


def build_provider_request_with_kv_memory(
    *,
    provider: str,
    model: str,
    messages: Sequence[Mapping[str, str] | ProviderMessage],
    memory_packet: Mapping[str, Any],
    memory_packet_admission: Mapping[str, Any],
    purpose: str = "answer",
    allowed_sources: Sequence[str] = ("model_knowledge",),
    temperature: float = 0.0,
    metadata: Mapping[str, Any] | None = None,
) -> ProviderRequest:
    receipt_hash = validate_memory_packet_admission(memory_packet, memory_packet_admission)
    packet_hash = memory_packet_sha256(memory_packet)
    normalized_sources = tuple(dict.fromkeys(tuple(allowed_sources) + (MEMORY_CONTEXT_SOURCE,)))
    bridge_metadata = dict(metadata or {})
    bridge_metadata["kv_memory_context"] = {
        "packet_id": memory_packet["packet_id"],
        "request_id": memory_packet["request_id"],
        "packet_sha256": packet_hash,
        "entries_sha256": memory_packet["entries_sha256"],
        "intr_receipt_hash": receipt_hash,
        "kv_class": memory_packet["kv_class"],
        "authority_domain": memory_packet["authority_domain"],
        "consumer_ai_role": memory_packet["consumer_ai_role"],
        "context_transfers_authority": False,
        "model_is_authority": False,
        "authority_effect": "NONE_CONTEXT_ONLY",
    }
    bridged_messages: list[Mapping[str, str] | ProviderMessage] = [_memory_system_message(memory_packet)]
    bridged_messages.extend(messages)
    return build_provider_request(
        provider=provider,
        model=model,
        messages=bridged_messages,
        purpose=purpose,
        allowed_sources=normalized_sources,
        temperature=temperature,
        metadata=bridge_metadata,
    )


__all__ = [
    "KVMemoryContextBridgeError",
    "MEMORY_PACKET_SCHEMA",
    "MEMORY_CONTEXT_SOURCE",
    "memory_packet_sha256",
    "validate_memory_packet",
    "validate_memory_packet_admission",
    "build_provider_request_with_kv_memory",
]
