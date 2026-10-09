"""The Master Records local-socket usage gate is removed (LLM-adapter#368 F6).

Provider usage is recorded in the local usage ledger and in the organization
ledger by the transition receipt. No provider path may wait on, or be gated by,
the Master Records provider-usage socket.
"""
import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_master_records_local_socket_module_is_gone():
    assert importlib.util.find_spec("llm_adapter.master_records_local_usage_record") is None
    assert not (ROOT / "llm_adapter" / "master_records_local_usage_record.py").exists()


def test_no_adapter_module_references_the_master_records_usage_socket():
    for path in (ROOT / "llm_adapter").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "master-records-provider-usage.sock" not in text, path
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.endswith("master_records_local_usage_record"), path
