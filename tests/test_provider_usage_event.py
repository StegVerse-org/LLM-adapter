from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.verify_provider_usage_event import canonical_hash, validate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/provider_usage_event.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class ProviderUsageEventTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        assert validate() == []

    def test_hash_is_deterministic(self) -> None:
        event = load_fixture()
        assert canonical_hash(event) == event["event_sha256"]

    def test_authority_escalation_fails_closed(self) -> None:
        event = load_fixture()
        event["authority_boundary"]["adapter_is_execution_authority"] = True
        event["event_sha256"] = canonical_hash(event)
        assert "authority escalation: adapter_is_execution_authority" in validate(event)

    def test_full_chain_of_thought_claim_fails_closed(self) -> None:
        event = load_fixture()
        event["reasoning_provenance"]["full_chain_of_thought_included"] = True
        event["event_sha256"] = canonical_hash(event)
        assert "full chain of thought boundary violated" in validate(event)

    def test_usage_measurement_is_not_value_claim(self) -> None:
        event = load_fixture()
        event["authority_boundary"]["usage_measurement_is_value_claim"] = True
        event["event_sha256"] = canonical_hash(event)
        assert "authority escalation: usage_measurement_is_value_claim" in validate(event)

    def test_token_total_mismatch_rejected(self) -> None:
        event = load_fixture()
        event["measurements"]["total_tokens"] = 999
        event["event_sha256"] = canonical_hash(event)
        assert "token total mismatch" in validate(event)

    def test_missing_return_receipt_rejected(self) -> None:
        event = load_fixture()
        event["return_to_origin"]["receipt_required"] = False
        event["event_sha256"] = canonical_hash(event)
        assert "return receipt must be required" in validate(event)

    def test_hash_tampering_rejected(self) -> None:
        event = copy.deepcopy(load_fixture())
        event["provider"]["model"] = "tampered-model"
        assert "event hash mismatch" in validate(event)


if __name__ == "__main__":
    unittest.main()
