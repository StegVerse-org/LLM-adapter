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

Bounded executor support is layered separately. `single`, `parallel`, and `fallback` can be executed over explicitly injected `ProviderClient` instances. `parallel` means independent fan-out over the same canonical input with deterministic retained result ordering; it does not grant scheduler or concurrency authority. Missing or failing optional sources produce explicit `FAILED` contribution evidence, provider refusal remains `REFUSED`, and fallback proceeds in declared workload order until a source returns. `sequential` and `challenge` fail closed until a separately governed derived-input/prompt-construction contract exists. Fixture-provider execution validates this execution mechanism only; it is not evidence of live external named-source execution.

The canonical sovereign local/private route remains independently sufficient for Ecosystem Chat operation. Optional named external sources may expand capability, comparison, specialization, or fallback behavior, but they must not become mandatory third-party production dependencies. Provider credentials are deployment/runtime configuration and are prohibited from workload, contribution, reconciliation, governed-result, and execution-summary artifacts.

The distributed contract preserves the following distinctions:

```text
model contribution != governed result
model disagreement != failure
model majority != governance authority
provider availability != canonical availability authority
provider credentials != artifact content
source validation != live distributed execution
fixture execution != live external provider execution
parallel fan-out semantics != scheduler authority
```

The unfinished 12-lane analysis may later populate source capability profiles and supply evidence for routing, cost, independence, or comparative behavior. It is useful evidence, not an implementation prerequisite.

The future native Ecosystem Chat LLM is a separate model-development target distinguished by governance that participates in reasoning and generation rather than relying primarily on reactive post-generation barriers:

> **No reactive guardrails. Native governance instead.**

The distributed workload and bounded executor do not claim that native model exists, and they do not create a second governance engine.

Canonical distributed-workload and executor source surfaces:

```text
llm_adapter/distributed_workload.py
llm_adapter/distributed_executor.py
schemas/ecosystem-chat-distributed-llm-workload.schema.json
schemas/ecosystem-chat-llm-contribution.schema.json
schemas/ecosystem-chat-llm-reconciliation-request.schema.json
schemas/ecosystem-chat-governed-result.schema.json
schemas/ecosystem-chat-distributed-llm-execution.schema.json
tests/test_distributed_workload.py
tests/test_distributed_executor.py
scripts/check_distributed_llm_workload.py
scripts/check_distributed_llm_executor.py
docs/DISTRIBUTED_LLM_WORKLOAD_MIRROR_HANDOFF.md
docs/DISTRIBUTED_LLM_EXECUTOR_MIRROR_HANDOFF.md
tasks/LLMA-DISTRIBUTED-LLM-WORKLOAD-272.json
tasks/LLMA-DISTRIBUTED-LLM-EXECUTOR-274.json
```

## Central AI Entity Coordination Ingress

All AI entities now have one provider-neutral coordination contract behind the same canonical `ecosystem_chat` entry point used by ChatGPT. The contract is `stegverse.ai_entity_coordination_ingress.v1`.

```text
canonical Ecosystem Chat ingress
-> identify AI entity + provider/model provenance
-> bind entity to ecosystem snapshot + issue refs
-> sandbox-only inspection / diagnosis / proposal / simulation
-> retain each entity AGREE / DISAGREE / ABSTAIN disposition
-> require unanimous agreement from every declared participant
-> unanimous candidate becomes READY_FOR_GOVERNED_IMPLEMENTATION_REVIEW
-> only ChatGPT may carry the candidate into the existing governed mutation path
-> existing Interlock/InTr, TV/TVC, WorkerCoordinator, Master Records, repository, release, and publication gates remain authoritative
```

External AI entities are `SANDBOX_CONTRIBUTOR`s. They may inspect supplied ecosystem evidence, diagnose build issues, propose solutions, simulate those solutions in bounded sandbox artifacts, and participate in consensus. They may not mutate repository or ecosystem state, acquire credentials, select authoritative routes, execute workers, control heartbeat, write custody records, publish, release, or grant governance authority.

The sandbox artifact boundary is `sandbox/ai-entity-coordination/`. Proposed artifacts that escape that root fail closed. Source solution records explicitly preserve `ecosystem_mutation_performed=false` and `authority_effect=NONE`.

ChatGPT is the sole designated ecosystem mutation actor under `mutation_authority=CHATGPT_ONLY_GOVERNED`, but that designation is not independent authority. A unanimous coordination result opens only a non-authorizing implementation-review gate with `authority_effect=NONE_LOCAL`, `requires_intr_admission=true`, and `requires_existing_authority_checks=true`. ChatGPT must still use the already-existing governed implementation path and may not bypass canonical authority.

Consensus is unanimity, not majority voting. Every declared participant must return exactly one `AGREE`, `DISAGREE`, or `ABSTAIN`; any missing disposition, disagreement, or abstention blocks implementation review. Disagreement remains evidence and is never silently collapsed.

Canonical source surfaces:

```text
llm_adapter/ai_entity_coordination_ingress.py
schemas/ai-entity-coordination-ingress.schema.json
tests/test_ai_entity_coordination_ingress.py
docs/AI_ENTITY_COORDINATION_INGRESS_MIRROR_HANDOFF.md
tasks/LLMA-AI-ENTITY-COORDINATION-INGRESS-282.json
data/preflight/LLMA-AI-ENTITY-COORDINATION-INGRESS-282-20260906.json
```

This source contract does not claim live external AI participation, a live process-isolated sandbox, live consensus execution, live ChatGPT mutation, Ecosystem Chat activation, Site activation, or release/tag authorization.

## Z.ai Interlock/InTr transport and governed execution

