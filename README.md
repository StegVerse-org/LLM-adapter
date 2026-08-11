# StegVerse LLM Adapter

The StegVerse LLM Adapter is the machine-readable translation and provider-boundary component between governed StegVerse requests and model/runtime execution.

Its canonical production path is sovereign and credential-neutral at the route boundary: TC/TVC owns credential semantics and route authority, and the canonical local route requires credential class `NONE`.

## Canonical production path

```text
StegVerse request
-> LLM-adapter governed consumer
-> canonical StegGate runtime identity validation
-> governed transition package
-> StegGate + coherence evaluation
-> canonical heartbeat-owned local model process
-> persistent local runtime proof
-> TVC route evaluation
-> ROUTE_ADMITTED / credential_requirement NONE
-> private or loopback StegVerseLocalHTTPProviderClient
-> provider response + measured usage
-> provider-usage persistence
-> Master Records custody/reconstruction
-> same-execution transition reconstruction
```

The adapter does not own the model process, heartbeat, route authority, or Master Records custody.

Canonical ownership:

```text
local model/runtime: StegVerse-002/micro-node-runtime#16/#22
heartbeat/carrier lifecycle: StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001
credential semantics: TC/TVC
route authority: StegVerse-Labs/TVC
provider transport/usage evidence: StegVerse-org/LLM-adapter
custody/reconstruction: master-records/orchestration
```

## No GitHub-token production dependency

GitHub repository access is not part of the production inference path.

```text
github_token_required_for_production: false
github_actions_production_role: false
credential_authority_model: TC/TVC
canonical_local_route_credential_requirement: NONE
```

GitHub Actions, Render, Cloudflare, Vercel, GitHub Models, OpenAI, and Anthropic are not canonical production heartbeat, inference, route, custody, or availability authorities. Optional hosted-provider interoperability lanes are separate from the canonical sovereign local route.

## Local model/runtime

The descriptive "select a local model/runtime" step has been superseded by an executable local-runtime path owned by `StegVerse-002/micro-node-runtime`.

The canonical implementation includes:

```text
runtime discovery
local model selection
real process launch
loopback/private serving
health proof
real generation
measured token/latency usage
hash-bound runtime proof
clean termination/recovery behavior
```

The repository-local fallback model is `stegverse-reference-lm-v1`, a formally developed local order-2 token-transition language model trained from repository-local corpus data. It guarantees a zero-external-dependency development/inference path and is explicitly not represented as a production-scale foundation LLM.

Runtime discovery prefers a qualifying local `llama.cpp`/GGUF or Ollama model when present and otherwise uses the reference model.

Canonical local-model evidence is recorded in `StegVerse-002/micro-node-runtime/MICRO_NODE_RUNTIME_MIRROR_HANDOFF.md` and `docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md` in that repository.

## LLM-adapter carrier execution

The LLM-adapter's same-carrier executor implementation is complete and released.

Canonical surfaces:

```text
scripts/execute_canonical_sovereign_route.py
tests/test_execute_canonical_sovereign_route.py
tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json
docs/SOVEREIGN_CARRIER_EXECUTION_MIRROR_HANDOFF.md
```

The executor requires an admitted TVC route, binds the exact canonical runtime proof and private endpoint, requires credential class `NONE`, rejects route/execution authority escalation, executes through `StegVerseLocalHTTPProviderClient`, persists request/response hashes and measured usage, and advances into Master Records reconstruction.

## What remains incomplete

Repository implementation completion is not product activation.

The remaining canonical gap is runtime observation of the complete same-carrier sequence:

```text
heartbeat recovery / current fence
-> local model process
-> TVC route admission
-> LLM-adapter carrier execution
-> provider usage persistence
-> provider-usage custody/reconstruction PASS
-> transition custody/reconstruction PASS
-> immutable zero-blocker activation receipt
-> Site activation
-> required Publisher/wiki propagation
```

This continuation is machine-owned. It is not a reason to re-open the completed local-model or carrier-executor implementation tasks.

## Boundary rules

```text
provider output != authority
route admission != execution authority
runtime proof != product activation
usage measurement != admissibility
local persistence != custody
custody receipt != execution authority
reconstruction PASS != execution authority
session archival != activation
```

The adapter must fail closed rather than silently substitute hosted inference, missing credential authority, unverified runtime identity, or incomplete custody evidence into the canonical sovereign route.

## Development and verification

Repository verification remains available through the existing test and verification surfaces, including:

```bash
pytest
python scripts/smoke_governed_session.py
python scripts/verify_goal4.py
pytest tests/test_execute_canonical_sovereign_route.py -v
```

The authoritative current task and release state is `LLM_ADAPTER_MIRROR_HANDOFF.md`. `adapter.capabilities.json` is the machine-readable capability posture.

## Optional interoperability lanes

The repository can still contain hosted-provider clients, fixture providers, Demo/conformance paths, SDK-adjacent integration, free-tier metadata, and system-boundary tooling. Those are optional or bounded interoperability surfaces and must not be mistaken for the canonical production local-model authority path.

## Repository

https://github.com/StegVerse-org/LLM-adapter
