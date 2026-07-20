from __future__ import annotations

import json
from pathlib import Path

from scripts import stegnode


def test_discovers_only_auto_start_capabilities(tmp_path: Path, monkeypatch) -> None:
    capability_dir = tmp_path / "capabilities"
    capability_dir.mkdir()
    (capability_dir / "chat.json").write_text(
        json.dumps({"capability_id": "chat", "node": {"auto_start": True}}),
        encoding="utf-8",
    )
    (capability_dir / "manual.json").write_text(
        json.dumps({"capability_id": "manual", "node": {"auto_start": False}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(stegnode, "CAPABILITY_DIR", capability_dir)
    assert stegnode.discover() == [capability_dir / "chat.json"]


def test_node_state_declares_no_manual_selection(tmp_path: Path, monkeypatch) -> None:
    state_path = tmp_path / "node-state.json"
    monkeypatch.setattr(stegnode, "STATE_PATH", state_path)
    stegnode.write_state({}, "RUNNING")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["manual_capability_selection_required"] is False
    assert state["state"] == "RUNNING"
