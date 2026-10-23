#!/usr/bin/env python3
"""Regenerate stegos_existence_broker_receipt.json with StegOS's own broker (not run in CI).

    STEGOS_ROOT=/path/to/StegOS python3 tests/fixtures/node_receipts/generate_with_stegos.py

It uses StegOS laneb/node-identity-key-reference (StegVerse-Labs/StegOS, on e63f7e89). The run is:
* register_reciprocal_node_existence_capability on NodeEventExecutionBroker;
* build_request and execute;
* the fixtures of StegOS tests/test_node_event_execution_broker.py.
The only substitution is the HTTPS reader. A fixed profile document
(stegos_observed_profile.json) stands in for the network read, so nothing is
fetched. The profile publishes `node_identity_key` carrying the TEST-ONLY public key
from tests/ed25519_test_signer.py and declares the KV_STANDING purpose; the
invocation also passes standing_request KV_STANDING, so StegOS enforces the key.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, os.environ["STEGOS_ROOT"])
sys.path.insert(0, os.path.join(os.environ["STEGOS_ROOT"], "tests"))
from test_node_event_execution_broker import _claim, _materialization, _node, _runtime_admission  # noqa: E402
from stegos.node_event_execution_broker import NodeEventExecutionBroker  # noqa: E402
from stegos.universal_intr_public_profile import (  # noqa: E402
    RECIPROCAL_EXISTENCE_CAPABILITY_ADAPTER, register_reciprocal_node_existence_capability)

profile = json.loads((HERE / "stegos_observed_profile.json").read_text())
broker = NodeEventExecutionBroker()
register_reciprocal_node_existence_capability(broker, reader=lambda url, timeout: profile)
request = broker.build_request(
    task_id="KV-SKAP-VAULT-FUNCTIONAL-001", cosv="71000000100110", materialization=_materialization(),
    retained_node=_node(), worker_claim=_claim(), runtime_admission=_runtime_admission(),
    capability_adapter=RECIPROCAL_EXISTENCE_CAPABILITY_ADAPTER,
    invocation={"profile_url": "https://node.example.invalid/intr/profile", "required_profile": "NodeExchange:Existence",
                "standing_request": "KV_STANDING"})
receipt = broker.execute(request)
(HERE / "stegos_existence_broker_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(receipt["receipt_hash"])
