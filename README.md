
## Generic SDK manifest InTr ingress

Issue #354 removes the governance-specific callable as the LLM Adapter's processing selector. Actionable external manifests now require a recognized Node endpoint plus manifest-declared `processing.capability` and `processing.route_id`; the adapter frames that unchanged declaration as non-authorizing Interlock/InTr transfer to the distributed SDK manifest endpoint. Source/provider identity is provenance only and cannot select processing. Missing Node recognition or processing declaration fails closed before endpoint invocation. This is source/CI conformance only; it does not claim authentic runtime transport, SDK execution, Organization custody, or Master Records reconstruction.
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

## KV-backed AI memory context

For `PERSONAL_KV / PERSON / PERSONAL_ASSISTANT_AI`, KnowledgeVault may supply bounded persistent context before the ordinary provider request enters the existing LLM path. KV remains the durable memory authority; the model/provider session remains replaceable and non-authoritative.

```text
already-built Personal-KV context packet
-> exact packet hash
-> externally-produced memory-packet InTr ALLOW
-> llm_adapter/kv_memory_context_bridge.py
-> exact ProviderRequest with KV provenance metadata
-> ordinary provider-request ingress InTr ALLOW
-> existing TV/TVC/provider execution path
-> provider response
-> ordinary exact-response egress InTr ALLOW
```

`llm_adapter/kv_memory_context_bridge.py` rejects secret/cross-authority packet flags, verifies per-entry hashes, requires the Personal-KV authority profile, and requires an external `ALLOW` receipt bound to the exact packet ID and canonical packet hash before adding KV context to a `ProviderRequest`. The packet admission is separate from provider-request admission; neither context nor admission transfers KV authority to the model.

`scripts/materialize_kv_memory_provider_request.py` supports the sovereign resident path. It consumes only resident-local packet/admission/request-input files, rejects credential-like request fields, requires an explicit reconstruction timestamp, and emits one deterministic provider request plus hash. The materialization result explicitly records provider ingress, provider execution, provider egress, and KV writeback as **not observed**. In the canonical `.github` resident binding these bytes remain under fenced bound state rather than GitHub repository state.

Canonical scoped documentation:

```text
docs/KV_AI_MEMORY_CONTEXT_BRIDGE_MIRROR_HANDOFF.md
StegVerse-Labs/.github/docs/KV_AI_MEMORY_RESIDENT_EXECUTION_MIRROR_HANDOFF.md
StegVerse-Labs/continuity-vault-kit/KV_AI_PERSISTENCE_CLASSES_MIRROR_HANDOFF.md
```

Source and CI validation prove only deterministic/fail-closed behavior. They do not prove that private KV bytes were read, that a memory-packet InTr decision occurred, that a model consumed context, or that any resulting memory proposal was admitted back into KV.

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

## Governed external LLM connection convergence

Z.ai, DeepSeek, Kimi/Moonshot, and Anthropic now share one provider-neutral connection primitive instead of separate orchestration semantics. `llm_adapter/external_llm_connection.py` selects only provider-specific transport/runtime adapters. `llm_adapter/governed_external_provider_client.py` implements the existing `ProviderClient` seam used by distributed Ecosystem Chat execution and does not return a provider response until both the exact request and exact response have passed the existing external Interlock/InTr evaluations.

```text
ProviderRequest
-> exact provider wire request hash
-> external Interlock/InTr ingress ALLOW bound to exact request
-> TVC short-lived single-use capability lease
-> TVC non-exportable provider operation
-> provider-specific transport/runtime adapter
-> provider response / authority_effect NONE
-> provider-usage event
-> Master Records provider-usage custody/reconstruction
-> exact provider response hash
-> external Interlock/InTr egress ALLOW bound to exact response
-> ProviderResponse becomes available to the existing distributed executor
```

Production external-provider execution uses TVC non-exportable operations for all four providers. Provider plaintext is not supplied to LLM-adapter in this path. Direct credential-resolver executors remain compatibility/test surfaces and are not the converged production contract. The shared connection module creates no Interlock/InTr, TVC, WorkerCoordinator, heartbeat, route, custody, or governance authority and does not turn provider success into an admissibility decision.

Canonical convergence source surfaces:

```text
llm_adapter/external_llm_connection.py
llm_adapter/governed_external_provider_client.py
llm_adapter/zai_tvc_broker.py
llm_adapter/zai_tvc_runtime_executor.py
llm_adapter/deepseek_tvc_broker.py
llm_adapter/deepseek_tvc_runtime_executor.py
llm_adapter/kimi_tvc_broker.py
llm_adapter/kimi_tvc_runtime_executor.py
llm_adapter/anthropic_intr_transport.py
llm_adapter/anthropic_intr_executor.py
llm_adapter/anthropic_tvc_broker.py
llm_adapter/anthropic_tvc_runtime_executor.py
config/zai-runtime-profile.json
config/deepseek-runtime-profile.json
config/kimi-runtime-profile.json
config/anthropic-runtime-profile.json
tests/test_external_llm_connection.py
tests/test_governed_external_provider_client.py
tests/test_zai_tvc_runtime.py
tests/test_deepseek_tvc_runtime.py
tests/test_kimi_tvc_runtime.py
tests/test_external_anthropic_tvc_runtime.py
docs/EXTERNAL_LLM_CONNECTION_CONVERGENCE_MIRROR_HANDOFF.md
```

`StegVerse-org/stegverse-demo-suite` has no production ownership, runtime, credential, custody, or connection role in this path. Demo/test surfaces may consume a governed connection but cannot become its canonical owner.

