from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_hps_adapter_consumption import verify_fixture  # noqa: E402

EXAMPLES = ROOT / "examples"


def load_example(name: str) -> dict:
    with (EXAMPLES / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class HpsAdapterConsumptionTests(unittest.TestCase):
    def test_allow_goes_only_to_next_boundary(self) -> None:
        result = verify_fixture(load_example("hps_adapter_route_allowed.json"))
        self.assertTrue(result.ok, result.errors)

    def test_deny_blocks_consequence(self) -> None:
        result = verify_fixture(load_example("hps_adapter_route_denied.json"))
        self.assertTrue(result.ok, result.errors)

    def test_fail_closed_blocks_and_preserves(self) -> None:
        result = verify_fixture(load_example("hps_adapter_route_fail_closed.json"))
        self.assertTrue(result.ok, result.errors)


if __name__ == "__main__":
    unittest.main()
