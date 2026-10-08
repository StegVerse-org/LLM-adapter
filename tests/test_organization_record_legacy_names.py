import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_stegverse_live_baseline_runtime_readiness.py"
ORGANIZATION_RECORD = "Master Records organization record"


def _load():
    spec = importlib.util.spec_from_file_location("live_baseline_readiness_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_with(tmp_path, monkeypatch, prerequisites_key):
    module = _load()
    readiness = json.loads(module.READINESS.read_text(encoding="utf-8"))
    required = readiness["prerequisites"]
    value = required.pop("master_records_organization_record_acceptance")
    required[prerequisites_key] = value
    path = tmp_path / "readiness.json"
    path.write_text(json.dumps(readiness), encoding="utf-8")
    monkeypatch.setattr(module, "READINESS", path)
    return module.main()


def test_organization_record_prerequisite_name_is_accepted(tmp_path, monkeypatch):
    assert _run_with(tmp_path, monkeypatch, "master_records_organization_record_acceptance") == 0


def test_legacy_prerequisite_name_is_accepted(tmp_path, monkeypatch):
    assert _run_with(tmp_path, monkeypatch, "master_records_custody_acceptance") == 0


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sovereign_task_with_gate(tmp_path, name):
    task = json.loads((ROOT / "tasks" / "VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json").read_text(encoding="utf-8"))
    kept = [item for item in task["preserved_vacc_gates"] if item != ORGANIZATION_RECORD]
    task["preserved_vacc_gates"] = kept + [name]
    path = tmp_path / "sovereign-task.json"
    path.write_text(json.dumps(task), encoding="utf-8")
    return path


def test_ecosystem_consolidation_accepts_both_organization_record_gate_names(tmp_path, monkeypatch):
    module = _load_script("validate_ecosystem_va_chat_session_consolidation")
    for name in (ORGANIZATION_RECORD, module.LEGACY_ORGANIZATION_RECORD_REQUIREMENT):
        monkeypatch.setattr(module, "SOVEREIGN_VA_PROVIDER_TASK", _sovereign_task_with_gate(tmp_path, name))
        _legacy, sovereign = module.validate_provider_continuation()
        assert name in sovereign["preserved_vacc_gates"]


def test_va_session_consolidation_accepts_both_organization_record_gate_names():
    module = _load_script("validate_va_claim_assistant_session_consolidation")
    assert module.organization_record_requirement_present({ORGANIZATION_RECORD})
    assert module.organization_record_requirement_present({module.LEGACY_ORGANIZATION_RECORD_REQUIREMENT})
    assert module.LEGACY_ORGANIZATION_RECORD_REQUIREMENT == "Master Records custody"
    assert not module.organization_record_requirement_present({"privacy guarded dispatch before model input"})


def test_orchestration_state_accepts_both_blocker_names():
    module = _load_script("check_llm_adapter_orchestration_state")
    assert module.external_blockers_valid(sorted(module.BLOCKERS))
    assert module.external_blockers_valid(sorted(module.LEGACY_BLOCKERS))
    assert not module.external_blockers_valid(["persistent endpoint"])


def test_provider_authority_binding_accepts_record_owner_and_legacy_custody_owner():
    module = _load_script("check_stegverse_live_baseline_provider_authority_binding")
    assert module.RECORD_OWNER_FIELD == "record_owner"
    assert module.LEGACY_RECORD_OWNER_FIELD == "custody_owner"
    binding = json.loads(module.BINDING.read_text(encoding="utf-8"))
    path_block = binding["provider_authority_path"]
    assert path_block["record_owner"] == "master-records/orchestration"
    assert "custody_owner" not in path_block
    assert module.main() == 0
    assert module.record_owner({"record_owner": "master-records/orchestration"}) == "master-records/orchestration"
    assert module.record_owner({"custody_owner": "master-records/orchestration"}) == "master-records/orchestration"
    assert module.record_owner({"record_owner": "x/y", "custody_owner": "master-records/orchestration"}) == "x/y"
    assert module.record_owner({}) is None
