"""The Master Records HTTPS provider-usage client is removed (LLM-adapter#368).

No provider path called it: provider usage is recorded in the local usage ledger
and in the organization ledger by the transition receipt. Master Records is the
downstream recorder of released organization batch receipts, so no provider
execution may submit to, wait on, or be gated by a Master Records usage endpoint.
"""
import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_master_records_usage_client_module_is_gone():
    assert importlib.util.find_spec("llm_adapter.master_records_usage_record") is None
    assert not (ROOT / "llm_adapter" / "master_records_usage_record.py").exists()


def test_no_adapter_module_imports_or_calls_the_master_records_usage_client():
    for path in (ROOT / "llm_adapter").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "record_provider_usage_in_master_records" not in text, path
        assert "STEGVERSE_MASTER_RECORDS_USAGE_URL" not in text, path
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.endswith("master_records_usage_record"), path
            if isinstance(node, ast.Import):
                assert all(not a.name.endswith("master_records_usage_record") for a in node.names), path
