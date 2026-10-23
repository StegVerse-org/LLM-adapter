# Node-receipt producer fixtures (test-only)

- `stegos_existence_broker_receipt.json` is a real `stegos.node-event-execution-broker.receipt/v3`. It was produced by StegOS's own `NodeEventExecutionBroker` (StegVerse-Labs/StegOS `laneb/node-identity-key-reference` on e63f7e89, which enforces `node_identity_key` for KV standing; invocation `standing_request: KV_STANDING`), with `observe-reciprocal-node-existence` registered, by `generate_with_stegos.py`. The only substitution is the HTTPS reader: `stegos_observed_profile.json` stands in for the network read.
- `stegos_observed_profile.json` is the public InTr profile the observation hashed. It declares the `KV_STANDING` purpose, and its `node_identity_key` is the TEST-ONLY public key from `tests/ed25519_test_signer.py`. The profile is marked `test_fixture_only`.
- `steghealth_runtime_observation.json` is the output of StegHealth @8508a43c `steghealth.sovereign_runtime_observation.project_runtime_observation`, run on a synthetic passing `sovereign-runtime-activation-proof/v4` with `observed_at` fixed.

None of these files is a real node, a real key or a ledger receipt.

## `stegos_node_ledger_opened.json`

This is the `NODE_LEDGER_OPENED` generation record (`stegverse.node-ledger-opened-generation/v1`, `schemas/node-ledger-opened-generation.v1.json`; `receipt_sha256` `sha256:668e9b72…7485`) that StegOS's own generation-time code (`stegos.ephemeral_node_ledger_open`, StegOS branch `laneb/ephemeral-node-ledger-opened`) emits for the EPHEMERAL StegNode ledger genesis of `stegos_observed_profile.json`'s node.

To regenerate it, run `STEGOS_ROOT=... python3 tests/fixtures/node_receipts/generate_node_ledger_opened_with_stegos.py`. The genesis is deterministic, and `tests/test_endpoint_ledger_anchor.py` re-opens it and checks that the record's `genesis_receipt_sha256` names its hash. The org ledger issues the `stegverse.node-ledger-opened/v1` anchor from this record when its ingress admits it; the anchor is not a fixture.

If the pinned code digests change, the genesis changes too, and this fixture has to be regenerated.

## `contract_with_431_repository_ledger_location.json`

A byte copy of `.stegverse/transition-ledger/contract.json` at StegVerse-org/LLM-adapter#431 @b7a5c08b, which adds `repository_ledger_location`. The LC-KV-16 tests point `llm_adapter.org_ledger_location.CONTRACT_PATH` at it so the designated-location path can be exercised before #431 is admitted; main's contract has no designation, so production refuses with `ORG_LEDGER_LOCATION_NOT_DESIGNATED`. The tests sign the `NODE_LEDGER_OPENED` envelope with a TEST-ONLY seed and publish its public key only inside the test.
