# Local Runtime Model Mirror Handoff

## Identity

```yaml
goal_id: LLMA-LOCAL-RUNTIME-MODEL-017
originating_session_goal: remove the descriptive select-a-local-model/runtime step and formally develop a model locally
repository: StegVerse-org/LLM-adapter
branch: main
canonical_continuation: StegVerse-org/LLM-adapter#18
claim: RELEASED_COMPLETE
public_activation: NOT_GRANTED_BY_THIS_TASK
```

## Result

The descriptive local-model choice has been replaced by an executable repository-owned path:

```text
discover loopback runtime
  -> accept conforming stegverse.local-runtime.v1 runtime
  -> otherwise detect a populated Ollama loopback endpoint
  -> if no conforming runtime exists, automatically launch the repository-owned runtime
  -> rediscover it
  -> execute real local inference
  -> bind model/input/output/weights hashes
  -> persist proof receipt
  -> retain hosted artifact
```

The canonical first-party model is `stegverse-local-reference-v1`. It is a formally specified, repository-trained deterministic count language model, not a foundation LLM. Training and inference require no external provider and no model-network download.

## Authoritative files

```text
models/stegverse-local-reference-v1/corpus.txt
models/stegverse-local-reference-v1/weights.json
models/stegverse-local-reference-v1/manifest.json
scripts/build_local_reference_model.py
llm_adapter/local_model_runtime.py
scripts/prove_local_runtime_model.py
tests/test_local_runtime_model.py
.github/workflows/local-runtime-model-proof.yml
receipts/local-runtime-model-proof.latest.json
tasks/LLMA-LOCAL-RUNTIME-MODEL-017.json
```

## Formal model definition

```text
model_id: stegverse-local-reference-v1
model_class: repository_trained_count_language_model
algorithm: deterministic-bigram-argmax
training corpus SHA-256: af6f125753a893f60c345f3214f5e7d8282c9f1fd7635ef2ef6778740596a558
weights SHA-256: b764e082c90e2c40998faf51e2bb3f616b5fad72dfd77735a2e86a7d2798fe4f
runtime protocol: stegverse.local-runtime.v1
network required for training: false
network required for inference: false
authority attached: false
```

The builder deterministically reconstructs weights and manifest from the committed corpus. CI requires byte-identical generated artifacts before inference proof proceeds.

## Runtime contract

`llm_adapter/local_model_runtime.py` owns discovery, automatic launch, identity, and inference. The first-party server binds only to loopback and exposes:

```text
GET  /healthz
GET  /v1/runtime-identity
GET  /v1/models
POST /v1/completions
```

Discovery first checks the StegVerse local protocol and can recognize a populated local Ollama endpoint. If no conforming runtime is reachable, `ensure_local_runtime()` launches the first-party model runtime and requires rediscovery before inference.

## Hosted verification

First run `31341760052` intentionally failed the reproducibility gate because the initially committed JSON formatting did not equal generated output. The repository was repaired rather than relaxing the check.

Successful proof:

```text
workflow: Local Runtime Model Proof
run: 31341784892
job: 93316662476
result: SUCCESS
artifact: 9046045319
artifact digest: sha256:d6221913fb1560c6cc0729f61aa568cb59bda016cbdd2878f6e951c6231399bf
receipt: receipts/local-runtime-model-proof.latest.json
receipt hash: f078d8507cf3ef5d1d5a36474b3f93ad73f3435ca55f51bab0545f2e3c6935ca
```

The successful job directly verified model rebuild reproducibility, model/runtime tests, automatic discovery/launch, real loopback inference, proof-receipt validation, receipt persistence, and artifact upload.

Observed inference:

```text
prompt hash: eb80e2077fb8e541a11ed6dbcd9532de7b26a28c7c534a2c103ff73faa3a5d60
output: records model identity input hash and execution
output hash: 34d1d39c4bc6145cdfe1898ebf1a6a0a409ff6ca9cf8d187295c7dd43285c9f8
external provider used: false
real local inference observed: true
```

## Authority boundary

```text
local model != canonical StegGate
model output != authority
runtime discovery != admissibility
runtime launch != public deployment
local inference proof != Ecosystem Chat activation
local inference proof != Master Records custody
Ollama discovery compatibility != Ollama dependency
repository-developed reference model != foundation LLM
```

Canonical StegGate remains `StegVerse-Labs/StegCore`; Master Records remains the custody/reconstruction owner.

## Completion and continuation

`LLMA-LOCAL-RUNTIME-MODEL-017` is COMPLETE and its claim is released. There is no remaining instruction to manually “select a local model/runtime” for the reference path.

MERGED INTO: `StegVerse-org/LLM-adapter#18`

Transferred next requirement: bind `stegverse.local-runtime.v1` into the real Ecosystem Chat governed provider-execution lane, retain the canonical StegGate identity and decision before inference, then persist provider-usage/custody/reconstruction evidence and allow the existing zero-blocker activation machinery to advance only from real evidence.

## Metrics

```yaml
developed_files_percent: 100
model_definition_percent: 100
reproducibility_validation_percent: 100
runtime_discovery_launch_percent: 100
local_inference_proof_percent: 100
hosted_validation_percent: 100
public_ecosystem_chat_activation_effect_percent: 0
session_requirement_transfer_percent: 100
```

## Archive condition

This local-runtime/model task itself is archive-safe. The parent session remains active because Ecosystem Chat has not yet consumed the proven local inference path as its real governed execution and the four-public-app activation goal remains incomplete.
