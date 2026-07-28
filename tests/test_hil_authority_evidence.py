from __future__ import annotations

import hashlib
from unittest.mock import patch

from llm_adapter import service_gateway, service_gateway_site


TVC = {
    "role": "service_gateway_intake",
    "decision_id": "TVC-DECISION-TEST",
    "policy_hash": "sha256:" + "a" * 64,
    "admissible": True,
    "binding_matched": True,
    "allowed_keys": sorted(service_gateway.INTAKE_KEYS),
    "denied_keys": [],
    "internal_note": "must not be exposed",
}


def test_authority_evidence_is_digest_bound_and_privacy_minimized() -> None:
    with patch.object(service_gateway_site.gateway, "_runtime", return_value={"tvc": TVC}):
        readiness = service_gateway_site.site_hil_readiness()
        response = service_gateway_site.hil_authority_evidence()

    assert hashlib.sha256(response.body).hexdigest() == readiness["authority_evidence_sha256"]
    evidence = service_gateway_site._authority_evidence(TVC)
    assert evidence["schema_version"] == "HIL-TVC-AUTHORITY-EVIDENCE-v1"
    assert evidence["authority_role"] == "service_gateway_intake"
    assert evidence["decision_id"] == "TVC-DECISION-TEST"
    assert evidence["admissible"] is True
    assert evidence["binding_matched"] is True
    assert evidence["denied_key_count"] == 0
    assert evidence["restricted_fields_exposed"] is False
    assert "internal_note" not in evidence
    assert "allowed_keys" not in evidence
    assert "denied_keys" not in evidence
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_authority_evidence_changes_when_authority_scope_changes() -> None:
    baseline = service_gateway_site._authority_evidence_sha256(TVC)
    changed = dict(TVC)
    changed["denied_keys"] = ["service-gateway/hil-intake/receipt-key"]
    assert service_gateway_site._authority_evidence_sha256(changed) != baseline
