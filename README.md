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

## Ecosystem Chat distributed LLM service

Until a fully realized native Ecosystem Chat LLM exists, the intended LLM capability is a **distributed service across named model sources**. A canonical Ecosystem Chat request may be represented as a deterministic workload that identifies one or more named sources, binds every contribution to the existing `ProviderRequest` / `ProviderResponse` envelopes, retains source-specific provenance and usage evidence, and packages the contribution set for the existing governance path.

```text
canonical Ecosystem Chat request
-> distributed workload descriptor
-> named source selection
-> one or more source-bound ProviderRequest / ProviderResponse pairs
-> normalized contribution envelopes
-> disagreement / refusal / uncertainty retained as evidence
-> reconciliation request for the existing governance path
-> governed disposition + result
-> source-bound provenance / receipt
-> Master Records custody/reconstruction
```

Supported source-level routing declarations are `single`, `parallel`, `sequential`, `challenge`, and `fallback`. These declarations describe workload execution intent only. They do not create truth by voting, grant admission, or make any model the governance authority.

The canonical sovereign local/private route remains independently sufficient for Ecosystem Chat operation. Optional named external sources may expand capability, comparison, specialization, or fallback behavior, but they must not become mandatory third-party production dependencies. Provider credentials are deployment/runtime configuration and are prohibited from workload, contribution, reconciliation, and governed-result artifacts.

The distributed contract preserves the following distinctions:

```text
model contribution != governed result
model disagreement != failure
model majority != governance authority
provider availability != canonical availability authority
provider credentials != artifact content
source validation != live distributed execution
```

The unfinished 12-lane analysis may later populate source capability profiles and supply evidence for routing, cost, independence, or comparative behavior. It is useful evidence, not an implementation prerequisite.

The future native Ecosystem Chat LLM is a separate model-development target distinguished by governance that participates in reasoning and generation rather than relying primarily on reactive post-generation barriers:

> **No reactive guardrails. Native governance instead.**

The distributed workload contract does not claim that native model exists, and it does not create a second governance engine.

Canonical distributed-workload source surfaces:

```text
llm_adapter/distributed_workload.py
schemas/ecosystem-chat-distributed-llm-workload.schema.json
schemas/ecosystem-chat-llm-contribution.schema.json
schemas/ecosystem-chat-llm-reconciliation-request.schema.json
schemas/ecosystem-chat-governed-result.schema.json
tests/test_distributed_workload.py
scripts/check_distributed_llm_workload.py
docs/DISTRIBUTED_LLM_WORKLOAD_MIRROR_HANDOFF.md
tasks/LLMA-DISTRIBUTED-LLM-WORKLOAD-272.json
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

The canonical implementation includes runtime discovery, local model selection, real process launch, loopback/private serving, health proof, real generation, measured token/latency usage, hash-bound runtime proof, and clean termination/recovery behavior.

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

The distributed named-source workload is an additive capability contract. Its source validation does not satisfy this sovereign activation sequence and does not prove live multi-provider fan-out.

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

The adapter must fail closed rather than silently substitute hosted inference, missing credential authority, unverified runtime identity, incomplete custody evidence, unknown distributed sources, broken hash binding, missing provenance, or provider authority escalation into the canonical sovereign route or distributed workload.

## Development and verification

Repository verification remains available through the existing test and verification surfaces, including:

```bash
pytest
python scripts/smoke_governed_session.py
python scripts/verify_goal4.py
pytest tests/test_execute_canonical_sovereign_route.py -v
pytest tests/test_distributed_workload.py -q
python scripts/check_distributed_llm_workload.py
```

The authoritative current task and release state is `LLM_ADAPTER_MIRROR_HANDOFF.md`. `adapter.capabilities.json` is the machine-readable capability posture.

## Optional interoperability lanes

The repository can still contain hosted-provider clients, fixture providers, Demo/conformance paths, SDK-adjacent integration, free-tier metadata, system-boundary tooling, and named-source distributed LLM contribution lanes. Those are optional or bounded interoperability surfaces and must not be mistaken for the canonical production local-model authority path.

## Repository

https://github.com/StegVerse-org/LLM-adapter
