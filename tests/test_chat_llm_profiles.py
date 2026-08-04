import json
from pathlib import Path

import pytest

from llm_adapter.chat_profiles import (
    FULL_LLM_FEATURES,
    ProfileValidationError,
    SourceCandidate,
    capability_matrix,
    evaluate_source,
    is_official_va_host,
    load_profile,
    validate_parallel_profiles,
    validate_profile_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
ECOSYSTEM_PATH = ROOT / "profiles" / "ecosystem-chat-llm.v1.json"
CLAIMS_PATH = ROOT / "profiles" / "va-claims-chat-llm.v1.json"


def _load_raw(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_profiles_expose_identical_full_llm_surface():
    ecosystem, claims = validate_parallel_profiles(
        _load_raw(ECOSYSTEM_PATH),
        _load_raw(CLAIMS_PATH),
    )

    assert ecosystem.has_full_llm_surface is True
    assert claims.has_full_llm_surface is True
    assert set(ecosystem.features) == set(FULL_LLM_FEATURES)
    assert set(claims.features) == set(FULL_LLM_FEATURES)

    matrix = capability_matrix((ecosystem, claims))
    assert all(matrix[ecosystem.profile_id].values())
    assert all(matrix[claims.profile_id].values())


def test_missing_llm_feature_fails_profile_validation():
    manifest = _load_raw(ECOSYSTEM_PATH)
    manifest["features"].remove("tool_candidate_generation") if "tool_candidate_generation" in manifest["features"] else manifest["features"].remove("candidate_action_generation")

    with pytest.raises(ProfileValidationError, match="full_llm_surface_missing"):
        validate_profile_manifest(manifest)


def test_ecosystem_chat_allows_admitted_general_source():
    profile = load_profile(ECOSYSTEM_PATH)
    decision = evaluate_source(
        profile,
        SourceCandidate(
            source_type="general_web",
            uri="https://example.org/reference",
            admitted=True,
        ),
    )

    assert decision.status == "ALLOW_ADMITTED_SOURCE"
    assert decision.allowed_for_factual_grounding is True
    assert decision.allowed_as_authority is False


def test_ecosystem_chat_still_requires_source_admission():
    profile = load_profile(ECOSYSTEM_PATH)
    decision = evaluate_source(
        profile,
        SourceCandidate(
            source_type="general_web",
            uri="https://example.org/reference",
            admitted=False,
        ),
    )

    assert decision.status == "DENY_SOURCE"
    assert decision.reasons == ("source_not_admitted",)


def test_va_claims_chat_allows_admitted_official_va_source():
    profile = load_profile(CLAIMS_PATH)
    decision = evaluate_source(
        profile,
        SourceCandidate(
            source_type="official_external",
            uri="https://www.va.gov/disability/eligibility/",
            admitted=True,
            authority_class="OFFICIAL_VA_GUIDANCE",
        ),
    )

    assert decision.status == "ALLOW_VA_SOURCE_FACT"
    assert decision.allowed_for_factual_grounding is True
    assert decision.allowed_as_authority is True
    assert decision.fact_label == "va_source_fact"
    assert decision.normalized_host == "www.va.gov"


@pytest.mark.parametrize(
    "uri",
    [
        "https://va.gov.evil.example/claims",
        "https://notva.gov/claims",
        "https://va-gov.example/claims",
        "https://example.org/?next=https://va.gov/claims",
        "https://vagov.example/claims",
    ],
)
def test_va_claims_chat_rejects_va_lookalike_hosts(uri):
    profile = load_profile(CLAIMS_PATH)
    decision = evaluate_source(
        profile,
        SourceCandidate(
            source_type="official_external",
            uri=uri,
            admitted=True,
        ),
    )

    assert decision.status == "DENY_SOURCE"
    assert decision.reasons == ("external_source_not_official_va",)


def test_va_host_validation_accepts_only_va_gov_boundary():
    assert is_official_va_host("va.gov") is True
    assert is_official_va_host("benefits.va.gov") is True
    assert is_official_va_host("https://www.va.gov/path") is True
    assert is_official_va_host("va.gov.example.org") is False
    assert is_official_va_host("notva.gov") is False


def test_va_claims_chat_rejects_general_web_even_when_admitted():
    profile = load_profile(CLAIMS_PATH)
    decision = evaluate_source(
        profile,
        SourceCandidate(
            source_type="general_web",
            uri="https://www.va.gov/disability/",
            admitted=True,
        ),
    )

    assert decision.status == "DENY_SOURCE"
    assert decision.reasons == (
        "va_claims_external_source_must_be_official",
    )


def test_va_claims_chat_rejects_model_memory_as_factual_source():
    profile = load_profile(CLAIMS_PATH)
    decision = evaluate_source(
        profile,
        SourceCandidate(source_type="model_memory"),
    )

    assert decision.status == "DENY_SOURCE"
    assert decision.allowed_for_factual_grounding is False
    assert decision.reasons == ("model_memory_not_a_factual_source",)


def test_va_claims_chat_accepts_privacy_approved_user_record_fact_without_authority():
    profile = load_profile(CLAIMS_PATH)
    decision = evaluate_source(
        profile,
        SourceCandidate(
            source_type="user_record",
            uri="stegverse-user-record://session/record-1",
            privacy_status="PASS",
            consent_present=True,
            content_hash="a" * 64,
        ),
    )

    assert decision.status == "ALLOW_USER_RECORD_FACT"
    assert decision.allowed_for_factual_grounding is True
    assert decision.allowed_as_authority is False
    assert decision.fact_label == "user_record_fact"


def test_va_claims_chat_rejects_unapproved_user_record():
    profile = load_profile(CLAIMS_PATH)
    decision = evaluate_source(
        profile,
        SourceCandidate(
            source_type="user_record",
            privacy_status="REVIEW_REQUIRED",
            consent_present=False,
            content_hash="",
        ),
    )

    assert decision.status == "DENY_SOURCE"
    assert set(decision.reasons) == {
        "user_record_privacy_not_pass",
        "user_record_consent_missing",
        "user_record_hash_missing",
    }


def test_profiles_never_grant_consequence_authority():
    for path in (ECOSYSTEM_PATH, CLAIMS_PATH):
        profile = load_profile(path)
        assert profile.authority_policy
        assert all(value is False for value in profile.authority_policy.values())