Source/CI/merge are not connection evidence. `CONNECTED` requires authentic same-execution ingress ALLOW, TVC provider operation, provider response, Master Records reconstruction, and exact-response egress ALLOW.

## Z.ai Interlock/InTr transport and governed execution

Z.ai is supported as an **optional hosted-provider interoperability transport** through `stegverse.intr.zai.transport.v1`. It does not replace the canonical sovereign local route and does not acquire admission, route, credential, custody, heartbeat, scheduler, worker, publication, or availability authority.

```text
canonical ProviderRequest provenance
-> derive exact outbound Z.ai wire payload: model + messages + temperature
-> canonicalize exact outbound payload and compute request_hash
-> contemporaneous Interlock/InTr ingress evaluation
-> DENY: no TVC lease / no provider operation
-> ALLOW: bind exact wire request_hash + transition ID + ingress receipt hash + carrier ref
-> derive transport_id as zait-<sha256(canonical transport basis)>
-> bind stegverse:runtime-profile:llm-adapter-zai:v1
-> TVC single-use non-exportable provider operation
-> TVC profile zai / chat_completion_with_usage
-> vault://tvc/providers/zai/api-key remains inside TV/TVC authority
-> approved official Z.ai OpenAI-compatible endpoint selected from admitted endpoint_profile
-> provider response with credential material absent and authority_effect NONE
-> provider usage event using the existing adapter schema
-> existing Master Records provider-usage submission path
-> deterministic pre-egress handoff requests ALLOW but never assumes it
-> separate Interlock/InTr egress evaluation
-> exact egress ALLOW receipt must bind the provider response hash
-> only the externally admitted downstream transition may attach consequence
```

The v1 `transport_id` format is `zait-` followed by a lowercase SHA-256 digest. Its digest basis is the protocol version, transition ID, exact wire request hash, ingress receipt hash, carrier reference, and endpoint profile. The envelope `request_hash` binds the exact outbound Z.ai payload rather than the broader adapter `ProviderRequest` object; the broader `ProviderRequest.request_hash` may be retained separately as provenance but is not substituted for the admitted wire hash.

The implementation allowlists the official global general API base `https://api.z.ai/api/paas/v4` and Coding Plan base `https://api.z.ai/api/coding/paas/v4`. Endpoint profile selection is part of the admitted envelope; a runtime configured for one profile cannot execute an envelope admitted for the other. The production connection uses the TVC non-exportable provider-operation profile `zai` and runtime profile `stegverse:runtime-profile:llm-adapter-zai:v1`; credential plaintext remains inside TV/TVC and is prohibited from serialized transport envelopes, response metadata, evidence, task records, handoffs, provider-usage events, and egress-admission records.

`execute_governed_zai_via_tvc_runtime` binds the admitted transport to the existing TVC provider-operation broker, provider-usage event, Master Records submission path, and exact-response egress handoff. The older `execute_governed_zai` credential-resolver path remains compatibility/test-only. Neither executor evaluates or grants governance; `admit_zai_tvc_runtime_egress` verifies a separately produced Interlock/InTr `ALLOW` receipt and exact provider response hash, with local authority effect `NONE_LOCAL`.

The exact outbound bytes are deterministically serialized from the canonical adapter request fields used by the Z.ai payload. Canonical `ProviderRequest` currently represents `temperature` as a numeric value; source validation therefore binds the bytes actually sent, while any future restricted-string/scaled-integer numeric canonicalization contract must be explicitly reconciled rather than silently changing provider typing.

Canonical source surfaces:

```text
llm_adapter/zai_intr_transport.py
llm_adapter/zai_intr_executor.py
llm_adapter/zai_tvc_broker.py
llm_adapter/zai_tvc_runtime_executor.py
config/zai-runtime-profile.json
schemas/zai-intr-transport-envelope.schema.json
tests/test_zai_intr_transport.py
tests/test_zai_intr_executor.py
tests/test_zai_tvc_runtime.py
capability/stegverse-intr-zai-transport.capability.json
docs/ZAI_INTR_TRANSPORT_MIRROR_HANDOFF.md
docs/ZAI_INTR_EXECUTOR_MIRROR_HANDOFF.md
docs/ZAI_INTR_TRANSPORT_ID_RECONCILIATION_MIRROR_HANDOFF.md
tasks/LLMA-ZAI-INTR-TRANSPORT-276.json
tasks/LLMA-ZAI-INTR-EXECUTOR-278.json
```

Source validation proves fail-closed transport identity, exact wire-byte/hash binding, TVC non-exportable operation construction, credential non-export semantics, usage evidence, custody submission, deterministic egress handoff, and exact-response egress binding only. It is not live Z.ai execution, authentic TVC provider use, authentic Master Records custody/reconstruction, live egress ALLOW, Ecosystem Chat activation, or Site activation evidence.

## DeepSeek Interlock/InTr transport and governed execution

DeepSeek is supported as an **optional hosted-provider interoperability transport** through `stegverse.intr.deepseek.transport.v1`. It is additive only and does not replace the canonical sovereign local route or acquire admission, route, credential, custody, heartbeat, scheduler, worker, publication, or availability authority.

The production DeepSeek connection now binds the existing DeepSeek InTr envelope to the canonical runtime profile `stegverse:runtime-profile:hb-intr-resident:v1` and the existing TVC non-exportable provider-operation broker. The runtime profile is carrier/materialization metadata only and grants no execution, admission, route, credential, or transition authority. Another physical machine, Linux-specific runtime, systemd service, or Unix socket path is not a declared DeepSeek runtime requirement.

