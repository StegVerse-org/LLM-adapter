#!/usr/bin/env python3
"""Verify paired Ecosystem Chat and VA Claims Chat LLM profiles."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any, Dict, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_adapter.chat_profiles import (  # noqa: E402
    FULL_LLM_FEATURES,
    SourceCandidate,
    capability_matrix,
    evaluate_source,
    manifest_sha256,
    validate_parallel_profiles,
)


ECOSYSTEM_PATH = ROOT / "profiles" / "ecosystem-chat-llm.v1.json"
CLAIMS_PATH = ROOT / "profiles" / "va-claims-chat-llm.v1.json"
DEFAULT_RECEIPT = ROOT / "receipts" / "chat-llm-profiles-validation.json"


def _load(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"profile root must be an object: {path}")
    return value


def _hash_receipt(receipt: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        receipt,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_receipt() -> Dict[str, Any]:
    ecosystem_manifest = _load(ECOSYSTEM_PATH)
    claims_manifest = _load(CLAIMS_PATH)
    ecosystem, claims = validate_parallel_profiles(
        ecosystem_manifest,
        claims_manifest,
    )

    ecosystem_general = evaluate_source(
        ecosystem,
        SourceCandidate(
            source_type="general_web",
            uri="https://example.org/reference",
            admitted=True,
        ),
    )
    claims_va = evaluate_source(
        claims,
        SourceCandidate(
            source_type="official_external",
            uri="https://www.va.gov/disability/eligibility/",
            admitted=True,
            authority_class="OFFICIAL_VA_GUIDANCE",
        ),
    )
    claims_non_va = evaluate_source(
        claims,
        SourceCandidate(
            source_type="official_external",
            uri="https://example.org/claims",
            admitted=True,
        ),
    )
    claims_user_record = evaluate_source(
        claims,
        SourceCandidate(
            source_type="user_record",
            uri="stegverse-user-record://session/record-1",
            privacy_status="PASS",
            consent_present=True,
            content_hash="a" * 64,
        ),
    )

    assert ecosystem_general.allowed_for_factual_grounding is True
    assert claims_va.allowed_for_factual_grounding is True
    assert claims_va.allowed_as_authority is True
    assert claims_non_va.allowed_for_factual_grounding is False
    assert claims_user_record.allowed_for_factual_grounding is True
    assert claims_user_record.allowed_as_authority is False
    assert all(value is False for value in ecosystem.authority_policy.values())
    assert all(value is False for value in claims.authority_policy.values())

    matrix = capability_matrix((ecosystem, claims))
    assert all(matrix[ecosystem.profile_id].values())
    assert all(matrix[claims.profile_id].values())

    receipt: Dict[str, Any] = {
        "schema": "stegverse.chat_llm_profiles.validation.v1",
        "state": "PASS",
        "profiles": {
            ecosystem.profile_id: {
                "manifest_sha256": manifest_sha256(ecosystem_manifest),
                "feature_count": len(ecosystem.features),
                "full_llm_surface": ecosystem.has_full_llm_surface,
                "source_mode": ecosystem.source_policy["mode"],
            },
            claims.profile_id: {
                "manifest_sha256": manifest_sha256(claims_manifest),
                "feature_count": len(claims.features),
                "full_llm_surface": claims.has_full_llm_surface,
                "source_mode": claims.source_policy["mode"],
            },
        },
        "required_feature_count": len(FULL_LLM_FEATURES),
        "feature_sets_equal": set(ecosystem.features) == set(claims.features),
        "source_policy_checks": {
            "ecosystem_admitted_general_source": ecosystem_general.status,
            "claims_official_va_source": claims_va.status,
            "claims_non_va_source": claims_non_va.status,
            "claims_privacy_approved_user_record": claims_user_record.status,
        },
        "authority_effect": False,
        "activation_effect": False,
        "provider_execution_observed": False,
        "site_activation_observed": False,
    }
    receipt["receipt_sha256"] = _hash_receipt(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-receipt",
        action="store_true",
        help="write the deterministic validation receipt under receipts/",
    )
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=DEFAULT_RECEIPT,
    )
    args = parser.parse_args()

    receipt = build_receipt()
    if args.write_receipt:
        args.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
