# Node-receipt producer fixtures (test-only)

- `stegos_existence_broker_receipt.json` is a real `stegos.node-event-execution-broker.receipt/v3`. It was produced by StegOS @e63f7e89's own `NodeEventExecutionBroker`, with `observe-reciprocal-node-existence` registered, by `generate_with_stegos.py`. The only substitution is the HTTPS reader: `stegos_observed_profile.json` stands in for the network read.
- `stegos_observed_profile.json` is the public InTr profile the observation hashed. Its `node_identity_key` is the TEST-ONLY public key from `tests/ed25519_test_signer.py`, marked `test_fixture_only`.
- `steghealth_runtime_observation.json` is the output of StegHealth @8508a43c `steghealth.sovereign_runtime_observation.project_runtime_observation`, run on a synthetic passing `sovereign-runtime-activation-proof/v4` with `observed_at` fixed.

None of these files is a real node, a real key or a ledger receipt.
