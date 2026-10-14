import importlib.util
import json
import shutil
import tempfile
import types
import unittest
from unittest import mock

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_stegverse_live_baseline_runtime_readiness.py"


def _load():
    spec = importlib.util.spec_from_file_location("live_baseline_readiness_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_with(tmp_path, monkeypatch, master_records_key, value):
    module = _load()
    readiness = json.loads(module.READINESS.read_text(encoding="utf-8"))
    readiness["prerequisites"][master_records_key] = value
    path = tmp_path / "readiness.json"
    path.write_text(json.dumps(readiness), encoding="utf-8")
    monkeypatch.setattr(module, "READINESS", path)
    return module.main()


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sovereign_task_with_gate(tmp_path, name):
    task = json.loads((ROOT / "tasks" / "VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json").read_text(encoding="utf-8"))
    task["preserved_vacc_gates"] = list(task["preserved_vacc_gates"]) + [name]
    path = tmp_path / "sovereign-task.json"
    path.write_text(json.dumps(task), encoding="utf-8")
    return path


class OrganizationRecordLegacyNamesTests(unittest.TestCase):
    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _monkeypatch(self):
        """The monkeypatch methods the module helpers call, each undone after the test."""
        return types.SimpleNamespace(setattr=self._setattr)

    def test_master_records_is_not_a_runtime_prerequisite(self):
        module = _load()
        assert not any("master_records" in key for key in module.RUNTIME_PREREQUISITES)
        assert "organization_ledger_transition_receipt_append" in module.RUNTIME_PREREQUISITES

    def test_master_records_prerequisite_keys_are_read_but_never_gate(self):
        tmp_path = self._tmp_path()
        monkeypatch = self._monkeypatch()
        for key in ("master_records_organization_record_acceptance", "master_records_custody_acceptance"):
            for value in (True, False):
                assert _run_with(tmp_path, monkeypatch, key, value) == 0

    def test_ecosystem_consolidation_requires_ledger_gate_and_refuses_master_records_gates(self):
        tmp_path = self._tmp_path()
        module = _load_script("validate_ecosystem_va_chat_session_consolidation")
        _legacy, sovereign = module.validate_provider_continuation()
        assert module.ORGANIZATION_LEDGER_GATE in sovereign["preserved_vacc_gates"]
        for name in sorted(module.RETIRED_MASTER_RECORDS_GATES):
            self._setattr(module, "SOVEREIGN_VA_PROVIDER_TASK", _sovereign_task_with_gate(tmp_path, name))
            with self.assertRaisesRegex(SystemExit, "master_records_cannot_be_a_vacc_gate"):
                module.validate_provider_continuation()

    def test_va_session_consolidation_requires_ledger_gate_and_refuses_master_records_gates(self):
        module = _load_script("validate_va_claim_assistant_session_consolidation")
        assert module.organization_record_requirement_present({module.ORGANIZATION_LEDGER_GATE})
        for retired in module.RETIRED_MASTER_RECORDS_GATES:
            assert not module.organization_record_requirement_present({retired})
            assert not module.organization_record_requirement_present({module.ORGANIZATION_LEDGER_GATE, retired})
        assert module.LEGACY_ORGANIZATION_RECORD_REQUIREMENT == "Master Records custody"
        assert not module.organization_record_requirement_present({"privacy guarded dispatch before model input"})

    def test_orchestration_state_rejects_master_records_as_a_blocker(self):
        module = _load_script("check_llm_adapter_orchestration_state")
        assert module.external_blockers_valid(sorted(module.BLOCKERS))
        for retired in module.RETIRED_MASTER_RECORDS_BLOCKERS:
            assert not module.external_blockers_valid(sorted(module.BLOCKERS | {retired}))
        assert not module.external_blockers_valid(["persistent endpoint"])

    def test_provider_authority_binding_accepts_record_owner_and_legacy_custody_owner(self):
        module = _load_script("check_stegverse_live_baseline_provider_authority_binding")
        assert module.RECORD_OWNER_FIELD == "record_owner"
        assert module.LEGACY_RECORD_OWNER_FIELD == "custody_owner"
        binding = json.loads(module.BINDING.read_text(encoding="utf-8"))
        path_block = binding["provider_authority_path"]
        assert path_block["record_owner"] == module.ORGANIZATION_RECORD_OWNER
        assert path_block["downstream_recorder"] == "master-records/orchestration"
        assert path_block["downstream_recorder_gates_dispatch"] is False
        assert "custody_owner" not in path_block
        assert binding["custody_binding"]["master_records_gates_dispatch"] is False
        assert not any("Master Records" in item for item in binding["required_before_dispatch"])
        assert not any("Master Records" in item for item in binding["runtime_preconditions_before_authority_consumption"])
        assert module.main() == 0
        assert module.record_owner({"record_owner": "master-records/orchestration"}) == "master-records/orchestration"
        assert module.record_owner({"custody_owner": "master-records/orchestration"}) == "master-records/orchestration"
        assert module.record_owner({"record_owner": "x/y", "custody_owner": "master-records/orchestration"}) == "x/y"
        assert module.record_owner({}) is None


if __name__ == "__main__":
    unittest.main()
