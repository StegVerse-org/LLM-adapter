#!/usr/bin/env python3
"""Deterministically verify Math Solver canonical StegGate execution and replay."""
from __future__ import annotations

import json

from llm_adapter.math_solver_gateway import governed_solve
from stegcore.portable_steggate import runtime_fingerprint

STEGCORE_COMMIT = "8c484e584d60a3bd2763d6948d0eb3f4afd67e0c"


def main() -> int:
    first = governed_solve("6 * 7", request_id="MATH-DETERMINISTIC-42-A")
    replay = governed_solve("6 * 7", request_id="MATH-DETERMINISTIC-42-B")
    identity = first["steggate_runtime_identity"]

    evidence = {
        "schema_version": "MATH-SOLVER-STEGGATE-INTEGRATION-v2",
        "stegcore_commit": STEGCORE_COMMIT,
        "runtime_fingerprint": runtime_fingerprint(),
        "runtime_identity": identity,
        "runtime_identity_replay_match": identity == replay["steggate_runtime_identity"],
        "request_hash_replay_match": first["request_hash"] == replay["request_hash"],
        "result_hash_replay_match": first["result_hash"] == replay["result_hash"],
        "canonical_steggate_preexecution": first["disposition"] == "ALLOW" and first["executor_invoked"] is True,
        "result": first["result"],
        "status": "PASS",
        "authority_effect": False,
        "public_deployment_proven": False,
        "sovereign_carrier_observed": False,
    }

    assert identity["contract_version"] == "stegverse.steggate.runtime-identity.v1"
    assert identity["runtime_identity"] == "stegverse:steggate:canonical:three-layer:v1"
    assert identity["canonical_owner"] == "StegVerse-Labs/StegCore"
    assert identity["canonical_admissibility_runtime"] == "stegcore.three_layer.evaluate_three_layer"
    assert identity["transport_identity_authoritative"] is False
    assert identity["application_specific_policy_authority"] is False
    assert evidence["runtime_identity_replay_match"]
    assert evidence["request_hash_replay_match"]
    assert evidence["result_hash_replay_match"]
    assert evidence["canonical_steggate_preexecution"]
    assert evidence["result"] == 42
    assert evidence["authority_effect"] is False
    assert evidence["public_deployment_proven"] is False
    assert evidence["sovereign_carrier_observed"] is False

    print(json.dumps(evidence, sort_keys=True))
    print("MATH_SOLVER_GOVERNED_RUNTIME_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
