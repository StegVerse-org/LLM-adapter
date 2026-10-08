import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_stegverse_live_baseline_runtime_readiness.py"


def _load():
    spec = importlib.util.spec_from_file_location("live_baseline_readiness_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_with(tmp_path, monkeypatch, prerequisites_key):
    module = _load()
    readiness = json.loads(module.READINESS.read_text(encoding="utf-8"))
    prerequisites = readiness["prerequisites"]
    value = prerequisites.pop("master_records_organization_record_acceptance")
    prerequisites[prerequisites_key] = value
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


def _sovereign_task_with_gate(tmp_path, gate):
    task = json.loads((ROOT / "tasks" / "VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json").read_text(encoding="utf-8"))
    gates = [item for item in task["preserved_vacc_gates"] if item != "Master Records organization record"]
    task["preserved_vacc_gates"] = gates + [gate]
    path = tmp_path / "sovereign-task.json"
    path.write_text(json.dumps(task), encoding="utf-8")
    return path


def test_ecosystem_consolidation_accepts_both_organization_record_gate_names(tmp_path, monkeypatch):
    module = _load_script("validate_ecosystem_va_chat_session_consolidation")
    for gate in ("Master Records organization record", "Master Records custody"):
        monkeypatch.setattr(module, "SOVEREIGN_VA_PROVIDER_TASK", _sovereign_task_with_gate(tmp_path, gate))
        _legacy, sovereign = module.validate_provider_continuation()
        assert gate in sovereign["preserved_vacc_gates"]


def test_va_session_consolidation_accepts_both_organization_record_gate_names(tmp_path, monkeypatch):
    module = _load_script("validate_va_claim_assistant_session_consolidation")
    monkeypatch.setattr(module, "OUTPUT", tmp_path / "receipt.json")
    for gate in ("Master Records organization record", "Master Records custody"):
        monkeypatch.setattr(module, "SOVEREIGN_PROVIDER_TASK", _sovereign_task_with_gate(tmp_path, gate))
        assert module.main() == 0


def test_orchestration_state_accepts_both_blocker_names():
    module = _load_script("check_llm_adapter_orchestration_state")
    assert module.external_blockers_valid(sorted(module.BLOCKERS))
    assert module.external_blockers_valid(sorted(module.LEGACY_BLOCKERS))
    assert not module.external_blockers_valid(["persistent endpoint"])