```text
current device
-> Universal InTr ingress
-> DeepSeek InTr envelope / exact request binding
-> stegverse:runtime-profile:llm-adapter-deepseek:v1
-> base profile stegverse:runtime-profile:hb-intr-resident:v1
-> existing WorkerCoordinator resident execution
-> TVC single-use non-exportable provider operation
-> TVC profile deepseek / chat_completion_with_usage
-> vault://tvc/providers/deepseek/api-key remains inside TV/TVC authority
-> DeepSeek provider result with no credential material returned
-> canonical provider-usage event
-> existing Master Records provider-usage submission path
-> deterministic pre-egress handoff that requests, but never assumes, ALLOW
-> separate Interlock/InTr egress evaluation bound to exact provider response hash
-> current device
```

The v1 transport ID remains `dsit-<sha256>`. The envelope request hash binds the exact admitted DeepSeek transport bytes rather than the broader adapter `ProviderRequest`. Current v1 source explicitly supports `deepseek-v4-flash` and `deepseek-v4-pro`; it does not silently substitute alternate endpoints or models.

For production runtime-profile execution, LLM-adapter does **not** accept or resolve DeepSeek credential plaintext. `llm_adapter.deepseek_tvc_broker` constructs the already-existing TVC non-exportable operation request using only the canonical vault reference, a separately admitted single-use TVC capability lease, the admitted model/prompt bounds, and the InTr transport binding. TVC remains the credential and provider-operation authority. The sanitized TVC result is normalized into the existing `ProviderResponse` shape, provider usage continues through the canonical Master Records path, and the result still requires a separate exact-response InTr egress ALLOW before consequence.

The older `execute_governed_deepseek` direct credential-resolver path remains source-compatible for deterministic validation and compatibility only; it is not the production connection contract after the runtime-profile/TVC-broker binding. Credential material remains prohibited from LLM-adapter artifacts, envelopes, response metadata, provider-usage evidence, Master Records evidence, task records, handoffs, and egress records.

Canonical source surfaces:

```text
llm_adapter/deepseek_intr_transport.py
llm_adapter/deepseek_intr_executor.py
llm_adapter/deepseek_tvc_broker.py
llm_adapter/deepseek_tvc_runtime_executor.py
config/deepseek-runtime-profile.json
schemas/deepseek-intr-transport-envelope.schema.json
tests/test_deepseek_intr_transport.py
tests/test_deepseek_intr_executor.py
tests/test_deepseek_tvc_runtime.py
capability/stegverse-intr-deepseek-transport.capability.json
docs/DEEPSEEK_INTR_TRANSPORT_MIRROR_HANDOFF.md
docs/DEEPSEEK_RUNTIME_PROFILE_TVC_BROKER_MIRROR_HANDOFF.md
tasks/LLMA-DEEPSEEK-INTR-TRANSPORT-289.json
tasks/LLMA-DEEPSEEK-RUNTIME-PROFILE-TVC-BROKER-290.json
```

Source validation of this bridge proves runtime-profile binding, TVC non-exportable operation construction, credential non-export semantics, provider-usage continuation, Master Records integration, and egress-handoff construction only. It does not by itself prove authentic live DeepSeek execution, TVC vault readiness, authentic Master Records reconstruction, or live InTr egress ALLOW.

## Kimi/Moonshot Interlock/InTr transport and governed execution

Kimi/Moonshot is supported as an **optional hosted-provider interoperability transport** through `stegverse.intr.kimi.transport.v1`. It is additive only and does not replace the canonical sovereign local route or acquire admission, route, credential, custody, heartbeat, scheduler, worker, publication, or availability authority.

The production Kimi connection binds an exact Kimi InTr envelope to `stegverse:runtime-profile:llm-adapter-kimi:v1`, derived from the existing resident `stegverse:runtime-profile:hb-intr-resident:v1`, and to the existing TVC Kimi non-exportable provider-operation profile. The admitted provider/model endpoint is `kimi` / `kimi-k3` at the TVC-governed Moonshot endpoint. LLM-adapter does not receive Kimi credential plaintext in this production path.

```text
current device
-> Universal InTr ingress
-> Kimi InTr envelope / exact request binding
-> stegverse:runtime-profile:llm-adapter-kimi:v1
-> base profile stegverse:runtime-profile:hb-intr-resident:v1
-> existing WorkerCoordinator resident execution
-> separately admitted TVC single-use non-exportable provider operation
-> TVC profile kimi / chat_completion_with_usage
-> vault://tvc/providers/kimi/api-key remains inside TV/TVC authority
-> Moonshot/Kimi provider result with no credential material returned
-> canonical provider-usage event
-> existing Master Records provider-usage submission path
-> deterministic pre-egress handoff that requests, but never assumes, ALLOW
-> separate Interlock/InTr egress evaluation bound to exact provider response hash
-> current device
```

The v1 Kimi transport ID is `kmit-<sha256>`. The envelope request hash binds the exact admitted Kimi transport bytes rather than the broader adapter `ProviderRequest`. Current source explicitly admits `kimi-k3` and the existing TVC provider endpoint/profile; alternate endpoints or model aliases are not silently substituted.

`llm_adapter.kimi_tvc_broker` builds the existing TVC non-exportable operation request from a separately admitted single-use TVC lease, canonical vault reference, model/prompt bounds, and exact InTr binding. The returned sanitized TVC result is normalized into `ProviderResponse`; usage continues through the existing Master Records path; and response consequence remains blocked until a separate exact-response InTr egress ALLOW exists. The direct credential-resolver Kimi transport remains compatibility/test-only and is explicitly not the production connection contract. `admit_kimi_tvc_runtime_egress` now enforces the same exact-response egress binding as the other external providers.

