from copy import deepcopy

import pytest

from llm_adapter.chat_profiles import FULL_LLM_FEATURES
from llm_adapter.chat_session_binding import (
    SessionBindingError,
    prepare_session,
    validate_candidate_response,
)


def _messages():
    return [
        {"role": "system", "content": "Help the user."},
        {"role": "user", "content": "Explain the evidence requirement."},
    ]


def _official_va_source(required=True):
    return {
        "source_id": "va-eligibility",
        "source_type": "official_external",
        "uri": "https://www.va.gov/disability/eligibility/",
        "admitted": True,
        "authority_class": "OFFICIAL_VA_GUIDANCE",
        "required_for_answer": required,
    }


def _user_record(required=True):
    return {
        "source_id": "user-record-1",
        "source_type": "user_record",
        "uri": "stegverse-user-record://session/record-1",
        "privacy_status": "PASS",
        "consent_present": True,
        "content_hash": "a" * 64,
        "required_for_answer": required,
    }


def test_ecosystem_session_defaults_to_full_llm_surface():
    result = prepare_session(
        {
            "profile_id": "ecosystem-chat-llm",
            "messages": _messages(),
            "requires_factual_grounding": False,
        }
    )

    assert result.state == "READY_FOR_PROVIDER_BINDING"
    assert result.envelope is not None
    assert set(result.envelope["requested_features"]) == set(FULL_LLM_FEATURES)
    assert result.receipt["declared_profile_feature_count"] == len(FULL_LLM_FEATURES)
    assert result.envelope["provider_call_performed"] is False
    assert result.envelope["authority_effect"] is False


def test_ecosystem_session_accepts_admitted_general_grounding():
    result = prepare_session(
        {
            "profile_id": "ecosystem-chat-llm",
            "messages": _messages(),
            "sources": [
                {
                    "source_id": "general-1",
                    "source_type": "general_web",
                    "uri": "https://example.org/reference",
                    "admitted": True,
                    "required_for_answer": True,
                }
            ],
            "requires_factual_grounding": True,
        }
    )

    assert result.state == "READY_FOR_PROVIDER_BINDING"
    assert result.envelope["grounding_sources"][0]["source_id"] == "general-1"
    assert result.envelope["grounding_sources"][0]["decision"]["fact_label"] == "admitted_source_fact"


def test_va_session_defaults_to_grounding_required():
    result = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
        }
    )

    assert result.state == "BLOCKED_SOURCE_POLICY"
    assert result.envelope is None
    assert result.blockers == ("factual_grounding_required_but_no_allowed_source",)
    assert result.receipt["provider_call_performed"] is False


def test_va_session_accepts_official_va_grounding():
    result = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
            "sources": [_official_va_source()],
        }
    )

    assert result.state == "READY_FOR_PROVIDER_BINDING"
    source = result.envelope["grounding_sources"][0]
    assert source["decision"]["status"] == "ALLOW_VA_SOURCE_FACT"
    assert source["decision"]["fact_label"] == "va_source_fact"
    assert source["decision"]["allowed_as_authority"] is True


def test_va_required_non_va_source_blocks_before_provider_envelope():
    result = prepare_session(
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

    assert result.state == "BLOCKED_SOURCE_POLICY"
    assert result.envelope is None
    assert any(reason.startswith("required_source_denied:non-va") for reason in result.blockers)
    assert "factual_grounding_required_but_no_allowed_source" in result.blockers


def test_va_optional_non_va_source_is_retained_as_denied_but_not_grounding():
    result = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
            "sources": [
                _official_va_source(),
                {
                    "source_id": "non-va",
                    "source_type": "general_web",
                    "uri": "https://example.org/claims",
                    "admitted": True,
                    "required_for_answer": False,
                },
            ],
        }
    )

    assert result.state == "READY_FOR_PROVIDER_BINDING"
    assert [source["source_id"] for source in result.envelope["grounding_sources"]] == [
        "va-eligibility"
    ]
    decisions = {source["source_id"]: source for source in result.envelope["source_decisions"]}
    assert decisions["non-va"]["decision"]["status"] == "DENY_SOURCE"


def test_va_session_accepts_privacy_approved_user_record_without_authority():
    result = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
            "sources": [_user_record()],
        }
    )

    assert result.state == "READY_FOR_PROVIDER_BINDING"
    source = result.envelope["grounding_sources"][0]
    assert source["decision"]["fact_label"] == "user_record_fact"
    assert source["decision"]["allowed_as_authority"] is False


def test_va_required_unapproved_user_record_blocks():
    record = _user_record()
    record["privacy_status"] = "REVIEW_REQUIRED"
    result = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
            "sources": [record],
        }
    )

    assert result.state == "BLOCKED_SOURCE_POLICY"
    assert any("user_record_privacy_not_pass" in reason for reason in result.blockers)


def test_requested_feature_subset_is_preserved():
    result = prepare_session(
        {
            "profile_id": "ecosystem-chat-llm",
            "messages": _messages(),
            "requested_features": [
                "multi_turn_conversation",
                "structured_output",
                "artifact_generation",
            ],
            "response_format": "artifact",
            "requires_factual_grounding": False,
        }
    )

    assert result.envelope["requested_features"] == [
        "multi_turn_conversation",
        "structured_output",
        "artifact_generation",
    ]
    assert result.envelope["response_format"] == "artifact"


