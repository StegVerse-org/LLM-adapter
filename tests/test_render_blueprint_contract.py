"""The Render-hosted blueprints are retired.

render.yaml was removed in a1e74f1 ("Remove obsolete Render HIL service
manifest") and render-production.yaml in 1bd4e4c ("Retire non-TVC hosted
activation paths"): both ran the gateway on an external hosted platform. The
sovereign destination contract records Render as superseded and not required
(tests/test_destination_activation_state_sovereign.py). These tests keep the
retirement from silently regressing.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RenderBlueprintRetirementTests(unittest.TestCase):
    def test_render_blueprints_stay_retired(self):
        for name in ("render.yaml", "render-production.yaml"):
            with self.subTest(blueprint=name):
                self.assertFalse((ROOT / name).exists(), f"{name} is retired and must stay absent")


if __name__ == "__main__":
    unittest.main()
