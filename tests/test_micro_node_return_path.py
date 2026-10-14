from __future__ import annotations

import unittest
from scripts.verify_micro_node_return_path import main as verify_micro_node_return_path


class MicroNodeReturnPathTests(unittest.TestCase):
    def test_micro_node_return_path_fixture_passes(self) -> None:
        assert verify_micro_node_return_path() == 0


if __name__ == "__main__":
    unittest.main()
