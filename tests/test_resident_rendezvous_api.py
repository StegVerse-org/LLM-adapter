from __future__ import annotations

from datetime import datetime, timezone
import copy

import pytest

from llm_adapter.resident_rendezvous_api import (
    ResidentRendezvousError,
    next_request,
    sha256_uri,
    store_acknowledgement,
    store_request,
)


NOW = datetime(2026, 8, 31, 2, 35, tzinfo=timezone.utc)


def resident_request():
    return {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-001",
        "state": "REQUESTED",
        "task_id": "SHWP-STEGOS-KV-INTR-CHAIN-001",
        "mode": "STEGOS_KV_INTR_CHAIN",
        "entrypoint": "scripts/refresh_and_execute_resident_task.py",
        "steps": [
            "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
            "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
            "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
            "SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001",
        ],
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
        "note": "Advance the existing admitted chain only.",
    }


def envelope():
    inner = resident_request()
    return {
        "schema": "stegverse.resident-rendezvous.request/v1",
        "request_id": "rendezvous-kv-001",
        "target_node_ref": "node:sovereign-primary",
        "consumer": "stegos_kv_intr_chain",
        "resident_request": inner,
        "resident_request_sha256": sha256_uri(inner),
        "submitted_at": "2026-08-31T02:34:00Z",
        "expires_at": "2026-08-31T03:34:00Z",
        "submitter_authorization_ref": "owner-assertion:opaque",
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def test_store_fetch_ack_round_trip(tmp_path):
    request = envelope()
    stored = store_request(request, root=tmp_path, now=NOW)
    assert stored["state"] == "PENDING"
    fetched = next_request("node:sovereign-primary", root=tmp_path, now=NOW)
    assert fetched == request

    ack = {
        "schema": "stegverse.resident-rendezvous.acknowledgement/v1",
        "request_id": request["request_id"],
        "target_node_ref": request["target_node_ref"],
        "resident_request_sha256": request["resident_request_sha256"],
        "resident_consumption_state": "ATTEMPT_RECORDED",
        "local_receipt_refs": [
            "receipts/sovereign-host/stegos-kv-intr-chain-consumption.latest.json"
        ],
        "terminal_chain_observed": False,
        "credential_authority": "TV/TVC",
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
        "acknowledged_at": "2026-08-31T02:36:00Z",
    }
    result = store_acknowledgement(ack, root=tmp_path)
    assert result["state"] == "ACKNOWLEDGED"
    assert result["canonical_runtime_evidence_verified"] is False
    assert next_request("node:sovereign-primary", root=tmp_path, now=NOW) is None


def test_duplicate_id_with_different_bytes_fails(tmp_path):
    request = envelope()
    store_request(request, root=tmp_path, now=NOW)
    changed = copy.deepcopy(request)
    changed["submitter_authorization_ref"] = "owner-assertion:different"
    with pytest.raises(ResidentRendezvousError, match="collision"):
        store_request(changed, root=tmp_path, now=NOW)


def test_arbitrary_task_and_command_fields_fail_closed(tmp_path):
    request = envelope()
    request["resident_request"]["task_id"] = "OTHER"
    request["resident_request_sha256"] = sha256_uri(request["resident_request"])
    with pytest.raises(ResidentRendezvousError, match="task_id mismatch"):
        store_request(request, root=tmp_path, now=NOW)

    request = envelope()
    request["resident_request"]["command"] = "echo nope"
    request["resident_request_sha256"] = sha256_uri(request["resident_request"])
    with pytest.raises(ResidentRendezvousError, match="forbidden field"):
        store_request(request, root=tmp_path, now=NOW)


def test_expired_request_not_delivered(tmp_path):
    request = envelope()
    store_request(request, root=tmp_path, now=NOW)
    late = datetime(2026, 8, 31, 3, 35, tzinfo=timezone.utc)
    assert next_request("node:sovereign-primary", root=tmp_path, now=late) is None


def test_ack_digest_mismatch_rejected(tmp_path):
    request = envelope()
    store_request(request, root=tmp_path, now=NOW)
    ack = {
        "schema": "stegverse.resident-rendezvous.acknowledgement/v1",
        "request_id": request["request_id"],
        "target_node_ref": request["target_node_ref"],
        "resident_request_sha256": "sha256:" + ("0" * 64),
        "resident_consumption_state": "BLOCKED",
        "local_receipt_refs": [],
        "terminal_chain_observed": False,
        "credential_authority": "TV/TVC",
        "gateway_execution_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
        "acknowledged_at": "2026-08-31T02:36:00Z",
    }
    with pytest.raises(ResidentRendezvousError, match="digest mismatch"):
        store_acknowledgement(ack, root=tmp_path)
