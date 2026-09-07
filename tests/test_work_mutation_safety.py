import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.validate_work_mutation_safety import validate_manifest


class WorkMutationSafetyTests(unittest.TestCase):
    def base_manifest(self):
        return {
            "schema": "stegverse.work-mutation-safety/v1",
            "task_id": "TEST-WORK-SAFETY",
            "authority_effect": "NONE_PREFLIGHT_ONLY",
            "canonical_handoff_refs": ["StegVerse-org/LLM-adapter:docs/TEST_MIRROR_HANDOFF.md"],
            "task_registry_refs": ["StegVerse-Labs/.github:data/canonical-task-registry.json"],
            "master_records_review": {"applicable": False, "reason": "unit test"},
            "cross_task_coordination": {"checked": True, "refs": ["StegVerse-Labs/.github:control/cross-task-coordination.json"]},
            "semantic_scan": {
                "completed": True,
                "repositories_searched": ["StegVerse-org/LLM-adapter"],
                "evidence_refs": ["tests/test_work_mutation_safety.py"],
            },
            "reuse_decision": "EXTEND",
            "existing_equivalent_found": True,
            "active_owner_collision": {"checked": True, "collision_found": False},
            "readme_impact": {
                "material_function_change": False,
                "no_readme_update_reason": "unit test only",
                "evidence_refs": ["tests/test_work_mutation_safety.py"],
            },
            "covered_paths": ["x.py"],
            "new_files": [],
        }

    def run_validation(self, data, changed=None):
        changed = changed or {"x.py"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "TEST_MIRROR_HANDOFF.md").write_text("test\n", encoding="utf-8")
            receipt = root / "receipt.json"
            receipt.write_text(json.dumps(data), encoding="utf-8")
            old = Path.cwd()
            try:
                os.chdir(root)
                return validate_manifest(receipt, repository="StegVerse-org/LLM-adapter", changed=changed)
            finally:
                os.chdir(old)

    def test_extend_existing_is_admissible(self):
        result = self.run_validation(self.base_manifest())
        self.assertEqual(result["reuse_decision"], "EXTEND")

    def test_create_new_is_blocked_when_equivalent_exists(self):
        data = self.base_manifest()
        data["reuse_decision"] = "CREATE_NEW"
        with self.assertRaisesRegex(ValueError, "CREATE_NEW forbidden"):
            self.run_validation(data)

    def test_active_owner_collision_blocks_unreconciled_create_new(self):
        data = self.base_manifest()
        data["existing_equivalent_found"] = False
        data["reuse_decision"] = "CREATE_NEW"
        data["active_owner_collision"] = {"checked": True, "collision_found": True}
        with self.assertRaisesRegex(ValueError, "active-owner collision"):
            self.run_validation(data)

    def test_material_change_requires_readme_in_same_change_set(self):
        data = self.base_manifest()
        data["readme_impact"] = {
            "material_function_change": True,
            "readme_updated_in_change_set": True,
            "readme_path": "README.md",
            "evidence_refs": ["x.py"],
        }
        with self.assertRaisesRegex(ValueError, "README update"):
            self.run_validation(data, changed={"x.py"})

    def test_local_handoff_must_exist(self):
        data = self.base_manifest()
        data["canonical_handoff_refs"] = ["StegVerse-org/LLM-adapter:docs/MISSING_MIRROR_HANDOFF.md"]
        with self.assertRaisesRegex(ValueError, "MIRROR_HANDOFF"):
            self.run_validation(data)


if __name__ == "__main__":
    unittest.main()
