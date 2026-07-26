#!/usr/bin/env python3
"""Transparent internal governed reference test suite.

This suite is intentionally dependency-free and deterministic. It does not claim
production deployment, independent reproduction, or external audit. It produces
an inspectable JSON evidence packet whose inputs, rules, observations, and hashes
can be replayed by any party with Python 3.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "internal_tests" / "artifacts" / "governed-reference-results.json"
FIXED_NOW = datetime(2026, 7, 25, 23, 30, 0, tzinfo=timezone.utc)
SUITE_VERSION = "stegverse.internal-governed-reference.v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(value: Any) -> str:
    material = value if isinstance(value, str) else canonical_json(value)
    return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Decision:
    outcome: str
    reason: str
    execution_allowed: bool
    authority_effect: str = "NONE"


@dataclass(frozen=True)
class TestResult:
    test_id: str
    description: str
    expected: dict[str, Any]
    observed: dict[str, Any]
    passed: bool
    input_hash: str
    result_hash: str
    limitations: list[str]


def decide(*, standing: str, delegation_expires: datetime, revoked: bool,
           policy_hash_at_review: str, policy_hash_at_commit: str,
           restricted: bool = False) -> Decision:
    if restricted:
        return Decision("DENY", "restricted_request_requires_separate_authority", False)
    if revoked:
        return Decision("DENY", "delegation_revoked_before_commit", False)
    if delegation_expires <= FIXED_NOW:
        return Decision("DENY", "delegation_expired_before_commit", False)
    if standing != "VALID":
        return Decision("DENY", "standing_invalid_at_commit", False)
    if policy_hash_at_review != policy_hash_at_commit:
        return Decision("DENY", "policy_mutated_after_review", False)
    return Decision("ALLOW", "all_declared_commit_time_conditions_valid", True)


def case(test_id: str, description: str, inputs: dict[str, Any],
         expected: dict[str, Any], evaluator: Callable[[], dict[str, Any]],
         limitations: list[str] | None = None) -> TestResult:
    observed = evaluator()
    passed = all(observed.get(key) == value for key, value in expected.items())
    result_material = {
        "test_id": test_id,
        "inputs": inputs,
        "expected": expected,
        "observed": observed,
        "passed": passed,
    }
    return TestResult(
        test_id=test_id,
        description=description,
        expected=expected,
        observed=observed,
        passed=passed,
        input_hash=sha256(inputs),
        result_hash=sha256(result_material),
        limitations=limitations or ["internal deterministic reference execution only"],
    )


def decision_observation(**kwargs: Any) -> dict[str, Any]:
    return asdict(decide(**kwargs))


def receipt_chain_test() -> dict[str, Any]:
    events = [
        {"event_id": "evt-1", "type": "submission", "payload": "bounded-input"},
        {"event_id": "evt-2", "type": "decision", "payload": "DENY"},
        {"event_id": "evt-3", "type": "receipt", "payload": "final"},
    ]
    previous = "GENESIS"
    chain = []
    for event in events:
        receipt = {
            "event": event,
            "previous_receipt_hash": previous,
        }
        current = sha256(receipt)
        chain.append({**receipt, "receipt_hash": current})
        previous = current
    replay_valid = True
    previous = "GENESIS"
    for item in chain:
        replay = {"event": item["event"], "previous_receipt_hash": previous}
        if sha256(replay) != item["receipt_hash"]:
            replay_valid = False
            break
        previous = item["receipt_hash"]
    return {
        "replay_valid": replay_valid,
        "chain_length": len(chain),
        "chain_head": chain[-1]["receipt_hash"],
        "authority_effect": "NONE",
    }


def restart_persistence_test() -> dict[str, Any]:
    state = {
        "transition_id": "transition-restart-001",
        "lifecycle": "DENIED",
        "reason": "policy_mutated_after_review",
        "authority_effect": "NONE",
    }
    serialized = canonical_json(state)
    restored = json.loads(serialized)
    return {
        "restored_equal": restored == state,
        "transition_id": restored["transition_id"],
        "lifecycle": restored["lifecycle"],
        "state_hash": sha256(restored),
    }


def main() -> int:
    valid_until = FIXED_NOW + timedelta(hours=1)
    expired_at = FIXED_NOW - timedelta(seconds=1)
    policy_v1 = sha256({"policy": "v1", "allow": ["bounded-task"]})
    policy_v2 = sha256({"policy": "v2", "allow": []})

    tests = [
        case(
            "GOV-001", "Valid standing and unchanged policy allow bounded execution.",
            {"standing": "VALID", "expires": valid_until.isoformat(), "revoked": False, "policy": policy_v1},
            {"outcome": "ALLOW", "execution_allowed": True, "authority_effect": "NONE"},
            lambda: decision_observation(standing="VALID", delegation_expires=valid_until,
                revoked=False, policy_hash_at_review=policy_v1, policy_hash_at_commit=policy_v1),
        ),
        case(
            "GOV-002", "Expired delegation denies at commit time.",
            {"standing": "VALID", "expires": expired_at.isoformat(), "revoked": False},
            {"outcome": "DENY", "reason": "delegation_expired_before_commit", "execution_allowed": False},
            lambda: decision_observation(standing="VALID", delegation_expires=expired_at,
                revoked=False, policy_hash_at_review=policy_v1, policy_hash_at_commit=policy_v1),
        ),
        case(
            "GOV-003", "Revocation before commit overrides earlier validity.",
            {"standing": "VALID", "expires": valid_until.isoformat(), "revoked": True},
            {"outcome": "DENY", "reason": "delegation_revoked_before_commit", "execution_allowed": False},
            lambda: decision_observation(standing="VALID", delegation_expires=valid_until,
                revoked=True, policy_hash_at_review=policy_v1, policy_hash_at_commit=policy_v1),
        ),
        case(
            "GOV-004", "Invalid standing denies despite valid delegation.",
            {"standing": "INVALID", "expires": valid_until.isoformat(), "revoked": False},
            {"outcome": "DENY", "reason": "standing_invalid_at_commit", "execution_allowed": False},
            lambda: decision_observation(standing="INVALID", delegation_expires=valid_until,
                revoked=False, policy_hash_at_review=policy_v1, policy_hash_at_commit=policy_v1),
        ),
        case(
            "GOV-005", "Policy mutation after review denies commit.",
            {"review_policy": policy_v1, "commit_policy": policy_v2},
            {"outcome": "DENY", "reason": "policy_mutated_after_review", "execution_allowed": False},
            lambda: decision_observation(standing="VALID", delegation_expires=valid_until,
                revoked=False, policy_hash_at_review=policy_v1, policy_hash_at_commit=policy_v2),
        ),
        case(
            "GOV-006", "Restricted request remains fail-closed without separate authority.",
            {"restricted": True},
            {"outcome": "DENY", "reason": "restricted_request_requires_separate_authority", "execution_allowed": False},
            lambda: decision_observation(standing="VALID", delegation_expires=valid_until,
                revoked=False, policy_hash_at_review=policy_v1, policy_hash_at_commit=policy_v1, restricted=True),
        ),
        case(
            "GOV-007", "Receipt chain replays deterministically.",
            {"events": ["submission", "decision", "receipt"]},
            {"replay_valid": True, "chain_length": 3, "authority_effect": "NONE"},
            receipt_chain_test,
        ),
        case(
            "GOV-008", "Serialized transition state survives a restart simulation.",
            {"transition_id": "transition-restart-001"},
            {"restored_equal": True, "transition_id": "transition-restart-001", "lifecycle": "DENIED"},
            restart_persistence_test,
            ["serialization/reload simulation; not evidence of deployed durable storage"],
        ),
    ]

    packet = {
        "schema": SUITE_VERSION,
        "execution_class": "INTERNAL_EXECUTION",
        "public_replayable": True,
        "independently_reproduced": False,
        "production_observed": False,
        "fixed_validation_time": FIXED_NOW.isoformat(),
        "runner": "internal_tests/run_governed_reference_suite.py",
        "runner_sha256": sha256(Path(__file__).read_text(encoding="utf-8")),
        "tests": [asdict(item) for item in tests],
        "summary": {
            "total": len(tests),
            "passed": sum(item.passed for item in tests),
            "failed": sum(not item.passed for item in tests),
        },
        "claim_boundary": {
            "established": ["deterministic reference behavior for declared vectors", "public replayability of this packet"],
            "not_established": ["live deployment", "provider execution", "durable infrastructure persistence", "independent reproduction", "production assurance"],
        },
    }
    packet["packet_sha256"] = sha256(packet)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(packet["summary"], sort_keys=True))
    print(f"evidence_packet={OUTPUT.relative_to(ROOT)}")
    print(f"packet_sha256={packet['packet_sha256']}")
    return 0 if packet["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
