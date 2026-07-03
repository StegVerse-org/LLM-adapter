from __future__ import annotations

from scripts.verify_micro_node_return_path import main as verify_micro_node_return_path


def test_micro_node_return_path_fixture_passes() -> None:
    assert verify_micro_node_return_path() == 0