def test_unsupported_feature_fails_closed():
    with pytest.raises(SessionBindingError, match="unsupported_requested_features"):
        prepare_session(
            {
                "profile_id": "ecosystem-chat-llm",
                "messages": _messages(),
                "requested_features": ["unbounded_autonomous_execution"],
            }
        )


def test_candidate_tools_remain_non_executing():
    result = prepare_session(
        {
            "profile_id": "ecosystem-chat-llm",
            "messages": _messages(),
            "tools": [
                {
                    "name": "search_records",
                    "description": "Search admitted records.",
                    "input_schema": {"type": "object"},
                }
            ],
            "requires_factual_grounding": False,
        }
    )

    tool = result.envelope["candidate_tools"][0]
    assert tool["execution_state"] == "CANDIDATE_ONLY_NOT_EXECUTED"
    assert tool["execution_authority"] is False
    assert result.envelope["tools_executed"] is False


def test_session_hashes_are_deterministic():
    request = {
        "profile_id": "va-claims-chat-llm",
        "messages": _messages(),
        "sources": [_official_va_source()],
    }
    first = prepare_session(deepcopy(request))
    second = prepare_session(deepcopy(request))

    assert first.envelope["request_sha256"] == second.envelope["request_sha256"]
    assert first.envelope["envelope_sha256"] == second.envelope["envelope_sha256"]
    assert first.receipt["receipt_sha256"] == second.receipt["receipt_sha256"]


def test_valid_va_candidate_response_is_accepted():
    prepared = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
            "sources": [_official_va_source()],
            "tools": [
                {
                    "name": "draft_checklist",
                    "description": "Prepare a non-filing checklist candidate.",
                    "input_schema": {"type": "object"},
                }
            ],
        }
    )
    validation = validate_candidate_response(
        prepared.envelope,
        {
            "text": "The cited VA page describes eligibility considerations.",
            "citations": ["va-eligibility"],
            "factual_claims": [
                {
                    "source_id": "va-eligibility",
                    "fact_label": "va_source_fact",
                }
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

    assert validation.state == "ACCEPT_CANDIDATE"
    assert validation.reasons == ()
    assert validation.receipt["provider_output_is_authority"] is False
    assert validation.receipt["tools_executed"] is False


def test_candidate_with_unknown_citation_is_rejected():
    prepared = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
            "sources": [_official_va_source()],
        }
    )
    validation = validate_candidate_response(
        prepared.envelope,
        {
            "text": "Unsupported claim.",
            "citations": ["unknown"],
            "factual_claims": [],
            "tool_calls": [],
            "side_effects_executed": False,
            "authority_claimed": False,
        },
    )

    assert validation.state == "REJECT_CANDIDATE"
    assert validation.reasons == ("unknown_citations:unknown",)


def test_candidate_with_wrong_fact_label_is_rejected():
    prepared = prepare_session(
        {
            "profile_id": "va-claims-chat-llm",
            "messages": _messages(),
            "sources": [_official_va_source()],
        }
    )
    validation = validate_candidate_response(
        prepared.envelope,
        {
            "text": "Claim.",
            "citations": ["va-eligibility"],
            "factual_claims": [
                {
                    "source_id": "va-eligibility",
                    "fact_label": "user_record_fact",
                }
            ],
            "tool_calls": [],
            "side_effects_executed": False,
            "authority_claimed": False,
        },
    )

    assert validation.state == "REJECT_CANDIDATE"
    assert validation.reasons == ("factual_claim_0_fact_label_mismatch",)


def test_candidate_claiming_tool_execution_or_side_effect_is_rejected():
    prepared = prepare_session(
        {
            "profile_id": "ecosystem-chat-llm",
            "messages": _messages(),
            "tools": [
                {
                    "name": "publish",
                    "description": "Produce a publication candidate.",
                    "input_schema": {"type": "object"},
                }
            ],
            "requires_factual_grounding": False,
        }
    )
    validation = validate_candidate_response(
        prepared.envelope,
        {
            "text": "Done.",
            "citations": [],
            "factual_claims": [],
            "tool_calls": [{"name": "publish", "status": "EXECUTED"}],
            "side_effects_executed": True,
            "authority_claimed": True,
            "publication_claimed": True,
        },
    )

    assert validation.state == "REJECT_CANDIDATE"
    assert set(validation.reasons) == {
        "tool_call_0_execution_status_invalid",
        "side_effects_must_remain_false",
        "authority_claimed_must_remain_false",
        "publication_claim_not_allowed",
    }


def test_unknown_profile_and_missing_user_message_fail():
    with pytest.raises(SessionBindingError, match="unknown_profile_id"):
        prepare_session({"profile_id": "other", "messages": _messages()})

    with pytest.raises(SessionBindingError, match="at_least_one_user_message_required"):
        prepare_session(
            {
                "profile_id": "ecosystem-chat-llm",
                "messages": [{"role": "system", "content": "Only system."}],
            }
        )
