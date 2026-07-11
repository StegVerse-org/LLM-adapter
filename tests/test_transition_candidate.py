from __future__ import annotations

import unittest

from llm_adapter.transition_candidate import emit_llm_transition_candidate


class LLMTransitionCandidateTests(unittest.TestCase):
    def test_emits_declared_non_authorizing_candidate(self) -> None:
        record = emit_llm_transition_candidate(
            transition_id="transition.llm.test",
            run_id="run-llm-test",
            event_id="event-llm-test",
            actor_ref="actor:test",
            target_ref="bridge:hybrid-collab",
            repository_ref="StegVerse-org/LLM-adapter",
        )
        self.assertEqual(record["origin"]["origin_class"], "LLM_ADAPTER_INPUT")
        self.assertEqual(record["lifecycle_state"], "DECLARED")
        self.assertEqual(record["governance"]["admissibility_result"], "PENDING")
        self.assertIsNone(record["execution"]["action_ref"])
        self.assertIsNone(record["continuity"]["final_receipt_id"])


if __name__ == "__main__":
    unittest.main()