Canonical source surfaces:

```text
llm_adapter/kimi_intr_transport.py
llm_adapter/kimi_intr_executor.py
llm_adapter/kimi_tvc_broker.py
llm_adapter/kimi_tvc_runtime_executor.py
config/kimi-runtime-profile.json
schemas/kimi-intr-transport-envelope.schema.json
tests/test_kimi_intr_transport.py
tests/test_kimi_intr_executor.py
tests/test_kimi_tvc_runtime.py
capability/stegverse-intr-kimi-transport.capability.json
docs/KIMI_INTR_TRANSPORT_MIRROR_HANDOFF.md
tasks/LLMA-KIMI-INTR-RUNTIME-292.json
```

Source/CI validation proves the implementation and authority boundaries only. A working Kimi connector is claimed only after authentic same-execution evidence proves InTr ingress, TVC Kimi lease/non-exportable provider execution, an authentic Moonshot response, Master Records custody/reconstruction, and exact-response InTr egress.

## Anthropic/Claude Interlock/InTr transport and governed execution

Anthropic is supported as an **optional, non-authoritative hosted-provider interoperability transport** through `stegverse.intr.anthropic.transport.v1`. It uses the native Messages API at `POST https://api.anthropic.com/v1/messages` and does not replace the canonical sovereign local route or acquire admission, route, credential, custody, heartbeat, scheduler, worker, publication, or availability authority.

The #288 transport is bound to the existing canonical resident runtime rather than a provider-specific runtime:

```text
runtime profile: sovereign-runtime-worker-v1
resident substrate: canonical-resident-substrate-v1
executor: WorkerCoordinator
HB protocol: HB32
runtime capability: bounded_process_execution
task routing direction: INTERNAL
credential authority: TV/TVC
ingress/egress authority: Interlock/InTr
custody/reconstruction: Master Records
```

The task-routing direction `INTERNAL` does not waive provider egress governance. The exact outbound request remains bound to an external Interlock/InTr ingress ALLOW; TV/TVC credential material is resolved only for the admitted execution and must not enter any transport envelope, evidence, usage record, custody handoff, or log; the normalized provider result has `authority_effect = "NONE"` and `egress_intr_required = true`; and consequence remains blocked until a separate external Interlock/InTr egress ALLOW binds the exact response hash.

`canonical_sovereign_route_replaced = false` and `hosted_provider_required = false`. Streaming, Batches, and Files are unsupported in v1 and require separate admitted endpoint profiles. Hashing and lossless content-block normalization are specified in `docs/CANONICALIZATION.md`. Source validation is `python3 scripts/validate_anthropic_intr.py --branch feat/anthropic-intr-runtime-fix-288`.

The provider-neutral convergence path reuses that contract through `anthropic_convergence_bridge.py` and the existing TVC single-use, non-exportable `message_with_usage` operation. It does not retain a second direct-credential Anthropic compatibility path.

Canonical Anthropic surfaces:

```text
llm_adapter/anthropic_intr_transport.py
llm_adapter/anthropic_intr_executor.py
llm_adapter/anthropic_convergence_bridge.py
llm_adapter/anthropic_tvc_broker.py
llm_adapter/anthropic_tvc_runtime_executor.py
config/anthropic-runtime-profile.json
tests/test_anthropic_tvc_runtime.py
schemas/stegverse-intr-anthropic-transport-envelope.schema.json
schemas/stegverse-intr-anthropic-evidence.schema.json
schemas/stegverse-intr-anthropic-capability.json
docs/CANONICALIZATION.md
docs/ANTHROPIC_INTR_MIRROR_HANDOFF.md
examples/reference_transaction.py
scripts/validate_anthropic_intr.py
tests/test_anthropic_intr_transport.py
tests/test_anthropic_content_blocks.py
tests/test_anthropic_intr_executor.py
tests/test_anthropic_adversarial.py
tasks/LLMA-ANTHROPIC-INTR-TRANSPORT-288.json
```

Source/CI validation proves implementation and authority boundaries only. It does not prove a current task-executing WorkerCoordinator, live Claude execution, TV/TVC credential readiness, authentic Master Records custody/reconstruction, exact-response live egress ALLOW, or product activation.

## No GitHub-token production dependency

GitHub repository access is not part of the production inference path.

```text
github_token_required_for_production: false
github_actions_production_role: false
credential_authority_model: TC/TVC
canonical_local_route_credential_requirement: NONE
```

GitHub Actions, Render, Cloudflare, Vercel, GitHub Models, OpenAI, Anthropic, Z.ai, DeepSeek, and Kimi/Moonshot are not canonical production heartbeat, inference, route, custody, or availability authorities. Optional hosted-provider interoperability lanes are separate from the canonical sovereign local route.

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

The KV-backed memory bridge adds a pre-ingress context stage when an exact memory packet is separately admitted; it does not weaken or bypass this runtime sequence. The distributed named-source workload, bounded executor, shared external-LLM connection primitive, Z.ai transport/runtime-profile executor, DeepSeek transport/runtime-profile executor, Kimi transport/runtime-profile executor, and Anthropic transport/runtime-profile executor are additive capability implementations. Their source/fixture validation does not satisfy sovereign activation and does not prove live multi-provider execution.

This continuation is machine-owned. It is not a reason to re-open the completed local-model or carrier-executor implementation tasks.

## Boundary rules

