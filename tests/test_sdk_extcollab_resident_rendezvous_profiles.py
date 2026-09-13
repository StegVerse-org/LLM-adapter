from datetime import datetime, timezone

import pytest

from llm_adapter.resident_rendezvous_api import (
    LISTENER_CONSUMER,
    LISTENER_EXPECTED,
    RESEAL_CONSUMER,
    RESEAL_EXPECTED,
    ResidentRendezvousError,
    PROFILES,
    sha256_uri,
    validate_resident_request,
    validate_rendezvous_request,
)


NODE = "SV-NODE-0123456789abcdef01234567"
CORRELATION = "transport-correlation:sha256:" + "a" * 64
NOW = datetime(2026, 9, 13, 19, 0, tzinfo=timezone.utc)


def envelope(consumer: str, resident_request: dict) -> dict:
    return {
        "schema": "stegverse.resident-rendezvous.request/v1",
        "request_id": "sdk-extcollab-" + consumer,
        "target_node_ref": NODE,
        "consumer": consumer,
        "resident_request": resident_request,
        "resident_request_sha256": sha256_uri(resident_request),
        "submitted_at": "2026-09-13T19:00:00+00:00",
        "expires_at": "2026-09-13T19:30:00+00:00",
        "submitter_authorization_ref": CORRELATION,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def test_external_collaboration_profiles_are_exact_and_transport_only():
    assert PROFILES[RESEAL_CONSUMER]["submitter_ref"] == "transport_correlation_only"
    assert PROFILES[LISTENER_CONSUMER]["submitter_ref"] == "transport_correlation_only"
    assert validate_resident_request(RESEAL_EXPECTED, consumer=RESEAL_CONSUMER) == RESEAL_EXPECTED
    assert validate_resident_request(LISTENER_EXPECTED, consumer=LISTENER_CONSUMER) == LISTENER_EXPECTED


def test_reseal_mutation_fails_closed():
    mutated = dict(RESEAL_EXPECTED)
    mutated["request_granted_authority"] = True
    with pytest.raises(ResidentRendezvousError):
        validate_resident_request(mutated, consumer=RESEAL_CONSUMER)


def test_listener_mutation_fails_closed():
    mutated = dict(LISTENER_EXPECTED)
    mutated["provider_contact_allowed"] = True
    with pytest.raises(ResidentRendezvousError):
        validate_resident_request(mutated, consumer=LISTENER_CONSUMER)


def test_gateway_accepts_exact_reseal_and_listener_envelopes():
    assert validate_rendezvous_request(envelope(RESEAL_CONSUMER, RESEAL_EXPECTED), now=NOW)["consumer"] == RESEAL_CONSUMER
    assert validate_rendezvous_request(envelope(LISTENER_CONSUMER, LISTENER_EXPECTED), now=NOW)["consumer"] == LISTENER_CONSUMER


def test_gateway_requires_transport_correlation_not_node_receipt_identity():
    value = envelope(RESEAL_CONSUMER, RESEAL_EXPECTED)
    value["submitter_authorization_ref"] = "node-receipt-1-sha256:" + "b" * 64
    with pytest.raises(ResidentRendezvousError):
        validate_rendezvous_request(value, now=NOW)
