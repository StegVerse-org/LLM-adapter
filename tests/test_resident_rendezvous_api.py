from __future__ import annotations

from datetime import datetime, timezone
import copy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from llm_adapter.resident_rendezvous_api import (
    ResidentRendezvousError,
    discover_resident,
    next_request,
    sha256_uri,
    store_acknowledgement,
    store_advertisement,
    store_request,
    router,
)


NOW = datetime(2026, 8, 31, 2, 35, tzinfo=timezone.utc)


def resident_request():
    return {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003",
        "state": "REQUESTED",
        "task_id": "SHWP-STEGOS-KV-INTR-CHAIN-001",
        "mode": "STEGOS_KV_INTR_CHAIN",
        "entrypoint": "scripts/refresh_and_execute_resident_task.py",
        "steps": [
            "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
            "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
            "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
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
        "target_node_ref": "SV-NODE-" + "a" * 24,
        "consumer": "stegos_kv_intr_chain",
        "resident_request": inner,
        "resident_request_sha256": sha256_uri(inner),
        "submitted_at": "2026-08-31T02:34:00Z",
        "expires_at": "2026-08-31T03:34:00Z",
        "submitter_authorization_ref": "node-receipt-1-sha256:" + "c" * 64,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def advertisement(node_ref="SV-NODE-" + "a" * 24, advertised_at="2026-08-31T02:34:00Z", expires_at="2026-08-31T02:38:00Z"):
    return {
        "schema": "stegverse.resident-rendezvous.advertisement/v1",
        "target_node_ref": node_ref,
        "consumer": "stegos_kv_intr_chain",
        "current_resident_request_id": "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003",
        "advertised_at": advertised_at,
        "expires_at": expires_at,
        "credential_authority": "TV/TVC",
        "gateway_execution_authority": "NONE",
        "advertisement_grants_authority": False,
        "authority_effect": "NONE_DISCOVERY_ONLY",
    }


def test_resident_discovery_requires_exactly_one_fresh_advertisement(tmp_path):
    empty = discover_resident(root=tmp_path, now=NOW)
    assert empty["state"] == "UNAVAILABLE"
    assert empty["target_node_ref"] is None

    stored = store_advertisement(advertisement(), root=tmp_path, now=NOW)
    assert stored["state"] == "ADVERTISED"
    one = discover_resident(root=tmp_path, now=NOW)
    assert one["state"] == "AVAILABLE"
    assert one["target_node_ref"] == "SV-NODE-" + "a" * 24
    assert one["discovery_grants_authority"] is False
    assert one["gateway_execution_authority"] == "NONE"

    store_advertisement(advertisement("SV-NODE-" + "b" * 24), root=tmp_path, now=NOW)
    ambiguous = discover_resident(root=tmp_path, now=NOW)
    assert ambiguous["state"] == "AMBIGUOUS"
    assert ambiguous["target_node_ref"] is None


def test_resident_advertisement_requires_canonical_sovereign_node_ref(tmp_path):
    with pytest.raises(ResidentRendezvousError, match="canonical sovereign node ref required"):
        store_advertisement(
            advertisement("node:primary"),
            root=tmp_path,
            now=NOW,
        )


def test_current_request_requires_node_receipt_1_provenance(tmp_path):
    request = envelope()
    request["submitter_authorization_ref"] = "owner-assertion:opaque"
    with pytest.raises(
        ResidentRendezvousError,
        match="Node Receipt #1 provenance invalid",
    ):
        store_request(request, root=tmp_path, now=NOW)


def test_resident_advertisement_lease_and_contract_fail_closed(tmp_path):
    too_long = advertisement(expires_at="2026-08-31T02:40:00Z")
    with pytest.raises(ResidentRendezvousError, match="five minutes"):
        store_advertisement(too_long, root=tmp_path, now=NOW)

    wrong = advertisement()
    wrong["current_resident_request_id"] = "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-002"
    with pytest.raises(ResidentRendezvousError, match="current_resident_request_id mismatch"):
        store_advertisement(wrong, root=tmp_path, now=NOW)


def test_bound_resident_poll_auto_advertises_canonical_target(tmp_path, monkeypatch):
    monkeypatch.setenv("STEGVERSE_RESIDENT_RENDEZVOUS_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_RESIDENT_RENDEZVOUS_ROOT", str(tmp_path))
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    node_ref = "SV-NODE-" + "9" * 24

    fetched = client.get(
        "/api/resident-rendezvous/v1/requests",
        params={"target_node_ref": node_ref},
        headers={"X-StegVerse-Node-Ref": node_ref},
    )
    assert fetched.status_code == 200
    assert fetched.json()["state"] == "NO_REQUEST"

    discovered = client.get("/api/resident-rendezvous/v1/discovery")
    assert discovered.status_code == 200
    value = discovered.json()
    assert value["state"] == "AVAILABLE"
    assert value["target_node_ref"] == node_ref
    assert value["current_resident_request_id"] == "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003"
    assert value["discovery_grants_authority"] is False
    assert value["gateway_execution_authority"] == "NONE"


def test_store_fetch_ack_round_trip(tmp_path):
    request = envelope()
    stored = store_request(request, root=tmp_path, now=NOW)
    assert stored["state"] == "PENDING"
    fetched = next_request("SV-NODE-" + "a" * 24, root=tmp_path, now=NOW)
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
    assert next_request("SV-NODE-" + "a" * 24, root=tmp_path, now=NOW) is None



def test_legacy_four_step_chain_remains_exactly_allowlisted(tmp_path):
    request = envelope()
    request["resident_request"]["request_id"] = "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-001"
    request["resident_request"]["steps"] = [
        "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
        "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
        "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
        "SHWP-ENDPOINT-FANOUT-SOVEREIGN-RUNTIME-001",
    ]
    request["resident_request_sha256"] = sha256_uri(request["resident_request"])
    stored = store_request(request, root=tmp_path, now=NOW)
    assert stored["state"] == "PENDING"


def test_unknown_resident_request_id_fails_closed(tmp_path):
    request = envelope()
    request["resident_request"]["request_id"] = "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-999"
    request["resident_request_sha256"] = sha256_uri(request["resident_request"])
    with pytest.raises(ResidentRendezvousError, match="request_id not admitted"):
        store_request(request, root=tmp_path, now=NOW)


def test_superseded_request_002_remains_boundedly_admitted(tmp_path):
    request = envelope()
    request["resident_request"]["request_id"] = "RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-002"
    request["resident_request_sha256"] = sha256_uri(request["resident_request"])
    stored = store_request(request, root=tmp_path, now=NOW)
    assert stored["state"] == "PENDING"


def test_noncanonical_step_vector_fails_closed(tmp_path):
    request = envelope()
    request["resident_request"]["steps"] = [
        "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
        "SHWP-DEVICE-KV-INTR-OBSERVATION-001",
    ]
    request["resident_request_sha256"] = sha256_uri(request["resident_request"])
    with pytest.raises(ResidentRendezvousError, match="steps mismatch"):
        store_request(request, root=tmp_path, now=NOW)


def test_duplicate_id_with_different_bytes_fails(tmp_path):
    request = envelope()
    store_request(request, root=tmp_path, now=NOW)
    changed = copy.deepcopy(request)
    changed["submitter_authorization_ref"] = "node-receipt-1-sha256:" + "d" * 64
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
    assert next_request("SV-NODE-" + "a" * 24, root=tmp_path, now=late) is None


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
