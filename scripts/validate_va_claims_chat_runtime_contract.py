#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/va-claims-chat-runtime.json"
OUT = ROOT / "receipts/va-claims-chat-runtime-contract-validation.json"

REQUIRED_ROUTES = {
    "claim_type",
    "evidence_requirement",
    "service_connection",
    "rating_criteria",
    "effective_date",
    "appeal_or_supplemental_claim",
    "cp_examination",
    "document_organization",
    "lay_statement",
    "private_record_collection",
    "procedural_filing",
    "representation_referral",
    "urgent_safety",
}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    errors: list[str] = []
    routes = contract.get("route_requirements", {})
    doc = contract.get("document_context_contract", {})
    filing = contract.get("filing_boundary", {})
    prohibited = contract.get("prohibited_claims", {})
    projection = contract.get("site_projection_contract", {})

    require(contract.get("contract_id") == "SV-VA-CLAIMS-CHAT-RUNTIME-001", "contract id mismatch", errors)
    require(set(routes) == REQUIRED_ROUTES, "required VA route set mismatch", errors)
    require(all(v.get("generator_required") is True for v in routes.values()), "one or more routes lack generator requirement", errors)
    require(routes.get("document_organization", {}).get("document_context_required") is True, "document organization must require document context", errors)
    require(doc.get("adapter_accepts_raw_documents") is False, "adapter must reject raw documents", errors)
    require(doc.get("adapter_accepts_sanitized_derived_context") is True, "adapter must accept sanitized derived context", errors)
    require(doc.get("raw_document_publication_allowed") is False, "raw document publication must remain prohibited", errors)
    require(doc.get("document_context_may_grant_authority") is False, "document context must not grant authority", errors)
    require(filing.get("automated_filing_active") is False, "automated filing unexpectedly active", errors)
    require(filing.get("autonomous_filing_from_uploaded_documents_allowed") is False, "autonomous filing must remain prohibited", errors)
    require(filing.get("veteran_submission_authority_preserved") is True, "veteran submission authority not preserved", errors)
    require(len(filing.get("required_before_filing_ready", [])) >= 12, "filing gate set incomplete", errors)
    require(all(value is False for value in prohibited.values()), "prohibited authority flag enabled", errors)
    require(projection.get("projection_must_be_receipt_derived") is True, "Site projection must be receipt-derived", errors)
    require(projection.get("future_capabilities_must_remain_disabled_until_verified") is True, "future capability gate missing", errors)
    require(projection.get("unsupported_routes_must_not_emit_substantive_answers") is True, "unsupported route fail-closed rule missing", errors)
    require(contract.get("authority_effect") is False, "contract must not grant authority", errors)
    require(contract.get("activation_effect") is False, "contract must not activate runtime", errors)

    body = {
        "schema_version": "1.0.0",
        "state": "PASS" if not errors else "FAIL",
        "contract_id": contract.get("contract_id"),
        "route_count": len(routes),
        "required_routes_present": set(routes) == REQUIRED_ROUTES,
        "raw_documents_rejected": doc.get("adapter_accepts_raw_documents") is False,
        "sanitized_derived_context_required": doc.get("adapter_accepts_sanitized_derived_context") is True,
        "automated_filing_active": filing.get("automated_filing_active"),
        "veteran_submission_authority_preserved": filing.get("veteran_submission_authority_preserved"),
        "authority_effect": False,
        "activation_effect": False,
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "errors": errors,
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    body["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(body, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
