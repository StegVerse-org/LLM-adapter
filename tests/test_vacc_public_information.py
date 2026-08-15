from __future__ import annotations

import unittest

from llm_adapter.vacc_public_information import (
    VACCSourceCandidate,
    evaluate_public_source,
    load_profile,
    validate_profile,
)


class VACCPublicInformationTests(unittest.TestCase):
    def test_profile_preserves_claims_boundary_and_tv_tvc_credentials(self) -> None:
        profile = load_profile()
        validate_profile(profile)
        self.assertTrue(profile["claims_profile_boundary"]["existing_official_va_only_policy_unchanged"])
        self.assertEqual(profile["credential_policy"]["credential_authority"], "TV/TVC")
        self.assertFalse(profile["credential_policy"]["non_tv_tvc_secret_or_token_required"])
        self.assertEqual(profile["credential_policy"]["github_token_runtime_authority"], "NONE")

    def test_va_gov_operational_source_is_allowed(self) -> None:
        decision = evaluate_public_source(VACCSourceCandidate(
            source_id="VA-FORMS",
            url="https://www.va.gov/find-forms/",
            authority_class="OFFICIAL_OPERATIONAL",
            admitted=True,
            public=True,
            freshness_required=True,
            freshness_verified=True,
        ))
        self.assertEqual(decision.state, "ALLOW_PUBLIC_GROUNDING")
        self.assertTrue(decision.allowed_as_government_authority)

    def test_title_38_ecfr_is_allowed_as_controlling(self) -> None:
        decision = evaluate_public_source(VACCSourceCandidate(
            source_id="ECFR-TITLE-38",
            url="https://www.ecfr.gov/current/title-38",
            authority_class="CONTROLLING",
            admitted=True,
            public=True,
            freshness_required=True,
            freshness_verified=True,
        ))
        self.assertTrue(decision.allowed_for_grounding)
        self.assertTrue(decision.allowed_as_government_authority)

    def test_unadmitted_general_web_source_fails_closed(self) -> None:
        decision = evaluate_public_source(VACCSourceCandidate(
            source_id="BLOG-1",
            url="https://example.com/veterans-advice",
            authority_class="EXPERIENTIAL",
            admitted=False,
            public=True,
        ))
        self.assertEqual(decision.state, "DENY_SOURCE")
        self.assertIn("source_not_admitted", decision.reasons)
        self.assertIn("host_not_in_vacc_public_allowlist", decision.reasons)

    def test_private_vawatchdog_content_is_not_automatically_public(self) -> None:
        decision = evaluate_public_source(VACCSourceCandidate(
            source_id="VAW-PRIVATE-OBSERVATION",
            url="https://github.com/StegVerse-Labs/VAwatchdog",
            authority_class="EXPERIENTIAL",
            admitted=True,
            public=False,
        ))
        self.assertFalse(decision.allowed_for_grounding)
        self.assertIn("source_not_public", decision.reasons)
        self.assertIn("private_vawatchdog_requires_sanitized_public_projection", decision.reasons)

    def test_sanitized_vawatchdog_projection_can_be_grounding_but_not_government_authority(self) -> None:
        decision = evaluate_public_source(VACCSourceCandidate(
            source_id="VAW-PUBLIC-SANITIZED-001",
            url="stegverse://public/vawatchdog/VAW-PUBLIC-SANITIZED-001",
            authority_class="EXPERIENTIAL",
            admitted=True,
            public=True,
            sanitized_public_projection=True,
        ))
        self.assertTrue(decision.allowed_for_grounding)
        self.assertFalse(decision.allowed_as_government_authority)


if __name__ == "__main__":
    unittest.main()