```text
provider output != authority
memory context != authority
memory packet admission != provider request admission
ProviderRequest materialization != provider execution
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

The adapter must fail closed rather than silently substitute hosted inference, missing credential authority, unverified runtime identity, incomplete custody evidence, unknown distributed sources, broken hash binding, missing provenance, unsupported derived-input semantics, endpoint-profile drift, missing egress governance, or provider authority escalation into the canonical sovereign route or distributed workload.

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
pytest tests/test_kv_memory_context_bridge.py -q
pytest tests/test_kv_memory_provider_request_materializer.py -q
pytest tests/test_zai_intr_transport.py -q
pytest tests/test_zai_intr_executor.py -q
pytest tests/test_zai_tvc_runtime.py -q
pytest tests/test_deepseek_intr_transport.py -q
pytest tests/test_deepseek_intr_executor.py -q
pytest tests/test_deepseek_tvc_runtime.py -q
pytest tests/test_kimi_intr_transport.py -q
pytest tests/test_kimi_intr_executor.py -q
pytest tests/test_kimi_tvc_runtime.py -q
pytest tests/test_anthropic_intr_transport.py -q
pytest tests/test_external_anthropic_tvc_runtime.py -q
pytest tests/test_external_llm_connection.py -q
pytest tests/test_governed_external_provider_client.py -q
python3 scripts/validate_anthropic_intr.py --branch feat/anthropic-intr-runtime-fix-288
```

The authoritative current task and release state is `LLM_ADAPTER_MIRROR_HANDOFF.md`. `adapter.capabilities.json` is the machine-readable capability posture.

## Optional interoperability lanes

The repository can still contain hosted-provider clients, fixture providers, Demo/conformance paths, SDK-adjacent integration, free-tier metadata, system-boundary tooling, named-source distributed LLM contribution lanes, and the Z.ai, DeepSeek, Kimi/Moonshot, and Anthropic InTr lanes. Those are optional or bounded interoperability surfaces and must not be mistaken for the canonical production local-model authority path.

## Repository

https://github.com/StegVerse-org/LLM-adapter

## Service Gateway query-secret-safe access logging

The sovereign Service Gateway runtime disables Uvicorn's built-in request-target access log and wraps the fully composed Gateway application in `QuerySecretSafeAccessLogMiddleware`. The Gateway-owned logger records only the HTTP method, canonical ASGI path, and response status. It does not read or serialize the ASGI query string, raw request target, headers, cookies, or request body.

This boundary exists so secret-bearing callback ingress such as `/tvc/google-drive/callback` can be transported without the Service Gateway application persisting OAuth authorization-code or state query material in its access log. TVC remains the callback, provider-session, credential, and provider-operation owner; this logging change transfers none of those responsibilities or authorities to LLM-adapter.

Source tests and CI can prove the logging implementation and fail-closed source boundary only. A source merge is **not** evidence that the active `stegverse.org -> TVC` public path is running this implementation. The Personal-KV Google Drive callback must remain runtime-pending until authentic deployed-ingress observation confirms the active Service Gateway path preserves the same query-safe behavior.

Canonical source surfaces:

```text
llm_adapter/query_safe_access_log.py
llm_adapter/runtime_gateway.py
tests/test_service_gateway_query_safe_logging.py
docs/SERVICE_GATEWAY_QUERY_SECRET_SAFE_INGRESS_MIRROR_HANDOFF.md
tasks/LLMA-SERVICE-GATEWAY-QUERY-SECRET-SAFE-271.json
```


## StegBrowser canonical Master Records relay

The existing Service Gateway can advertise a bounded, credential-nonexporting transport for the immutable StegBrowser runtime-readiness custody receipt. Site discovers the route through the existing hash/health-bound StegVerse node advertisement instead of assuming a fixed host. The browser submits only `stegverse.master-records.state-transition-submission/v1`; the gateway uses the existing TV/TVC-scoped `service_gateway_master_records` server-side credential path to call the sole `master-records/orchestration` state-transition custody API.

The relay is intentionally bound to nonce `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z`, sequence 1, transition `STEGBROWSER_RUNTIME_READINESS_MASTER_RECORDS_CUSTODY`, COSV `40000100100000`, and the exact Node/Interlock/Receipt-1/lease/runtime/exported-bundle evidence tuple. It returns success only when Master Records returns `RECORDED`, reconstruction `PASS`, and exact canonical digest equality with no authority escalation. The browser never receives the Master Records bearer credential.

This is transport over the existing gateway, not a second custody implementation, scheduler, runtime, or authority plane. Source and CI validate the binding only; they do not prove a reachable sovereign gateway, authentic Master Records custody, or reconstruction for the immutable invocation. Scoped continuation: `docs/STEGBROWSER_MASTER_RECORDS_STATE_TRANSITION_RELAY_MIRROR_HANDOFF.md`.


### Canonical resident control-root map binding — 2026-09-21

StegDeploy now includes its already-materialized canonical control root in `STEGVERSE_REPO_ROOTS_JSON` under `StegVerse-Labs/.github`. This lets the existing Healer neutral reusable-task scheduler resolve `.github`-owned children such as `RT-CANONICAL-WORK-PORTABLE-DISPATCH-001` without another checkout or transport. The binding is path-only and non-authorizing.


## Repository hygiene adoption — 2026-09-21

This Wave-1 repository now adopts canonical hygiene goal `HYGIENE-CAUSAL-ROOTS-001` through the shared read-only inventory workflow pinned to `739a611afd70bbe5b8e598b03180e62624fb8459`. Pre-adoption branch census: **268**. The workflow classifies only; it cannot delete refs, close PRs/issues, or treat branch age/name as retirement authority. See `docs/REPOSITORY_HYGIENE_ADOPTION_MIRROR_HANDOFF.md`.


