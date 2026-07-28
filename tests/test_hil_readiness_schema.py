from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import jsonschema

from llm_adapter import service_gateway_site

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schemas" / "hil-readiness-v1.schema.json").read_text(encoding="utf-8")
)
TVC_RECEIPT = {
    "role": "service_gateway_intake",
    "decision_id": "TVC-DECISION-TEST",
    "policy_hash": "sha256:" + "b" * 64,
    "admissible": True,
    "binding_matched": True,
    "allowed_keys": sorted(service_gateway_site.gateway.INTAKE_KEYS),
    "denied_keys": [],
}


def readiness_payload() -> dict:
    with patch.object(
        service_gateway_site.gateway,
        "_runtime",
        return_value={"tvc": dict(TVC_RECEIPT)},
    ):
        return service_gateway_site.site_hil_readiness()


def rejects(payload: dict) -> bool:
    try:
        jsonschema.validate(payload, SCHEMA)
    except jsonschema.ValidationError:
        return True
    return False


def test_runtime_readiness_conforms_to_schema() -> None:
    jsonschema.validate(readiness_payload(), SCHEMA)


def test_readiness_rejects_unknown_fields() -> None:
    payload = readiness_payload()
    payload["internal_storage_path"] = "/private/runtime"
    assert rejects(payload), "readiness schema accepted undeclared internal field"


def test_readiness_rejects_unbounded_retry_authority() -> None:
    payload = readiness_payload()
    payload["notification_max_attempts"] = 21
    assert rejects(payload), "readiness schema accepted retry authority above governed bound"


def test_readiness_rejects_address_retention_claim() -> None:
    payload = readiness_payload()
    payload["expired_recipient_addresses_retained"] = True
    assert rejects(payload), "readiness schema accepted expired-address retention"


def test_readiness_requires_receipt_bound_status_authority() -> None:
    payload = readiness_payload()
    payload["submission_status_authorization"] = "SUBMISSION_ID_ONLY"
    assert rejects(payload), "readiness schema accepted weaker status authority"


def test_readiness_rejects_unbound_or_inadmissible_tvc_authority() -> None:
    for field, invalid in (
        ("tvc_authority_role", "other_role"),
        ("tvc_admissible", False),
        ("tvc_binding_matched", False),
        ("tvc_decision_receipt_sha256", "not-a-digest"),
        ("tvc_policy_hash", "not-a-policy-hash"),
    ):
        payload = readiness_payload()
        payload[field] = invalid
        assert rejects(payload), f"readiness schema accepted invalid {field}"
