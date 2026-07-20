from __future__ import annotations

import pytest

from llm_adapter import portable_node


def test_process_backend_is_selected_without_manual_action(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(portable_node.shutil, "which", lambda name: None)
    result = portable_node.resolve_backend(["process", "container"])
    assert result.backend == "process"
    assert result.manual_action_required is False
    assert result.profile.process_available is True


def test_preferred_unavailable_backend_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(portable_node.shutil, "which", lambda name: None)
    result = portable_node.resolve_backend(["wasm", "process"], preferred="wasm")
    assert result.backend == "process"


def test_peer_backend_can_be_selected_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(portable_node.shutil, "which", lambda name: None)
    result = portable_node.resolve_backend(
        ["peer"],
        env={"STEGVERSE_PEER_EXECUTOR_ENDPOINT": "https://peer.invalid/execute"},
    )
    assert result.backend == "peer"
    assert result.profile.peer_available is True


def test_resolution_fails_closed_when_no_backend_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(portable_node.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="capability remains unconstructed"):
        portable_node.resolve_backend(["wasm", "container"], env={})
