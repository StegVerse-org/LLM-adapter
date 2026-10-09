import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_cosv_task_projection.py"
SPEC = importlib.util.spec_from_file_location("check_cosv_task_projection", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)
TASK_306 = "data/cosv/task-vectors/LLMA-EXTERNAL-LLM-CONVERGENCE-306.json"
TASK_007 = "data/cosv/task-vectors/LLMA-ECOSYSTEM-CHAT-DESTINATION-PROJECTION-007.json"


class TestLLMACOSV(unittest.TestCase):
    def test_projection(self):
        cp = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("LLMA_COSV_TASK_PROJECTION_PASS", cp.stdout)

    def copy(self) -> Path:
        tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for rel in ("data/cosv", "tasks"):
            shutil.copytree(ROOT / rel, tmp / rel)
        return tmp

    def mutate(self, root: Path, rel: str, change) -> None:
        path = root / rel
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))

    def test_non_terminal_task_is_not_held_to_terminal_claims(self):
        record = json.loads((ROOT / TASK_306).read_text())
        self.assertNotEqual(record["exact_metrics"]["lifecycle"], "COMPLETE")
        self.assertEqual(CHECKER.check(ROOT)[0], [])

    def test_non_terminal_task_cannot_claim_archive_ready_or_complete_evidence(self):
        root = self.copy()
        self.mutate(root, TASK_306, lambda v: v["exact_metrics"].update(archive_ready=True, evidence_complete=True))
        errors, _ = CHECKER.check(root)
        self.assertIn("LLMA-EXTERNAL-LLM-CONVERGENCE-306:non_terminal_task_claims_archive_ready", errors)
        self.assertIn("LLMA-EXTERNAL-LLM-CONVERGENCE-306:non_terminal_task_claims_evidence_complete", errors)

    def test_terminal_task_must_be_archive_ready_and_evidence_complete(self):
        root = self.copy()
        self.mutate(root, TASK_007, lambda v: v["exact_metrics"].update(archive_ready=False, evidence_complete=False, blocker_count=1))
        errors, _ = CHECKER.check(root)
        for code in ("terminal_task_not_archive_ready", "terminal_task_evidence_incomplete", "terminal_task_has_blockers"):
            self.assertIn("LLMA-ECOSYSTEM-CHAT-DESTINATION-PROJECTION-007:" + code, errors)

    def test_activation_cannot_be_claimed_without_complete_evidence(self):
        root = self.copy()
        self.mutate(root, TASK_306, lambda v: v["exact_metrics"].update(activated=True))
        errors, _ = CHECKER.check(root)
        self.assertIn("LLMA-EXTERNAL-LLM-CONVERGENCE-306:activated_claimed_without_complete_evidence", errors)

    def test_repository_vector_claim_must_match_the_index(self):
        root = self.copy()
        self.mutate(root, "data/cosv/task-vector-index.json",
                    lambda v: v["coverage"].update(repository_vector_present_claimed=True))
        self.assertIn("repository_vector_present_claimed_does_not_match_index", CHECKER.check(root)[0])
        (root / "data/cosv/repository-vector.json").write_text("{}")
        self.mutate(root, "data/cosv/task-vector-index.json",
                    lambda v: v.update(repository_vector_ref="data/cosv/repository-vector.json"))
        self.assertNotIn("repository_vector_present_claimed_does_not_match_index", CHECKER.check(root)[0])

    def test_task_306_names_no_master_records_predicate(self):
        task = json.loads((ROOT / "tasks/LLMA-EXTERNAL-LLM-CONVERGENCE-306.json").read_text())
        self.assertNotIn("custody_reconstruction", task["authority"])
        self.assertNotIn("custody/reconstruction", task["next_executable_action"])
        non_allow = task["non_allow"]
        for key in ("failure_code", "failed_predicate", "required_evidence_or_repair",
                    "retry_entrypoint", "owning_existing_goal", "next_attempt"):
            self.assertTrue(non_allow[key], key)


if __name__ == "__main__":
    unittest.main()
