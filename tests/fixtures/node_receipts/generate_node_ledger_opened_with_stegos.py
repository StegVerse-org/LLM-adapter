#!/usr/bin/env python3
"""Regenerate stegos_node_ledger_opened.json with StegOS's own generation-time emit (not run in CI).

    STEGOS_ROOT=/path/to/StegOS python3 tests/fixtures/node_receipts/generate_node_ledger_opened_with_stegos.py

It uses StegOS laneb/ephemeral-node-ledger-opened (stacked on laneb/node-identity-key-reference,
StegVerse-Labs/StegOS#426). The run is:
* open the EPHEMERAL StegNode ledger genesis with llm_adapter.endpoint_ledger_anchor.open_ledger in a temporary
  directory (deterministic: no clock, observed_at null, epoch from the empty chain);
* pass the profile fixture and that genesis to stegos.ephemeral_node_ledger_open.open_ephemeral_node_ledger.
The tests re-open the same genesis and check that the StegOS record names its hash.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, os.environ["STEGOS_ROOT"])
from llm_adapter import endpoint_ledger_anchor as anchor  # noqa: E402
from stegos.ephemeral_node_ledger_open import open_ephemeral_node_ledger  # noqa: E402

profile = json.loads((HERE / "stegos_observed_profile.json").read_text())
key = profile["node_identity_key"]
with tempfile.TemporaryDirectory() as root:
    genesis = anchor.open_ledger(root, key["node_id"], anchor.EPHEMERAL, key, "StegNode")["genesis"]
record = open_ephemeral_node_ledger(profile, node_kind="StegNode", ledger_genesis=genesis)
assert record["disposition"] == "ALLOW", record
(HERE / "stegos_node_ledger_opened.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(record["record_sha256"], record["ledger_genesis_sha256"])
