from __future__ import annotations

import copy
import hashlib
import json

import pytest

from llm_adapter.kv_memory_context_bridge import (
    KVMemoryContextBridgeError,
    build_provider_request_with_kv_memory,
    memory_packet_sha256,
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_packet():
    content = "ERL tracks primary-source funding and advocacy edges."
    entry = {
        "entry_id": "MEM-ERL-001",
        "source_kv_instance_id": "KV-INSTANCE-1",
        "relative_path": "02_Research/ERL/ai-influence.md",
        "title": "ERL AI influence research continuity",
        "content": content,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "tags": ["ERL", "AI funding"],
        "retention_class": "DURABLE",
        "provenance_ref": "ERL-EDUCATIONAL-ACCESS-INFLUENCE-001",
    }
    entries = [entry]
    return {
        "schema": "stegverse.kv.ai-memory-context-packet/v1",
        "packet_id": "KVMEM-testpacket001",
        "request_id": "REQ-AURI-ERL-001",
        "request_sha256": "0" * 64,
        "kv_class": "PERSONAL_KV",
        "authority_domain": "PERSON",
        "consumer_ai_role": "PERSONAL_ASSISTANT_AI",
        "purpose": "Recover prior ERL research context",
        "entries": entries,
        "entries_sha256": hashlib.sha256(canonical(entries).encode("utf-8")).hexdigest(),
        "selected_item_count": 1,
        "selected_content_bytes": len(content.encode("utf-8")),
        "secret_material_included": False,
        "cross_authority_content_included": False,
        "intr_admission_required": True,
        "model_is_authority": False,
        "context_transfers_authority": False,
        "authority_effect": "NONE_CONTEXT_ONLY",
    }


def make_admission(packet):
    return {
        "disposition": "ALLOW",
        "packet_id": packet["packet_id"],
        "packet_sha256": memory_packet_sha256(packet),
        "receipt_hash": "sha256:" + ("a" * 64),
    }


def test_bridge_requires_exact_packet_admission_and_binds_metadata():
    packet = make_packet()
    request = build_provider_request_with_kv_memory(
        provider="deepseek",
        model="deepseek-chat",
        messages=[{"role": "user", "content": "What did we establish about the ERL funding lane?"}],
        memory_packet=packet,
        memory_packet_admission=make_admission(packet),
    )
    assert request.allowed_sources == ("model_knowledge", "kv_memory_context")
    assert request.messages[0].role == "system"
    assert "STEGVERSE_KV_MEMORY_CONTEXT" in request.messages[0].content
    metadata = request.metadata["kv_memory_context"]
    assert metadata["packet_id"] == packet["packet_id"]
    assert metadata["packet_sha256"] == memory_packet_sha256(packet)
    assert metadata["intr_receipt_hash"] == "sha256:" + ("a" * 64)
    assert metadata["context_transfers_authority"] is False
    assert metadata["model_is_authority"] is False
    assert metadata["authority_effect"] == "NONE_CONTEXT_ONLY"


def test_bridge_rejects_denied_memory_packet():
    packet = make_packet()
    admission = make_admission(packet)
    admission["disposition"] = "DENY"
    with pytest.raises(KVMemoryContextBridgeError, match="did not ALLOW"):
        build_provider_request_with_kv_memory(
            provider="deepseek",
            model="deepseek-chat",
            messages=[{"role": "user", "content": "test"}],
            memory_packet=packet,
            memory_packet_admission=admission,
        )


def test_bridge_rejects_tampered_packet_after_admission():
    packet = make_packet()
    admission = make_admission(packet)
    packet["purpose"] = "tampered purpose"
    with pytest.raises(KVMemoryContextBridgeError, match="exact hash mismatch"):
        build_provider_request_with_kv_memory(
            provider="deepseek",
            model="deepseek-chat",
            messages=[{"role": "user", "content": "test"}],
            memory_packet=packet,
            memory_packet_admission=admission,
        )


def test_bridge_rejects_tampered_entry_content():
    packet = make_packet()
    packet["entries"][0]["content"] = "tampered"
    admission = make_admission(packet)
    with pytest.raises(KVMemoryContextBridgeError, match="content hash mismatch"):
        build_provider_request_with_kv_memory(
            provider="deepseek",
            model="deepseek-chat",
            messages=[{"role": "user", "content": "test"}],
            memory_packet=packet,
            memory_packet_admission=admission,
        )


def test_bridge_rejects_cross_authority_profile():
    packet = make_packet()
    packet["kv_class"] = "ORGANIZATIONAL_KV"
    packet["authority_domain"] = "ORGANIZATION"
    packet["consumer_ai_role"] = "ORGANIZATIONAL_AI"
    admission = make_admission(packet)
    with pytest.raises(KVMemoryContextBridgeError, match="requires PERSONAL_KV"):
        build_provider_request_with_kv_memory(
            provider="deepseek",
            model="deepseek-chat",
            messages=[{"role": "user", "content": "test"}],
            memory_packet=packet,
            memory_packet_admission=admission,
        )


def test_bridge_rejects_secret_flag():
    packet = make_packet()
    packet["secret_material_included"] = True
    admission = make_admission(packet)
    with pytest.raises(KVMemoryContextBridgeError, match="secret material"):
        build_provider_request_with_kv_memory(
            provider="deepseek",
            model="deepseek-chat",
            messages=[{"role": "user", "content": "test"}],
            memory_packet=packet,
            memory_packet_admission=admission,
        )
