from __future__ import annotations

import hashlib
import json

import pytest

from llm_adapter.kv_memory_context_bridge import memory_packet_sha256
from scripts.materialize_kv_memory_provider_request import materialize


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def packet():
    content = "Persistent Personal-KV memory remains source-authoritative context."
    entry = {
        "entry_id": "MEM-001",
        "source_kv_instance_id": "KV-INSTANCE-1",
        "relative_path": "01_Notes/continuity.md",
        "title": "Continuity",
        "content": content,
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "tags": ["continuity"],
        "retention_class": "DURABLE",
        "provenance_ref": "PERSONAL-KV-ENTRY-001",
    }
    entries = [entry]
    return {
        "schema": "stegverse.kv.ai-memory-context-packet/v1",
        "packet_id": "KVMEM-packet-001",
        "request_id": "REQ-001",
        "request_sha256": "0" * 64,
        "kv_class": "PERSONAL_KV",
        "authority_domain": "PERSON",
        "consumer_ai_role": "PERSONAL_ASSISTANT_AI",
        "purpose": "personal continuity",
        "entries": entries,
        "entries_sha256": hashlib.sha256(canonical(entries).encode()).hexdigest(),
        "selected_item_count": 1,
        "selected_content_bytes": len(content.encode()),
        "secret_material_included": False,
        "cross_authority_content_included": False,
        "intr_admission_required": True,
        "model_is_authority": False,
        "context_transfers_authority": False,
        "authority_effect": "NONE_CONTEXT_ONLY",
    }


def admission(value):
    return {
        "disposition": "ALLOW",
        "packet_id": value["packet_id"],
        "packet_sha256": memory_packet_sha256(value),
        "receipt_hash": "sha256:" + "b" * 64,
    }


def request_input():
    return {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "created_at": "2026-09-14T03:00:00+00:00",
        "messages": [{"role": "user", "content": "Continue from durable Personal-KV context."}],
        "purpose": "answer",
        "allowed_sources": ["model_knowledge"],
        "temperature": 0.0,
        "metadata": {"session_class": "PERSONAL_ASSISTANT_AI"},
    }


def test_materialization_is_exact_and_replay_stable():
    p = packet()
    first = materialize(p, admission(p), request_input())
    second = materialize(p, admission(p), request_input())
    assert first == second
    assert first["state"] == "PROVIDER_REQUEST_MATERIALIZED"
    assert first["provider_request_hash"]
    assert first["memory_packet_sha256"] == memory_packet_sha256(p)
    assert first["provider_ingress_admission_observed"] is False
    assert first["provider_execution_observed"] is False
    assert first["provider_egress_admission_observed"] is False
    assert first["kv_writeback_observed"] is False
    assert first["credential_material_present"] is False
    assert first["authority_effect"] == "NONE_MATERIALIZATION_ONLY"


def test_materialization_rejects_credential_like_input():
    p = packet()
    bad = request_input()
    bad["metadata"]["api_key"] = "forbidden"
    with pytest.raises(ValueError, match="credential-like field forbidden"):
        materialize(p, admission(p), bad)


def test_materialization_requires_replay_timestamp():
    p = packet()
    bad = request_input()
    bad.pop("created_at")
    with pytest.raises(ValueError, match="created_at required"):
        materialize(p, admission(p), bad)


def test_materialization_rejects_tampered_memory_admission():
    p = packet()
    bad_admission = admission(p)
    bad_admission["packet_sha256"] = "0" * 64
    with pytest.raises(Exception, match="exact hash mismatch"):
        materialize(p, bad_admission, request_input())