### Machine-owned HIL receiver Gateway projection

The deployed Service Gateway can project the already-running loopback HIL receiver through `/api/hil/*` without conflating it with the Universal InTr `/intr/materialization` upstream. The projection is transport-only, loopback-only, rejects browser authorization/cookie headers, and does not create a second receiver or custody lineage.


## Governed public-wiki publication closure

`GOVERNED-WIKI-PUBLICATION-TRANSITION-001` now reuses the existing Service Gateway TV/TVC-materialized Master Records transport for the publication decision. The adapter validates the exact SDK manifest, posture-bound governed result, and a separately observed external Interlock/InTr `ALLOW` decision; it then submits one canonical state-transition receipt to `master-records/orchestration` and immediately rereads the retained reconstruction. Repository mutation requires only that canonical receipt SHA-256 as caller input and independently reconstructs it before any GitHub API operation. `DENY_PUBLICATION` and `REVIEW_REQUIRED` stop before repository mutation. This adds no custody store, local allow decision, credential path, runtime, scheduler, or direct submitter write surface. See `docs/GOVERNED_WIKI_PUBLICATION_TRANSITION_MIRROR_HANDOFF.md`.


### Governed wiki publication runtime boundary

The governed publication source chain is merged through SDK PRs #307/#308 and LLM-adapter PR #348. Repository mutation now requires canonical Master Records reconstruction of the exact governed publication decision before any GitHub operation. Authentic runtime progression remains separately evidence-gated: no retained external Interlock/InTr ALLOW or `PUBLIC_WIKI_GOVERNED_PUBLICATION_DECISION` closure has yet been observed for `GOVERNED-WIKI-PUBLICATION-TRANSITION-001`. The current state is `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`, not failure or authorization. See `docs/GOVERNED_WIKI_PUBLICATION_TRANSITION_MIRROR_HANDOFF.md`.


## Optional manifest-selected Grok/xAI

The existing distributed Ecosystem Chat workload may declare a named `provider: xai` source (or compatibility alias `grok`) alongside a sovereign local source. `build_http_provider_client("xai", api_key=<execution-scoped key>)` constructs the optional `XAIHTTPProviderClient` at the existing LLM Adapter provider boundary. The caller must first obtain its exact manifested InTr ingress ALLOW and TV/TVC+SKAP execution-scoped credential. This transport never discovers credentials from environment variables and rejects non-xAI HTTPS endpoints. Do not place credentials, cookies, raw personal KV context or provider keys in workload manifests or retained response artifacts.

This is a compatibility adapter for xAI's documented chat-completions endpoint; it preserves reported actual model identity, native measured token usage and provider-side cost ticks when supplied. It fails closed on malformed response or missing usage. The existing distributed executor can independently collect a local and an xAI response and retain an optional provider failure without disabling the sovereign route. No model contribution grants execution, route, custody or governance authority.

Current source tests use deterministic HTTP fixtures only. They prove no real Grok invocation, TVC secret operation, admitted ephemeral StegBrowser lease, InTr ingress/egress, terminal session destruction, Master Records reconstruction or Site activation. xAI Responses API support and true governed challenge/sequential deliberation are separate subsequent integrations. See `docs/XAI_MANIFEST_PROVIDER_MIRROR_HANDOFF.md`.


## Canonical node-standing ingress

The public node advertisement maps existing gateway surfaces to the canonical node-standing contract rather than creating a second ingress host. The contract distinguishes explicit genesis from continuity by a mandatory predecessor key: `null` is explicit generation-1 genesis; established-node continuation carries the canonical predecessor binding. Missing or invalid continuity fails closed and cannot silently re-enroll.

The governed machine-manifest ingress carries this standing evidence into the existing distributed SDK manifest transfer. Processing remains selected by the manifest-declared capability and route; message-content classification is descriptive fallback guidance and cannot substitute a governed declaration. The gateway, advertisement, transport and adapter grant no additional execution or governance authority.

KV-as-established-node and StegBrowser-as-KV-surface are not asserted by this repair.


## Machine-readable continuation instructions

Two non-authorizing instruction profiles exist, and standing is what releases them. `LLM_MACHINE_CONTINUATION` directs a machine that already has a canonical manifest to `llm_adapter.governed_manifest_ingress` and the existing distributed SDK manifest transfer. `EXTERNAL_FRAMEWORK_MANIFEST_CONTINUATION` directs a framework to the SDK-owned `stegverse.manifest_builder.build_manifest` / `stegverse manifest build` and `stegverse.external_framework_runner.manifest_external_framework_submission` / `stegverse external-run` path.

Neither is served by the public advertisement. `GET /api/stegverse-node` names the standing endpoints and states that the continuation is withheld until standing resolves; the profiles are returned by `POST /api/node-standing` on `ALLOW` and from nowhere else. `GET /api/node-standing/readiness` publishes what standing requires — the mandatory `predecessor` key, the two modes, the oscillator-epoch ordering — so a machine can satisfy it on the first attempt instead of discovering the shape by being refused. Readiness is not standing and grants nothing.

`POST /api/node-standing` resolves `ESTABLISH_GENESIS` or `VERIFY_EXISTING` to `ALLOW`, `DENY` or `FAIL_CLOSED`. A `null` predecessor is explicit genesis; an absent `predecessor` key fails closed rather than defaulting to genesis; a failed `VERIFY_EXISTING` stays failed and never silently re-enrolls. The predecessor field set is read off the SDK's own `successor_predecessor_binding` at import rather than restated here, because `local_second_predecessor_semantics_permitted` is false.

