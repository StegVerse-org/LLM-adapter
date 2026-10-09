from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "authorized_provider_activation_verifier",
    ROOT / "scripts" / "verify_authorized_provider_activation.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
validate_runtime_result = MODULE.validate_runtime_result


def _identity() -> dict:
    return {
        "transition_id": "transition.test.provider",
        "run_id": "run.test.provider",
        "event_id": "event.test.provider",
        "origin_manifest_id": "origin.test.provider",
    }


def _health() -> dict:
    return {
        "governed_provider_enabled": True,
        "provider_output_is_authority": False,
    }


def _response() -> dict:
    identity = _identity()
    return {
        **identity,
        "lifecycle_state": "COMPLETED",
        "final_receipt": True,
        "final_receipt_id": "final-response-receipt:sha256:test",
        "provider": {
            "used": True,
            "status": "USED",
            "provider_receipt_id": "provider-response-receipt:sha256:test",
            "fallback_required": False,
        },
        "provider_usage_submission": {
            "schema": "stegverse.usage.internal_submission.v1",
            "measurement_id": "provider-usage:sha256:test",
            "event_sha256": "a" * 64,
            "authority_granted": False,
            "custody_recorded": False,
        },
        "authority": {
            "provider_output_is_authority": False,
            "repository_mutation_allowed": False,
            "publication_allowed": False,
            "gateway_receipt_is_final": False,
            "final_response_receipt_is_repository_execution_authority": False,
            "local_persistence_is_master_records_organization_record": False,
            "site_grants_admissibility": False,
            "provider_usage_grants_authority": False,
        },
    }


def test_complete_authorized_provider_path_passes() -> None:
    assert validate_runtime_result(_health(), _response(), _identity()) == []


def test_fallback_provider_fails_closed() -> None:
    response = _response()
    response["provider"]["used"] = False
    response["provider"]["status"] = "DISABLED"
    response["provider"]["fallback_required"] = True
    blockers = validate_runtime_result(_health(), response, _identity())
    assert "real_provider_not_used" in blockers
    assert "provider_status_not_used" in blockers
    assert "provider_fallback_used" in blockers


def test_local_usage_cannot_self_claim_custody() -> None:
    response = _response()
    response["provider_usage_submission"]["custody_recorded"] = True
    blockers = validate_runtime_result(_health(), response, _identity())
    assert "local_usage_misclassified_as_custody" in blockers


def test_master_records_is_not_a_predicate() -> None:
    """No Master Records health flag, usage reply, or reconstruction gates the slice."""
    health = _health()
    health["master_records_submission_enabled"] = False
    response = _response()
    response["master_records_usage_submission"] = {"status": "NOT_CONFIGURED", "custody_recorded": False}
    response["master_record_status"] = "NOT_RECORDED"
    response["reconstruction_status"] = "NOT_RUN"
    assert validate_runtime_result(health, response, _identity()) == []


def test_missing_provider_usage_record_fails_closed() -> None:
    response = _response()
    response["provider_usage_submission"] = {}
    blockers = validate_runtime_result(_health(), response, _identity())
    assert "provider_usage_persistence_missing" in blockers
    assert "provider_usage_identity_missing" in blockers


def test_missing_organization_ledger_transition_receipt_fails_closed() -> None:
    response = _response()
    response["final_receipt"] = False
    response["final_receipt_id"] = None
    blockers = validate_runtime_result(_health(), response, _identity())
    assert "organization_ledger_transition_receipt_missing" in blockers


def test_unverified_slice_carries_the_six_non_allow_fields() -> None:
    disposition = MODULE.non_allow(["organization_ledger_transition_receipt_missing"])
    assert disposition["disposition"] == "FAIL_CLOSED"
    for key in ("failure_code", "failed_predicate", "required_evidence_or_repair",
                "retry_entrypoint", "owning_existing_goal", "next_attempt"):
        assert disposition[key], key
    assert disposition["owning_existing_goal"] == "LLMA-DECLARED-PATH-CONFORMANCE-368"
    assert '"BLOCKED"' not in (ROOT / "scripts" / "verify_authorized_provider_activation.py").read_text()


def test_authority_escalation_fails_closed() -> None:
    response = _response()
    response["authority"]["publication_allowed"] = True
    blockers = validate_runtime_result(_health(), response, _identity())
    assert "authority_publication_allowed_must_be_false" in blockers


def test_legacy_authority_key_names_from_deployed_adapters_are_accepted() -> None:
    response = _response()
    authority = response["authority"]
    authority["local_persistence_is_master_records_custody"] = authority.pop(
        "local_persistence_is_master_records_organization_record"
    )
    assert validate_runtime_result(_health(), response, _identity()) == []
