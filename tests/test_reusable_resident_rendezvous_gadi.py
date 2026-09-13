from __future__ import annotations

from datetime import datetime, timezone

import pytest

from llm_adapter.resident_rendezvous_api import (
    GADI_CONSUMER,
    GADI_EXPECTED,
    ResidentRendezvousError,
    discover_resident,
    next_request,
    sha256_uri,
    store_advertisement,
    store_request,
)

NOW = datetime(2026, 9, 13, 5, 10, tzinfo=timezone.utc)
NODE = "SV-NODE-" + "d" * 24


def gadi_envelope():
    inner = dict(GADI_EXPECTED)
    digest = sha256_uri(inner)
    return {
        "schema": "stegverse.resident-rendezvous.request/v1",
        "request_id": "rendezvous-gadi-001",
        "target_node_ref": NODE,
        "consumer": GADI_CONSUMER,
        "resident_request": inner,
        "resident_request_sha256": digest,
        "submitted_at": "2026-09-13T05:09:00Z",
        "expires_at": "2026-09-13T06:09:00Z",
        "submitter_authorization_ref": "transport-correlation:" + digest,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def gadi_advertisement():
    return {
        "schema": "stegverse.resident-rendezvous.advertisement/v1",
        "target_node_ref": NODE,
        "consumer": GADI_CONSUMER,
        "current_resident_request_id": GADI_EXPECTED["request_id"],
        "advertised_at": "2026-09-13T05:09:30Z",
        "expires_at": "2026-09-13T05:12:30Z",
        "credential_authority": "TV/TVC",
        "gateway_execution_authority": "NONE",
        "advertisement_grants_authority": False,
        "authority_effect": "NONE_DISCOVERY_ONLY",
    }


def test_gadi_request_uses_transport_correlation_not_node_verification(tmp_path):
    request = gadi_envelope()
    stored = store_request(request, root=tmp_path, now=NOW)
    assert stored["state"] == "PENDING"
    assert stored["gateway_execution_authority"] == "NONE"
    fetched = next_request(NODE, root=tmp_path, now=NOW, consumer=GADI_CONSUMER)
    assert fetched == request


def test_gadi_rejects_device_provenance_as_transport_correlation(tmp_path):
    request = gadi_envelope()
    request["submitter_authorization_ref"] = "node-receipt-1-sha256:" + "c" * 64
    with pytest.raises(ResidentRendezvousError, match="transport correlation reference invalid"):
        store_request(request, root=tmp_path, now=NOW)


def test_gadi_inner_contract_drift_fails_closed(tmp_path):
    request = gadi_envelope()
    request["resident_request"]["request_granted_authority"] = True
    request["resident_request_sha256"] = sha256_uri(request["resident_request"])
    with pytest.raises(ResidentRendezvousError, match="GADI resident_request contract mismatch"):
        store_request(request, root=tmp_path, now=NOW)


def test_discovery_is_profile_scoped_and_non_authorizing(tmp_path):
    store_advertisement(gadi_advertisement(), root=tmp_path, now=NOW)
    result = discover_resident(root=tmp_path, now=NOW, consumer=GADI_CONSUMER)
    assert result["state"] == "AVAILABLE"
    assert result["consumer"] == GADI_CONSUMER
    assert result["current_resident_request_id"] == GADI_EXPECTED["request_id"]
    assert result["target_node_ref"] == NODE
    assert result["gateway_execution_authority"] == "NONE"
    assert result["discovery_grants_authority"] is False


def test_profile_filter_prevents_cross_consumer_delivery(tmp_path):
    store_request(gadi_envelope(), root=tmp_path, now=NOW)
    assert next_request(NODE, root=tmp_path, now=NOW, consumer="stegos_kv_intr_chain") is None
    assert next_request(NODE, root=tmp_path, now=NOW, consumer=GADI_CONSUMER) is not None
