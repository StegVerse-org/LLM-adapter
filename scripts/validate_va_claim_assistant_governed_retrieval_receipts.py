#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDENTITY = {
    "contract_version": "stegverse.steggate.runtime-identity.v1",
    "runtime_identity": "stegverse:steggate:canonical:three-layer:v1",
    "canonical_owner": "StegVerse-Labs/StegCore",
    "canonical_admissibility_runtime": "stegcore.three_layer.evaluate_three_layer",
}


def load_and_verify(relative_path: str) -> dict:
    path = ROOT / relative_path
    value = json.loads(path.read_text(encoding="utf-8"))
    material = dict(value)
    expected = material.pop("receipt_hash")
    actual = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert expected == actual, f"{relative_path}: receipt hash mismatch"
    return value


def main() -> int:
    retrieval = load_and_verify("receipts/va-claim-assistant-public-source-fixture.json")
    assert retrieval["route"] == "evidence_requirement"
    assert retrieval["capability_state"] == "SOURCE_GROUNDED_ASSISTANT"
    assert not any(retrieval["authority_flags"].values())
    assert "contract_refs" not in retrieval

    classifier = load_and_verify("receipts/va-claim-assistant-route-classifier-validation.json")
    assert classifier["result"] == "PASS"
    assert classifier["ambiguous_state"] == "REVIEW_REQUIRED"
    assert classifier["unsupported_state"] == "REVIEW_REQUIRED"
    assert classifier["urgent_route"] == "urgent_safety"
    assert classifier["authority_granted"] is False

    generators = load_and_verify("receipts/va-claim-assistant-route-generators-validation.json")
    assert generators["result"] == "PASS"
    assert generators["source_registry_commit"] == "e69e8421084b1343a9dc809fdb2a579089d37813"
    assert generators["source_registry_blob_sha"] == "a83ff2dd8343f947265981609b154693cc5deecc"
    assert generators["answer_ready_public_routes"] == sorted([
        "claim_type", "evidence_requirement", "service_connection",
        "rating_criteria", "effective_date", "appeal_or_supplemental_claim",
        "cp_examination", "lay_statement", "private_record_collection",
        "procedural_filing", "representation_referral",
    ])
    assert generators["document_route_generator"] == "PASS_WITH_SANITIZED_DERIVED_CONTEXT"
    assert generators["urgent_safety_route"] == "AUTHORITY_RESOLUTION_REQUIRED"
    assert generators["urgent_safety_missing_source"] == "VA-CRISIS-LINE"
    assert generators["raw_document_and_direct_identifier_rejection"] is True
    assert generators["site_answer_schema_additional_properties_rejected"] is True
    assert generators["authority_granted"] is False
    assert generators["activation_granted"] is False

    dispatch = load_and_verify("receipts/va-claim-assistant-governed-dispatch-validation.json")
    assert dispatch["result"] == "PASS"
    assert dispatch["states_verified"] == [
        "ANSWER_READY_PENDING_TVC_AND_CUSTODY",
        "DOCUMENT_CONTEXT_REQUIRED",
        "AUTHORITY_RESOLUTION_REQUIRED",
        "REVIEW_REQUIRED",
    ]
    assert dispatch["document_route_answer_ready_with_sanitized_context"] is True
    assert dispatch["document_route_missing_context_fails_closed"] is True
    assert dispatch["privacy_boundary_rejection_verified"] is True
    assert dispatch["urgent_safety_authority_resolution_required"] is True
    assert dispatch["authority_granted"] is False
    assert dispatch["activation_granted"] is False

    execution = load_and_verify("receipts/va-claim-assistant-service-connection-execution-readiness.json")
    assert execution["schema_version"] == "1.1.0"
    assert execution["state"] in {"BLOCKED", "REVIEW_REQUIRED", "COMPLETE"}
    assert execution["route"] == "service_connection"
    identity = execution["steggate_runtime_identity"]
    for key, value in EXPECTED_IDENTITY.items():
        assert identity[key] == value
    assert identity["transport_identity_authoritative"] is False
    assert identity["application_specific_policy_authority"] is False
    assert execution["tvc_admission"]["receipt_hash"] == "aec5c2fa8c2c6b73e6dd9dddbafa39314a30bd0ccf19bb881349be2d3e9724f8"
    assert execution["tvc_admission"]["answer_receipt_hash"] == "bd1f6c3e751b1adf2345383f724f133c321e0e42096b4556f682837caf73ee29"
    assert execution["tvc_admission"]["dispatch_receipt_hash"] == "55419dc015db717f10914c86286b3222493753545f03fb4bd675a7dd2db4bd4e"
    assert execution["authority_effect"] is False
    assert execution["activation_effect"] is False
    if execution["state"] == "BLOCKED":
        assert execution["blockers"] == ["provider_execution_evidence_missing"]
        assert execution["provider_execution_observed"] is False
    elif execution["state"] == "COMPLETE":
        assert execution["provider_execution_observed"] is True
        assert execution["custody_state"] == "READY_FOR_MASTER_RECORDS"

    print(f"VA_GOVERNED_RETRIEVAL_VALIDATION_PASS:{execution['state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
