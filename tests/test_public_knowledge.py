from __future__ import annotations

import unittest

from llm_adapter.ai_entry_backend_service import build_ai_entry_backend_response
from llm_adapter.public_knowledge import load_manifest, resolve_public_question, validate_manifest


class PublicKnowledgeTests(unittest.TestCase):
    def test_manifest_is_public_non_authorizing_and_valid(self) -> None:
        manifest = load_manifest()
        validate_manifest(manifest)
        self.assertFalse(manifest["authority_effect"])
        self.assertFalse(manifest["publication_authority"])
        self.assertFalse(manifest["model_memory_is_source"])
        self.assertTrue(all(source["public"] for source in manifest["sources"]))

    def test_connect_my_llm_returns_exact_adapter_procedure(self) -> None:
        answer = resolve_public_question("How do I connect my LLM?")
        self.assertIsNotNone(answer)
        assert answer is not None
        self.assertEqual(answer.entry_id, "connect-my-llm")
        self.assertIn("stegverse-connect-llm", answer.answer)
        self.assertIn("/v1/user-llm/requests", answer.answer)
        self.assertFalse(answer.to_dict()["model_memory_used_as_source"])

    def test_mode_help_is_grounded(self) -> None:
        answer = resolve_public_question("What is mode 1 and how do I replay a receipt?")
        self.assertIsNotNone(answer)
        assert answer is not None
        self.assertEqual(answer.entry_id, "governance-replay")
        self.assertIn("--manifest-receipt-id", answer.answer)

    def test_unknown_public_question_does_not_invent(self) -> None:
        self.assertIsNone(resolve_public_question("Tell me the launch date of an unindexed imaginary StegVerse feature ZXQ-991"))
        response = build_ai_entry_backend_response("Tell me the launch date of an unindexed imaginary StegVerse feature ZXQ-991")
        self.assertIn("does not invent an answer", response.stegverse_response)
        self.assertFalse(response.governance["authority_issued"])

    def test_ecosystem_backend_uses_grounded_answer_and_source_refs(self) -> None:
        response = build_ai_entry_backend_response("How do I connect my LLM?")
        self.assertEqual(response.primary_route, "public_knowledge")
        self.assertIn("stegverse-connect-llm", response.stegverse_response)
        self.assertIn("StegVerse-org/StegVerse-SDK/docs/CONNECT_MY_LLM.md", response.route_guidance)
        self.assertIn("Model memory is not the factual source", response.route_guidance)
        self.assertFalse(response.activation["provider_output_is_authority"])


if __name__ == "__main__":
    unittest.main()
