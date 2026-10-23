"""Test helper: put a NODE_HEALTH_REPORTED receipt on the (redirected) repository ledger.

The healthy-node evaluator decides only from receipted reports, so a test that
expects a healthy node first records one through this repository's own emitter,
into the temporary ledger root the tests redirect to. Never used outside tests.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from llm_adapter import healthy_node_evaluator as hne

ROOT = Path(__file__).resolve().parents[1]
TEST_EPOCH = 64


def _emitter():
    spec = importlib.util.spec_from_file_location("emit_for_tests", ROOT / ".stegverse/transition-ledger/emit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report(node_id: str, status: str = hne.HEALTHY) -> dict:
    evidence = {"schema": hne.HEALTH_REPORT_SCHEMA, "node_id": node_id, "status": status,
                "authority_effect": "NONE_TEST_FIXTURE"}
    emit = _emitter()
    return emit.append(f"{hne.HEALTH_REPORT_CLASS}:{node_id}", hne.HEALTH_REPORT_CLASS,
                       emit.sha({"node_id": node_id}), emit.sha(evidence), evidence, "NONE", hb_epoch=TEST_EPOCH)
