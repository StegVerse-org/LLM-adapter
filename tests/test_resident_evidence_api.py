from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from llm_adapter.resident_evidence_api import (
    EVIDENCE_SCHEMA,
    FETCH_SCHEMA,
    PROOF_SCHEMA,
    STORE_SCHEMA,
    ResidentEvidenceError,
    fetch_evidence,
    sha256_uri,
    store_evidence,
)


class ResidentEvidenceApiTests(unittest.TestCase):
    def proof(self):
        return {
            "schema": PROOF_SCHEMA,
            "state": "PASS",
            "execution_surface": "CURRENT_USER_IPHONE",
            "source_receipt_sha256": "sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35",
            "intr_governance_admission_observed": True,
            "intr_admission_receipt_sha256": "sha256:" + "1" * 64,
            "intr_admission_journal_entry_sha256": "2" * 64,
            "custody_hash": "sha256:" + "3" * 64,
            "reconstruction_hash": "sha256:" + "4" * 64,
            "reconstruction_state": "PASS",
            "custody_journal_entry_sha256": "5" * 64,
            "reconstruction_journal_entry_sha256": "6" * 64,
            "final_replay_tail_sha256": "7" * 64,
            "canonical_owner": "master-records/orchestration",
            "site_custody_authority": False,
            "site_execution_authority": False,
            "heartbeat_granted_authority": False,
            "human_approval_checkpoint_inserted": False,
            "prior_receipt_authorizes_transition": False,
            "historical_state_retroactively_authorized": False,
        }

    def envelope(self):
        proof = self.proof()
        return {
            "schema": EVIDENCE_SCHEMA,
            "target_node_ref": "SV-NODE-" + "a" * 24,
            "proof": proof,
            "proof_sha256": sha256_uri(proof),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "gateway_execution_authority": "NONE",
            "evidence_grants_authority": False,
            "authority_effect": "NONE_EVIDENCE_ONLY",
        }

    def test_store_then_fetch_preserves_non_authorizing_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stored = store_evidence(self.envelope(), root=root)
            self.assertEqual(stored["schema"], STORE_SCHEMA)
            self.assertEqual(stored["state"], "RETAINED")
            self.assertEqual(stored["gateway_execution_authority"], "NONE")
            fetched = fetch_evidence("SV-NODE-" + "a" * 24, root=root)
            self.assertEqual(fetched["schema"], FETCH_SCHEMA)
            self.assertEqual(fetched["state"], "EVIDENCE_AVAILABLE")
            self.assertEqual(fetched["evidence"]["proof"]["reconstruction_state"], "PASS")
            self.assertFalse(fetched["evidence_grants_authority"])

    def test_conflicting_proof_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.envelope()
            store_evidence(first, root=root)
            second = self.envelope()
            second["proof"]["custody_hash"] = "sha256:" + "8" * 64
            second["proof_sha256"] = sha256_uri(second["proof"])
            with self.assertRaisesRegex(ResidentEvidenceError, "conflicting custody proof"):
                store_evidence(second, root=root)

    def test_authority_escalation_is_rejected(self):
        value = self.envelope()
        value["evidence_grants_authority"] = True
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ResidentEvidenceError, "may not grant authority"):
                store_evidence(value, root=Path(tmp))


if __name__ == "__main__":
    unittest.main()