### Establishing a healthy node is ingress, and the boundary records it

`llm_adapter/node_ingress_boundary.py` is the ingress boundary. `POST /api/node-standing` is the HTTP transport reaching it, not the place standing is resolved: the boundary resolves standing, records the ingress in this repository's transition ledger, and returns the healthy-node packet carrying the receipt's own digest, so a node cites its arrival rather than asserting it.

The record is a property of the crossing, not of HTTP. `transport` names how the signal arrived — `HTTP` is `INSTALLED`, `INTERLOCK_INTR` is `NOT_YET_ENABLED` — and every other field is identical whichever transport carried it. The next stage puts an external ingress point (an ephemeral StegBrowser, a StegNode, or a device that already understands the manifest protocol) on the far side of Interlock/InTr with its egress at this boundary; that swaps the transport and leaves the boundary and the record unchanged.

`NODE_INGRESS_ADMITTED` carries what makes this the record of ingress: the boundary-issued `node_endpoint`, the declared class, the standing mode and chain position, the health the node was told about, and the continuation profile it was instructed to use. Boundary-issued fields are kept apart from caller-declared ones, because a caller writing `recognized` about itself is the fabricated-identity bypass. Admission is structural, not authenticated, and the record says so rather than letting a chain entry read as proof of who arrived.

Every arrival is recorded, admitted or refused. A state transition is the disposition of an intended action, not only a successful one: the intended action here is `ESTABLISH_A_HEALTHY_NODE` either way, and a signal that arrived and was refused is a transition whose disposition is `DENY`. An earlier version of this boundary resolved standing first and minted only on success, so a refused registration left no trace — the chain then showed only the arrivals that happened to succeed, and a held or dropped signal was indistinguishable from one that never arrived. The two dispositions carry different transition classes, `NODE_INGRESS_ADMITTED` and `NODE_INGRESS_REFUSED`, so no reader can mistake a refusal for an admission: the refused record says `healthy_node_established: false`, `node_endpoint_issued: false`, and names no endpoint, class or continuation, because the boundary issued none. The refusal response carries its own receipt digest, so a refused caller cites its refusal rather than being told nothing happened.

`.stegverse/transition-ledger/emit.py` needed two repairs before it could hold that record. It published HEAD with no lock and no atomic replacement: eight concurrent appends produced eight receipts, five bound to a null predecessor and one reachable from HEAD, orphaning seven. An HTTP ingress boundary takes concurrent arrivals as its normal case, so the append is now serialized and HEAD is replaced atomically. It also ordered by a host clock; progression is `OSCILLATOR_ONLY`, so the chain is ordered by a heartbeat reference derived from the parameters this repository already declares in `.stegverse/heartbeat-awareness.json` — whose `canonical_owner` is `StegVerse-Labs/.github` — and a reference derived from a clock sample marks itself. `observed_at` stays because the ledger contract requires it, and is descriptive only.

### The healthy-node packet selects one profile by node class

A device registers once and is told, in the same response, that it reached a healthy node and what to do next. `POST /api/node-standing` on `ALLOW` returns `healthy_node_established`, the node's own `/health` body as `node_health` — so "healthy" means here what it means there rather than being a separate assertion about it — and the instructions for the class that registered.

The class is the selector. A registering node declares `node_class`: `CONSOLE` to build a manifest with the SDK console, or `LLM_ADAPTER` to interface with the adapter and submit one. `CONSOLE` receives `EXTERNAL_FRAMEWORK_MANIFEST_CONTINUATION`; `LLM_ADAPTER` receives `LLM_MACHINE_CONTINUATION`. Only the selected profile comes back, with the others named in `other_continuation_profiles` and withheld. An undeclared or unrecognised `node_class` fails closed and says what to declare, because handing a console the adapter's instructions is worse than refusing. `GET /api/node-standing/readiness` publishes `continuation_selector` and the class list so a caller satisfies this on the first attempt. The other declared ingress dimensions — substrate, materialization, runtime — are recorded as declared and select nothing: `caller_editable_ingress_source_field` is `FORBIDDEN_AS_AUTHORITATIVE_EVIDENCE`.

### The SDK boundary behind standing

Every crossing of that boundary is recorded. The four surfaces run through one seam, so a surface cannot be added that crosses this boundary without being recorded: standing resolves first, the surface runs, and the crossing is appended to this repository's transition ledger as `SDK_CONTRACT_DISCOVERED`, `SDK_MANIFEST_BUILT`, `SDK_MANIFEST_VALIDATED` or `SDK_MANIFEST_HANDED_OFF` — a handoff, because a receipt reading `SUBMITTED` would imply the transition completed here. The response carries the receipt's digest, so a caller cites the crossing rather than asserting it.

The record carries the disposition of the intended action the crossing arrived with. Each surface declares its `intended_action` — discover the contract, build, validate, hand off — and the record resolves it to `ALLOW` or `DENY`. An earlier version of this boundary asked a second question, did some store change, and used it to mark a contract read and a refused build as not transitions; that is not a definition this ecosystem holds. The disposition *is* the transition, so a refused build is `DENY` rather than an absence, and the correction round trip — refused, then built from the refusal — is two transitions on the chain.

Digests, not payloads. The request and result are bound by `request_sha256` and `result_sha256` so neither can be swapped afterwards, without copying a caller's arguments or a manifest's contents into the chain. A crossing refused for want of standing is recorded too, under `SDK_CROSSING_REFUSED_FOR_WANT_OF_STANDING`: the intended action arrived and its disposition is `DENY`. That record says `surface_was_run: false` and names no node endpoint, generation or predecessor, because the standing boundary issued none — so it cannot be read as a crossing that had standing.


