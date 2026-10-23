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


# Receipted inputs the producer reads. These are test fixtures, standing in for
# the real producers of AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE,
# NODE_IDENTITY_BINDING and NODE_HEALTH_CHECK_OBSERVED. They are appended only
# into the redirected test ledger.
def _fixture(transition_class: str, evidence: dict) -> dict:
    emit = _emitter()
    evidence = {**evidence, "authority_effect": "NONE_TEST_FIXTURE"}
    return emit.append(f"{transition_class}:{evidence.get('node_id')}", transition_class,
                       emit.sha({"node_id": evidence.get("node_id")}), emit.sha(evidence), evidence, "NONE",
                       hb_epoch=TEST_EPOCH)


def existence(node_id: str, disposition: str = "ALLOW") -> dict:
    return _fixture("AUTHENTICATED_RECIPROCAL_NODE_EXISTENCE", {"node_id": node_id, "disposition": disposition})


def binding(node_id: str, existence_receipt_sha256: str | None, disposition: str = "ALLOW") -> dict:
    return _fixture("NODE_IDENTITY_BINDING", {"node_id": node_id, "disposition": disposition,
                                              "existence_receipt_sha256": existence_receipt_sha256})


def health_check(node_id: str, status: str = hne.HEALTHY) -> dict:
    return _fixture("NODE_HEALTH_CHECK_OBSERVED", {"schema": "stegverse.node-health-check/v1",
                                                   "node_id": node_id, "status": status})


def identified(node_id: str) -> tuple[dict, dict]:
    """Receipt the two earlier gates for node_id, in order."""
    exists = existence(node_id)
    return exists, binding(node_id, exists["receipt_sha256"])
