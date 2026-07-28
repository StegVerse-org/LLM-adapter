from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import jsonschema

from llm_adapter import service_gateway_site

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schemas" / "hil-tvc-authority-evidence-v1.schema.json").read_text(encoding="utf-8")
)

TVC = {
    "role": "service_gateway_intake",
    "decision_id": "TVC-DECISION-TEST",
    "policy_hash": "a" * 64,
    "admissible": True,
    "binding_matched": True,
    "allowed_keys": sorted(service_gateway_site.gateway.INTAKE_KEYS),
    "denied_keys": [],
}


def evidence() -> dict:
    return service_gateway_site._authority_evidence(TVC)


def test_runtime_authority_evidence_conforms_to_schema() -> None:
    jsonschema.validate(evidence(), SCHEMA)


def test_live_schema_endpoint_matches_readiness_binding() -> None:
    with patch.object(service_gateway_site.gateway, "_runtime", return_value={"tvc": TVC}):
        readiness = service_gateway_site.site_hil_readiness()
    response = service_gateway_site.hil_authority_evidence_schema()
    assert response.media_type == "application/schema+json"
    assert readiness["authority_evidence_schema_path"] == service_gateway_site.AUTHORITY_EVIDENCE_SCHEMA_PATH
    assert readiness["authority_evidence_schema_sha256"] == service_gateway_site._schema_sha256(
        service_gateway_site.AUTHORITY_EVIDENCE_SCHEMA_PATH
    )


def test_schema_rejects_extra_or_restricted_fields() -> None:
    payload = evidence()
    payload["allowed_keys"] = ["secret/name"]
    try:
        jsonschema.validate(payload, SCHEMA)
    except jsonschema.ValidationError:
        return
    raise AssertionError("authority evidence schema accepted restricted field exposure")


def test_schema_rejects_denied_scope_or_wrong_allowed_count() -> None:
    for field, value in (("denied_key_count", 1), ("allowed_key_count", 3)):
        payload = evidence()
        payload[field] = value
        try:
            jsonschema.validate(payload, SCHEMA)
        except jsonschema.ValidationError:
            continue
        raise AssertionError(f"authority evidence schema accepted invalid {field}")
