import pytest

from llm_adapter.master_records_local_usage_submission import (
    MasterRecordsLocalUsageError,
    submit_provider_usage_to_local_master_records,
)


def event():
    return {
        "schema": "stegverse.llm_adapter.provider_usage.v1",
        "measurement_id": "measurement-1",
        "session_id": "session-1",
        "transition_id": "transition-1",
        "origin_entry_point": "intr",
        "interaction_type": "governed_deepseek_inference",
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "metric_owner": "llm_adapter",
        "authority_granted": False,
        "custody_recorded": False,
        "event_sha256": "a" * 64,
    }


def reply(**overrides):
    base = {
        "schema": "stegverse.master_records.local_provider_usage_result.v1",
        "decision": "ALLOW_CUSTODY_RESULT",
        "status": "CUSTODY_RECORDED",
        "receipt_id": "master-records-provider-usage-receipt:test",
        "session_id": "session-1",
        "measurement_id": "measurement-1",
        "event_sha256": "a" * 64,
        "custody_recorded": True,
        "reconstructability": "PASS",
        "authority_granted": False,
        "admissibility_determined": False,
        "execution_authority": False,
        "publication_authority": False,
        "secret_material_returned": False,
        "credential_material_returned": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE",
    }
    base.update(overrides)
    return base


def test_local_submitter_sends_only_non_authorizing_custody_request_and_requires_reconstruction_pass():
    observed = []
    result = submit_provider_usage_to_local_master_records(
        event(), exchange=lambda request: observed.append(request) or reply()
    )
    assert observed == [{
        "schema": "stegverse.master_records.local_provider_usage_request.v1",
        "event": event(),
        "authority_requested": False,
        "custody_requested": True,
    }]
    assert result["status"] == "CUSTODY_RECORDED"
    assert result["custody_recorded"] is True
    assert result["reconstructability"] == "PASS"
    assert result["authority_granted"] is False
    assert result["credential_material_present"] is False
    assert result["transport"] == "master_records_local_unix_socket"


@pytest.mark.parametrize("field,value", [
    ("decision", "FAIL_CLOSED"),
    ("status", "CUSTODY_NOT_RECORDED"),
    ("custody_recorded", False),
    ("reconstructability", "PENDING"),
    ("authority_granted", True),
    ("admissibility_determined", True),
    ("execution_authority", True),
    ("publication_authority", True),
    ("secret_material_returned", True),
    ("credential_material_returned", True),
    ("authority_effect", "ALLOW"),
    ("credential_authority", "consumer"),
    ("session_id", "drift"),
    ("measurement_id", "drift"),
    ("event_sha256", "b" * 64),
])
def test_local_submitter_fails_closed_on_boundary_or_identity_drift(field, value):
    with pytest.raises(MasterRecordsLocalUsageError):
        submit_provider_usage_to_local_master_records(
            event(), exchange=lambda request: reply(**{field: value})
        )


def test_local_submitter_rejects_client_self_custody_or_authority_claim():
    bad = event()
    bad["custody_recorded"] = True
    with pytest.raises(MasterRecordsLocalUsageError, match="provider_usage_event_boundary_invalid"):
        submit_provider_usage_to_local_master_records(bad, exchange=lambda request: reply())
    bad = event()
    bad["authority_granted"] = True
    with pytest.raises(MasterRecordsLocalUsageError, match="provider_usage_event_boundary_invalid"):
        submit_provider_usage_to_local_master_records(bad, exchange=lambda request: reply())
