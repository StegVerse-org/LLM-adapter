import copy
import json
from pathlib import Path
import unittest

from llm_adapter.chat_specialties import SpecialtyValidationError, load_specialty, validate_specialty_manifest

ROOT = Path(__file__).resolve().parents[1]


class ChatSpecialtyProfilesTests(unittest.TestCase):
    def load_json(self, relative: str):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_vacc_and_math_share_canonical_llm(self):
        vacc = load_specialty(ROOT / "profiles/vacc-specialty.v1.json")
        math = load_specialty(ROOT / "profiles/math-educator-specialty.v1.json")
        self.assertEqual(vacc.base_llm_profile, "ecosystem-chat-llm")
        self.assertEqual(math.base_llm_profile, "ecosystem-chat-llm")
        self.assertTrue(vacc.inherits_full_llm_surface)
        self.assertTrue(math.inherits_full_llm_surface)

    def test_math_preserves_image_and_transcription_as_distinct_states(self):
        math = load_specialty(ROOT / "profiles/math-educator-specialty.v1.json")
        self.assertEqual(math.context_policy["source_image_state"], "source_image")
        self.assertEqual(math.context_policy["interpreted_transcription_state"], "interpreted_mathematical_transcription")
        self.assertNotEqual(math.context_policy["source_image_state"], math.context_policy["interpreted_transcription_state"])
        self.assertFalse(math.context_policy["transcription_is_source_fact"])

    def test_candidate_tools_have_no_execution_authority(self):
        for path in ("profiles/vacc-specialty.v1.json", "profiles/math-educator-specialty.v1.json"):
            specialty = load_specialty(ROOT / path)
            for tool in specialty.candidate_tools:
                self.assertFalse(tool["execution_authority"])
                self.assertEqual(tool["execution_state"], "CANDIDATE_ONLY_NOT_EXECUTED")

    def test_second_provider_runtime_is_rejected(self):
        manifest = self.load_json("profiles/math-educator-specialty.v1.json")
        manifest["authority_policy"]["provider_runtime_is_duplicated"] = True
        with self.assertRaisesRegex(SpecialtyValidationError, "provider_runtime_is_duplicated"):
            validate_specialty_manifest(manifest)

    def test_reduced_llm_surface_is_rejected(self):
        manifest = self.load_json("profiles/vacc-specialty.v1.json")
        manifest["inherits_full_llm_surface"] = False
        with self.assertRaisesRegex(SpecialtyValidationError, "inherit_full_llm_surface"):
            validate_specialty_manifest(manifest)

    def test_math_transcription_cannot_be_promoted_to_source_fact(self):
        manifest = copy.deepcopy(self.load_json("profiles/math-educator-specialty.v1.json"))
        manifest["context_policy"]["transcription_is_source_fact"] = True
        with self.assertRaisesRegex(SpecialtyValidationError, "remain_interpretation"):
            validate_specialty_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
