from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json

from llm_adapter.org_federation_rendezvous_api import (
    ACK_SCHEMA,
    FRAME_SCHEMA,
    next_frame,
    sha256_uri,
    sha256_uri_bytes,
    store_ack,
    store_frame,
)


def _frame(origin: str = "StegVerse-Labs", destination: str = "Triad-Test") -> dict:
    packet = {
        "schema_version": "stegverse.intr.org-boundary.v1",
        "packet_id": "ECOSYSTEM-MONITOR-20260831-001:triad-test",
        "direction": "INGRESS",
        "origin": {"org": origin, "service": "stegverse-labs.org-control"},
        "destination": {"org": destination, "service": "triad-test.org-control"},
        "carrier": {"kind": "HB_DERIVED", "reference": "org-federation"},
        "intr_profile": "stegverse.intr.org-boundary.v1",
        "transition": {
            "reference": "ecosystem.communication.v1",
            "authority_effect": "NONE",
            "conditions": [],
        },
        "payload": {
            "communication_id": "ECOSYSTEM-MONITOR-20260831-001",
            "message_class": "ecosystem.monitor.request",
            "subject": "Ecosystem resident runtime status",
            "body": {"monitor": "resident-status"},
            "requested_action": "REPORT_STATUS",
            "audience": "ECOSYSTEM",
            "target_organization": destination,
            "target_count": 14,
        },
        "evidence": {
            "ingress_receipt": None,
            "dispatch_receipt": None,
            "consumption_receipt": None,
            "egress_receipt": None,
            "reconstruction_reference": None,
        },
    }
    raw = json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    body = {
        "schema": FRAME_SCHEMA,
        "packet_id": packet["packet_id"],
        "packet_sha256": sha256_uri_bytes(raw),
        "packet_base64": base64.b64encode(raw).decode("ascii"),
        "heartbeat_reference": {
            "epoch": 32,
            "generation": 32,
            "heartbeat_id": "HB:32",
            "sampled_unix_ns": 1787511600000000000,
            "phase_offset_ns": 0,
            "frequency_hz": 100,
            "progression_dependency": "OSCILLATOR_ONLY",
            "authority_effect": "NONE",
        },
        "channel": {
            "channel_id": "HB:H1:P0",
            "phase_slot": 0,
            "phase_slot_count": 16,
            "derivation": "PAYLOAD_SHA256_FIRST64_MOD_16",
            "authority_effect": "NONE_CARRIER_ONLY",
        },
        "origin_org": origin,
        "destination_org": destination,
        "intr_profile": "stegverse.intr.org-boundary.v1",
        "authority_effect": "NONE_CARRIER_ONLY",
    }
    return {**body, "frame_sha256": sha256_uri(body)}


def test_store_fetch_ack_round_trip(tmp_path) -> None:
    frame = _frame()
    stored = store_frame(frame, root=tmp_path)
    assert stored["state"] == "PENDING"
    assert stored["gateway_execution_authority"] == "NONE"

    fetched = next_frame("Triad-Test", root=tmp_path)
    assert fetched == frame
    assert next_frame("master-records", root=tmp_path) is None

    ack = {
        "schema": ACK_SCHEMA,
        "organization": "Triad-Test",
        "packet_id": frame["packet_id"],
        "frame_sha256": frame["frame_sha256"],
        "state": "CONSUMED",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    result = store_ack(ack, root=tmp_path)
    assert result["state"] == "ACKNOWLEDGED"
    assert next_frame("Triad-Test", root=tmp_path) is None


def test_duplicate_same_bytes_is_idempotent(tmp_path) -> None:
    frame = _frame()
    first = store_frame(frame, root=tmp_path)
    second = store_frame(frame, root=tmp_path)
    assert first == second
