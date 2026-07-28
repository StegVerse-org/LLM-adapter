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


def readiness_payload() -> dict:
    with patch.object(
        service_gateway_site.gateway,
        "_runtime",
        return_value={"tvc": {"decision_id": "TVC-DECISION-TEST"}},
    ):
        return service_gateway_site.site_hil_readiness()


def test_runtime_readiness_conforms_to_schema() -> None:
    jsonschema.validate(readiness_payload(), SCHEMA)


def test_readiness_rejects_unknown_fields() -> None:
    payload = readiness_payload()
    payload["internal_storage_path"] = "/private/runtime"
    try:
        jsonschema.validate(payload, SCHEMA)
    except jsonschema.ValidationError:
        return
    raise AssertionError("readiness schema accepted undeclared internal field")


def test_readiness_rejects_unbounded_retry_authority() -> None:
    payload = readiness_payload()
    payload["notification_max_attempts"] = 21
    try:
        jsonschema.validate(payload, SCHEMA)
    except jsonschema.ValidationError:
        return
    raise AssertionError("readiness schema accepted retry authority above governed bound")


def test_readiness_rejects_address_retention_claim() -> None:
    payload = readiness_payload()
    payload["expired_recipient_addresses_retained"] = True
    try:
        jsonschema.validate(payload, SCHEMA)
    except jsonschema.ValidationError:
        return
    raise AssertionError("readiness schema accepted expired-address retention")


def test_readiness_requires_receipt_bound_status_authority() -> None:
    payload = readiness_payload()
    payload["submission_status_authorization"] = "SUBMISSION_ID_ONLY"
    try:
        jsonschema.validate(payload, SCHEMA)
    except jsonschema.ValidationError:
        return
    raise AssertionError("readiness schema accepted weaker status authority")