Z.ai is supported as an **optional hosted-provider interoperability transport** through `stegverse.intr.zai.transport.v1`. It does not replace the canonical sovereign local route and does not acquire admission, route, credential, custody, heartbeat, scheduler, worker, publication, or availability authority.

```text
exact ProviderRequest
-> contemporaneous Interlock/InTr ingress evaluation
-> DENY: no provider call
-> ALLOW: bind exact request hash + transition ID + ingress receipt hash + carrier ref
-> TV/TVC-resolved provider credential supplied only at execution time
-> approved official Z.ai OpenAI-compatible endpoint
-> provider response with authority_effect NONE
-> provider usage event using the existing adapter schema
-> existing Master Records provider-usage submission path
-> retained transport/request/response/custody evidence with no credential material
-> separate Interlock/InTr egress evaluation
-> exact egress ALLOW receipt must bind the provider response hash
-> only the externally admitted downstream transition may attach consequence
```

The implementation allowlists the official global general API base `https://api.z.ai/api/paas/v4` and Coding Plan base `https://api.z.ai/api/coding/paas/v4`. Endpoint profile selection is part of the admitted envelope; a runtime configured for one profile cannot execute an envelope admitted for the other. Credentials remain under TV/TVC authority and are prohibited from serialized transport envelopes, response metadata, evidence, task records, handoffs, provider-usage events, and egress-admission records.

`execute_governed_zai` binds the merged transport to the existing provider-usage and Master Records submission mechanisms. It accepts the credential only as ephemeral execution input, produces non-authoritative provider output, and emits `egress_intr_required=true`. `admit_zai_egress` does not evaluate or grant governance; it verifies an externally produced Interlock/InTr `ALLOW` receipt, an exact SHA-256 receipt identifier, and an admitted response hash equal to the provider response produced by the execution. Its local authority effect is explicitly `NONE_LOCAL`.

Canonical source surfaces:

```text
llm_adapter/zai_intr_transport.py
llm_adapter/zai_intr_executor.py
schemas/zai-intr-transport-envelope.schema.json
tests/test_zai_intr_transport.py
tests/test_zai_intr_executor.py
docs/ZAI_INTR_TRANSPORT_MIRROR_HANDOFF.md
docs/ZAI_INTR_EXECUTOR_MIRROR_HANDOFF.md
tasks/LLMA-ZAI-INTR-TRANSPORT-276.json
tasks/LLMA-ZAI-INTR-EXECUTOR-278.json
```

Source validation proves fail-closed transport, usage-evidence, custody-submission, and exact-response egress-binding semantics only. It is not live Z.ai execution, route admission, credential materialization, authentic Master Records custody/reconstruction, live egress ALLOW, Ecosystem Chat activation, or Site activation evidence.

## No GitHub-token production dependency

GitHub repository access is not part of the production inference path.

```text
github_token_required_for_production: false
github_actions_production_role: false
credential_authority_model: TC/TVC
canonical_local_route_credential_requirement: NONE
```

GitHub Actions, Render, Cloudflare, Vercel, GitHub Models, OpenAI, Anthropic, and Z.ai are not canonical production heartbeat, inference, route, custody, or availability authorities. Optional hosted-provider interoperability lanes are separate from the canonical sovereign local route.

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

The distributed named-source workload, bounded executor, Z.ai transport, governed Z.ai execution wrapper, and AI Entity Coordination Ingress are additive capability implementations. Their source/fixture validation does not satisfy this sovereign activation sequence and does not prove live multi-provider, live coordination, or Z.ai execution.

This continuation is machine-owned. It is not a reason to re-open the completed local-model or carrier-executor implementation tasks.

## Boundary rules

```text
provider output != authority
model agreement != governance authority
unanimous AI agreement != transition authority
sandbox test success != ecosystem mutation authority
ChatGPT implementation eligibility != governance bypass
route admission != execution authority
runtime proof != product activation
usage measurement != admissibility
local persistence != custody
custody receipt != execution authority
reconstruction PASS != execution authority
ingress ALLOW != egress ALLOW
egress receipt verification != local authority grant
session archival != activation
```

The adapter must fail closed rather than silently substitute hosted inference, missing credential authority, unverified runtime identity, incomplete custody evidence, unknown distributed sources, broken hash binding, missing provenance, unsupported derived-input semantics, endpoint-profile drift, missing egress governance, sandbox-boundary escape, incomplete consensus, non-ChatGPT mutation attempts, or provider authority escalation into the canonical sovereign route or distributed workload.

## Development and verification

Repository verification remains available through the existing test and verification surfaces, including:

```bash
pytest
python scripts/smoke_governed_session.py
python scripts/verify_goal4.py
pytest tests/test_execute_canonical_sovereign_route.py -v
pytest tests/test_distributed_workload.py -q
python scripts/check_distributed_llm_workload.py
pytest tests/test_distributed_executor.py -q
python scripts/check_distributed_llm_executor.py
pytest tests/test_zai_intr_transport.py -q
pytest tests/test_zai_intr_executor.py -q
pytest tests/test_ai_entity_coordination_ingress.py -q
```

The authoritative current task and release state is `LLM_ADAPTER_MIRROR_HANDOFF.md`. `adapter.capabilities.json` is the machine-readable capability posture.

## Optional interoperability lanes

The repository can still contain hosted-provider clients, fixture providers, Demo/conformance paths, SDK-adjacent integration, free-tier metadata, system-boundary tooling, named-source distributed LLM contribution lanes, the Z.ai InTr transport, the governed Z.ai execution wrapper, and sandboxed AI Entity Coordination Ingress. Those are optional or bounded interoperability surfaces and must not be mistaken for the canonical production local-model authority path.

## Repository

https://github.com/StegVerse-org/LLM-adapter
