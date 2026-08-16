from __future__ import annotations

import json
from pathlib import Path

from llm_adapter.node_bootstrap import bootstrap, default_node_root


def test_override_selects_node_root(tmp_path: Path) -> None:
    root = default_node_root({"STEGVERSE_NODE_ROOT": str(tmp_path / "node")})
    assert root == (tmp_path / "node").resolve()


def test_bootstrap_materializes_profile_manifest_and_receipt(tmp_path: Path) -> None:
    receipt = bootstrap(tmp_path)
    profile = json.loads((tmp_path / "node-profile.json").read_text(encoding="utf-8"))
    capability = json.loads(
        (tmp_path / "capabilities" / "ecosystem-chat-gateway.json").read_text(encoding="utf-8")
    )
    stored_receipt = json.loads(
        (tmp_path / "receipts" / "bootstrap.latest.json").read_text(encoding="utf-8")
    )

    assert profile["manual_capability_selection_required"] is False
    assert profile["reconstruct_missing_capabilities"] is True
    assert capability["portability"]["manual_backend_selection_required"] is False
    assert capability["state"]["durable_root"] == str((tmp_path / "state").resolve())
    assert capability["entrypoint"][3] == "llm_adapter.deployed_gateway:app"
    assert capability["routes"]["math_solver_readiness"] == "/api/math-solver/v1/readiness"
    assert capability["routes"]["math_solver_solve"] == "/api/math-solver/v1/solve"
    assert capability["credential_boundary"]["credential_authority"] == "TV/TVC"
    assert capability["credential_boundary"]["github_token_runtime_authority"] == "NONE"
    assert receipt["manual_action_required"] is False
    assert stored_receipt["receipt_sha256"] == receipt["receipt_sha256"]


def test_bootstrap_is_idempotent(tmp_path: Path) -> None:
    first = bootstrap(tmp_path)
    second = bootstrap(tmp_path)
    assert first["receipt_sha256"] == second["receipt_sha256"]
