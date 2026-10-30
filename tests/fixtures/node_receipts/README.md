# Node-receipt producer fixtures (test-only)

- `stegos_existence_broker_receipt.json` is a real `stegos.node-event-execution-broker.receipt/v3`. It was produced by StegOS's own `NodeEventExecutionBroker` (StegVerse-Labs/StegOS `laneb/node-identity-key-reference` on e63f7e89, which enforces `node_identity_key` for KV standing; invocation `standing_request: KV_STANDING`), with `observe-reciprocal-node-existence` registered, by `generate_with_stegos.py`. The only substitution is the HTTPS reader: `stegos_observed_profile.json` stands in for the network read.
- `stegos_observed_profile.json` is the public InTr profile the observation hashed. It declares the `KV_STANDING` purpose, and its `node_identity_key` is the TEST-ONLY public key from `tests/ed25519_test_signer.py`. The profile is marked `test_fixture_only`.
- `steghealth_runtime_observation.json` is the output of StegHealth @8508a43c `steghealth.sovereign_runtime_observation.project_runtime_observation`, run on a synthetic passing `sovereign-runtime-activation-proof/v4` with `observed_at` fixed.

None of these files is a real node, a real key or a ledger receipt.
