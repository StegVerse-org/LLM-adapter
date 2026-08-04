#!/usr/bin/env python3
"""Verify governed provider-neutral Chat LLM session binding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_adapter.chat_session_binding import (  # noqa: E402
    canonical_sha256,
    prepare_session,
    validate_candidate_response,
)


DEFAULT_RECEIPT = ROOT / "receipts" / "chat-llm-session-binding-validation.json"


def _messages() -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "Provide governed assistance."},
        {"role": "user", "content": "Explain what evidence is required."},
    ]


def build_receipt() -> Dict[str, Any]:
    ecosystem = prepare_session(
        {
            "profile_id": "ecosystem-chat-llm",
            "messages": _messages(),
            "requested_features": [
                "multi_turn_conversation",
                "retrieval_augmented_generation",
                "function_and_tool_calling",
                "structured_output",
            ],
            "sources": [
                {
                    "source_id": "ecosystem-source",
                    "source_type": "general_web",
                    "uri": "https://example.org/reference",
                    "admitted": True,
                    "required_for_answer": True,
                }
            ],
            "tools": [
                {
                    "name": "build_artifact",
                    "description": "Create an artifact candidate.",
                    "input_schema": {"type": "object"},
                }
            ],
            "response_format": "json",
            "requires_factual_grounding": True,
        }
    )
    claims = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
            "sources": [
                {
                    "source_id": "va-source",
                    "source_type": "official_external",
                    "uri": "https://www.va.gov/disability/eligibility/",
                    "admitted": True,
                    "authority_class": "OFFICIAL_VA_GUIDANCE",
                    "required_for_answer": True,
                },
                {
                    "source_id": "user-record",
                    "source_type": "user_record",
                    "uri": "stegverse-user-record://session/record-1",
                    "privacy_status": "PASS",
                    "consent_present": True,
                    "content_hash": "a" * 64,
                    "required_for_answer": False,
                },
            ],
            "tools": [
                {
                    "name": "draft_checklist",
                    "description": "Create a non-filing checklist candidate.",
                    "input_schema": {"type": "object"},
                }
            ],
        }
    )
    claims_blocked = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
            "sources": [
                {
                    "source_id": "non-va",
                    "source_type": "official_external",
                    "uri": "https://example.org/claims",
                    "admitted": True,
                    "required_for_answer": True,
                }
            ],
        }
    )
    accepted_candidate = validate_candidate_response(
        claims.envelope,
        {
            "text": "The admitted VA source describes eligibility considerations.",
            "citations": ["va-source"],
            "factual_claims": [
                {"source_id": "va-source", "fact_label": "va_source_fact"}
            ],
            "tool_calls": [
                {
                    "name": "draft_checklist",
                    "status": "CANDIDATE_NOT_EXECUTED",
                }
            ],
            "side_effects_executed": False,
            "authority_claimed": False,
        },
    )
    rejected_candidate = validate_candidate_response(
        claims.envelope,
        {
            "text": "I filed the claim.",
            "citations": ["unknown"],
            "factual_claims": [],
            "tool_calls": [
                {"name": "draft_checklist", "status": "EXECUTED"}
            ],
            "side_effects_executed": True,
            "authority_claimed": True,
            "publication_claimed": True,
        },
    )

    assert ecosystem.state == "READY_FOR_PROVIDER_BINDING"
    assert claims.state == "READY_FOR_PROVIDER_BINDING"
    assert claims_blocked.state == "BLOCKED_SOURCE_POLICY"
    assert accepted_candidate.state == "ACCEPT_CANDIDATE"
    assert rejected_candidate.state == "REJECT_CANDIDATE"
    assert ecosystem.envelope["provider_call_performed"] is False
    assert claims.envelope["provider_call_performed"] is False
    assert all(
        source["decision"]["fact_label"] in {"va_source_fact", "user_record_fact"}
        for source in claims.envelope["grounding_sources"]
    )

    receipt: Dict[str, Any] = {
        "schema": "stegverse.chat_llm_session_binding.validation.v1",
        "state": "PASS",
        "ecosystem_session": {
            "state": ecosystem.state,
            "envelope_sha256": ecosystem.envelope["envelope_sha256"],
            "requested_feature_count": len(ecosystem.envelope["requested_features"]),
            "candidate_tool_count": len(ecosystem.envelope["candidate_tools"]),
            "allowed_grounding_source_count": len(
                ecosystem.envelope["grounding_sources"]
            ),
        },
        "claims_session": {
            "state": claims.state,
            "envelope_sha256": claims.envelope["envelope_sha256"],
            "allowed_fact_labels": sorted(
                source["decision"]["fact_label"]
                for source in claims.envelope["grounding_sources"]
            ),
            "official_va_only": True,
        },
        "claims_non_va_required_source": {
            "state": claims_blocked.state,
            "provider_envelope_created": claims_blocked.envelope is not None,
            "blockers": list(claims_blocked.blockers),
        },
        "candidate_validation": {
            "valid_candidate": accepted_candidate.state,
            "invalid_side_effect_candidate": rejected_candidate.state,
            "invalid_reasons": list(rejected_candidate.reasons),
        },
        "provider_configuration_attached": False,
        "provider_permission_requested": False,
        "provider_call_performed": False,
        "tools_executed": False,
        "custody_submitted": False,
        "site_mutated": False,
        "authority_effect": False,
        "activation_effect": False,
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-receipt", action="store_true")
    parser.add_argument("--receipt-path", type=Path, default=DEFAULT_RECEIPT)
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