`POST /api/sdk/contract`, `/api/sdk/manifest/build`, `/api/sdk/manifest/validate` and `/api/sdk/manifest/submit` put the SDK's own surfaces behind the same standing check — no token, standing resolved per call, no standing no SDK. The contract surface is discovered from the enforcing code rather than from a published schema copy that could drift, and a build refusal is the SDK's own refusal passed through verbatim, so a caller learns the shape from the authority that enforces it. Validation is side-effect-free, so discovery costs nothing.

### Standing is a property of the crossing, not of the document

Standing evidence no longer travels inside the manifest. `node_endpoint`, `node_standing_mode`, `generation` and `predecessor` are issued by the standing boundary as `manifest_fields` and passed to `process_manifest` as a separate `standing` argument, validated before the manifest is looked at. The manifest handed to the SDK runtime is the manifest the SDK built — `wire_manifest` strips this adapter's bookkeeping, because the runtime refuses unknown top-level fields and a caller writing `recognized: true` about itself is the fabricated-identity bypass. A live stream carries one standing for the stream; every unit still keeps its own manifest and receipt identity.

An `ALLOW` result is only accepted when an organization transition receipt was observed. The organization ledger is `runtime_reality_authority` and `propagation_gates_organization_runtime_reality` is false, so waiting on a Master Records id would gate organization reality on propagation. A non-`ALLOW` result that claims `consequence_executed` fails closed, and the far-side disposition is preserved in the result rather than collapsed into a local verdict.

An `ALLOW` is structural, not authenticated. The caller still supplies its own identity, `attestation_owner_state` remains `NOT_PROVEN`, and a declared predecessor is checked against the owner's shape rather than recomputed — the SDK's binding function takes the predecessor manifest and result, while a standing request carries the digests only. Both the readiness and the disposition say so in their own fields. Source regressions exercise both standing modes and both released profiles. Authentic deployed discovery, external transport, far-side InTr admission and organization custody remain separate runtime proof.



## Test 5/6 external submission boundary — 2026-10-02

External instructions terminate at `SUBMIT_CANONICAL_MANIFEST` and `RETAIN_SUBMISSION_RESULT_AND_EVIDENCE`. Interlock/InTr is `INTERNAL_POST_SUBMISSION`; `EXTERNAL_INTERLOCK_INTR` is deferred to a separate successor expansion after Tests 5/6. This changes the caller instruction boundary, not the retained experiment, Test 5-before-Test 6 ordering, or downstream receipt/custody acceptance. Source tests are not Test 5/6 runtime results.

`SDK_MACHINE_CONTRACT` derives from existing SDK builder signatures, processor/route declarations, return projections and console commands. The adapter consumes that SDK projection instead of maintaining a second instruction recipe. The console wrapper already dispatched manifest/external-run; its top-level help omitted them. Shared dispatch/help declarations repair that discovery mismatch.

The external-framework helper currently reports `SDK_LOCAL_MANIFEST_HANDOFF`; it does not prove receiver observation. Adapter predecessor checks establish structural validity only, not authenticated standing. Production endpoint binding, authentic standing, runtime execution, deployment and custody remain NOT_PROVEN. No endpoint, runtime, credential path or authority was created.


## Ecosystem Chat capability-addressed route selection

The canonical hybrid-collab `CapabilityDescriptor` may be supplied to the existing LLM-adapter SDK manifest-build crossing as non-authoritative selection input. The adapter does not invent a route: an `AVAILABLE` external text/reasoning descriptor whose execution constraints require an ephemeral surface maps only to the already-published `stegbrowser / stegverse.route.stegbrowser.v1` processing pair. Its provider/model identity must match the processor request, and the execution primitive remains `llm_adapter.external_llm_connection`.

`UPGRADE_REQUIRED` and `PURCHASE_REQUIRED` stop before manifest construction or provider execution and are returned through the same recorded SDK build crossing with disposition `DENY`. They are not rewritten as `PROVIDER_UNAVAILABLE`, and no free/local/alternate provider is silently selected. Other capability work classes remain explicit non-ALLOW until an existing compatible execution adapter is installed; they are not coerced into text/reasoning. Descriptor authority remains `NONE`, and successful provider outputs still require independent retained observations with `authority_effect=NONE`.


### StegBrowser owner clarification

Current StegVerse-SDK main resolves the `stegbrowser / stegverse.route.stegbrowser.v1` path through the installed StegBrowser owner `stegbrowser.llm_browser_execution.execute_manifested_llm_browser_operation`. Therefore the capability-selection metadata names StegBrowser as the execution owner. `llm_adapter.external_llm_connection` remains a separate provider-neutral text/reasoning primitive; selecting the StegBrowser route does not by itself invoke it. No bridge between these surfaces is inferred or created.


### Test 5/6 machine submission reconciliation

Existing goal: `SVORG-STEGOS-PORTABILITY-001` (parent counter 28/20).
COSV source projection candidate: `20011100100000`, retained with exact metrics
in StegVerse-org/.github `control/task-vector-index.json`; canonical admission
requires review/merge. SDK `machine-contract` projects current declarations and
peer execution profiles. The framework helper uses existing run-manifest routing;
adapter discovery preserves its own receiving operation. External instructions
end at canonical manifest submission and evidence retention. Local handoff is not
receiver observation; external reciprocal Interlock/InTr remains deferred.
See the repository's portability/canonical-standing/machine-contract mirror handoff
for source validation and remaining evidence.
