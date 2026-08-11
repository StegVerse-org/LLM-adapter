# LLM Adapter Mirror Handoff

## Source of truth

Organization: `StegVerse-org`  
Repository: `LLM-adapter`  
Canonical branch: `main`  
Canonical Ecosystem Chat activation owner: `StegVerse-org/LLM-adapter#18`  
Canonical local-model/runtime owner: `StegVerse-002/micro-node-runtime#16/#22`  
Canonical carrier: `StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001`  
Canonical TVC route: `StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json`  
Custody/reconstruction owner: `master-records/orchestration`

Live repository state, task records, runtime receipts, immutable evidence, and this handoff supersede older chat claims.

## Current state

```text
repository-local governed path: COMPLETE
portable StegGate consumer: COMPLETE_VALIDATED
canonical local model development: COMPLETE_RELEASED
local runtime discovery/launch/proof: COMPLETE_RELEASED
persistent local endpoint proof: COMPLETE_MERGED_VALIDATED
heartbeat-owned lifecycle: COMPLETE_MERGED_VALIDATED
heartbeat -> TVC invocation: COMPLETE_MERGED_VALIDATED
TVC route credential requirement: NONE
LLM-adapter transport/evidence task 019: COMPLETE_RELEASED
LLM-adapter same-carrier executor task 020: COMPLETE_RELEASED
real same-carrier sovereign provider execution: NOT_YET_OBSERVED
provider-usage custody/reconstruction: NOT_YET_OBSERVED
same-execution transition reconstruction: NOT_YET_OBSERVED
immutable zero-blocker activation receipt: NOT_YET_OBSERVED
Site ACTIVATION_COMPLETE: NOT_YET_OBSERVED
manual user tasks: NONE
implementation claim for local runtime/model/carrier executor: RELEASED
continuation role: MACHINE_OWNED_RUNTIME_OBSERVATION
```

Repository implementation completion does not imply product activation.

## Canonical production path

```text
request
-> LLM-adapter governed consumer
-> canonical StegGate runtime identity validation
-> governed transition package
-> StegGate + coherence gate
-> heartbeat-owned canonical local model process
-> persistent runtime proof
-> TVC route evaluation
-> ROUTE_ADMITTED / credential_requirement NONE
-> StegVerseLocalHTTPProviderClient private/loopback transport
-> provider response + MEASURED usage
-> provider usage persistence
-> Master Records provider-usage custody/reconstruction
-> same-execution transition custody/reconstruction
-> immutable zero-blocker activation receipt
-> Site activation
-> Publisher/wiki propagation
```

## No-GitHub-token production boundary

```text
github_token_required_for_production: false
github_actions_production_role: false
credential_authority_model: TC/TVC
canonical_local_route_credential_requirement: NONE
```

GitHub repository access is not part of canonical production inference. GitHub Actions, Render, Cloudflare, Vercel, GitHub Models, OpenAI, and Anthropic are not canonical production heartbeat, inference, route, custody, or availability authorities. Optional hosted-provider interoperability remains separate.

## Local model/runtime — COMPLETE_RELEASED

Canonical owner: `StegVerse-002/micro-node-runtime#22`.

The descriptive "select a local model/runtime" step is superseded by executable discovery, launch, private serving, health proof, generation, measured usage, and hash-bound runtime proof.

The guaranteed fallback is `stegverse-reference-lm-v1`, a formally developed repository-local order-2 token-transition language model trained from repository-local corpus data. It guarantees a zero-external-dependency model-development/inference path and is explicitly not a production-scale foundation LLM.

Runtime discovery prefers a qualifying local `llama.cpp`/GGUF or Ollama model when present and otherwise uses the reference model.

Canonical evidence:

```text
StegVerse-002/micro-node-runtime/MICRO_NODE_RUNTIME_MIRROR_HANDOFF.md
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
validated_code_commit: 395d4013d1354c07bc3cf66c44f4f26f856c75fc
canonical_validation_run: 31339534741 SUCCESS
```

## LLM-adapter carrier execution — COMPLETE_RELEASED

Canonical task: `tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json`.

```text
script: scripts/execute_canonical_sovereign_route.py
test: tests/test_execute_canonical_sovereign_route.py
merge: 72934c7cf135ce2953591a81fe01e16c9719ec2f
credential_requirement: NONE
github_token_required: false
claim_state: COMPLETE_RELEASED
```

No session should reopen task 019 or 020 implementation unless directly observed evidence establishes a bounded defect.

## Public documentation reconciliation

Active docs branch: `fix/public-runtime-docs-20260811`.

Goal: make `README.md` and `adapter.capabilities.json` accurately describe the already-canonical sovereign runtime rather than the older hosted-provider/Demo-first story.

Required docs state:

```text
canonical route is sovereign local runtime
credential authority is TC/TVC
canonical local route credential class is NONE
GitHub token is not a production prerequisite
local model/runtime development is complete/released
reference model is real but intentionally not production-scale
same-carrier executor is complete/released
remaining gap is machine-owned runtime observation/custody/reconstruction/activation
```

This docs reconciliation is separate from the released runtime implementation and must not create a competing model/runtime implementation claim.

## Remaining activation work — MACHINE OWNED

```text
StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001
StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
master-records/orchestration
StegVerse-Labs/Site#239/#242
```

Required observation sequence:

```text
resident carrier recovery/current fence
-> local model process
-> TVC route admission
-> task-020 carrier execution
-> measured usage persistence
-> provider-usage reconstruction PASS
-> transition reconstruction PASS
-> immutable zero-blocker activation receipt
-> Site ACTIVATION_COMPLETE
-> Publisher/admissibility-wiki/stegguardian-wiki propagation
```

No downstream activation is claimed until that exact sequence is evidenced.

## Authority boundary

```text
provider output != authority
usage measurement != admissibility
local persistence != custody
custody receipt != execution authority
reconstruction PASS != execution authority
runtime proof != product activation
TVC route admission != execution authority
workflow artifact != live execution evidence
session archival != activation
```

## Session consolidation

Transferred and durable requirements:

1. no GitHub token in canonical production inference;
2. TV/TVC owns credential and route semantics;
3. local model selection must be executable, not descriptive;
4. a model must be formally developed locally;
5. the local reference model must not be misrepresented as a production-scale LLM;
6. stronger local models may be selected without changing governance/custody authority;
7. LLM-adapter same-carrier execution must use exact runtime proof + TVC admission + credential class NONE;
8. public README/capability manifest must match canonical runtime truth;
9. runtime observation/custody/reconstruction remains machine-owned and must not be falsely reported complete.

MERGED INTO canonical runtime continuation:

```text
StegVerse-002/micro-node-runtime#16/#22
StegVerse-org/LLM-adapter#18
StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001
StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
master-records/orchestration
```

## Completion accounting

```text
local-model developed surfaces: complete/released
local-model scaffolding/stubs: 0
carrier executor developed surfaces: 4/4 complete/released
public docs reconciliation required files: 3
public docs reconciliation implemented on branch: 3
runtime/product activation: incomplete, machine-owned observation
```

## Archive posture

The implementation slices for local model/runtime and carrier execution are already transferred and do not require this session. The docs-reconciliation branch remains active until its validation/merge state is resolved. Product activation remains machine-owned and is not a session-local implementation task.
