# Universal AI Ingress Mirror Handoff

Updated: 2026-09-07
Repository: `StegVerse-org/LLM-adapter`
Issue: `#324`
Pull request: `#325` (draft)
Task: `LLMA-UNIVERSAL-AI-INGRESS-324`
Branch: `feat/universal-ai-ingress-324`
State: `SOURCE_IMPLEMENTED_VALIDATION_IN_PROGRESS`

## Canonical purpose

All incoming AI entities converge on one provider-independent StegVerse AI connection model:

```text
AI entity
-> thin provider / transport adapter
-> existing StegOS Universal InTr ingress
-> existing bounded entity sandbox / confinement route
-> existing Interlock / InTr evaluation
-> authorized semantic capability
-> governed egress through the same shared contracts
-> thin provider / transport adapter
```

This task creates no second transport, runtime, credential broker, identity authority, governance engine, receipt system, sandbox runtime, scheduler, provider-operation registry, or browser-session system.

## Canonical owners

```text
Universal InTr transport/backbone/connector registry:
  StegVerse-Labs/StegOS
  stegos/universal_intr_transport.py
  stegos/intr_backbone.py
  specs/universal-intr-connector-profiles.v1.json
  profile external-provider-operation

AI request/response normalization + provider translation + provider evidence:
  StegVerse-org/LLM-adapter
  llm_adapter/provider_request.py
  llm_adapter/provider_client.py
  llm_adapter/external_llm_connection.py

Provider-neutral Chat/session binding:
  StegVerse-org/LLM-adapter
  LLMA-CHAT-SESSION-BINDING-010
  llm_adapter/chat_session_binding.py

Transition authority:
  Interlock/InTr

Credential and provider-operation authority:
  TV/TVC
  config/provider_operation_profiles.json

Runtime scheduling/carrier:
  StegVerse-Labs/.github WorkerCoordinator
  HB/oscillator remains timing/liveness/observability support only

Sovereign/local model runtime:
  StegVerse-002/micro-node-runtime

Confinement route:
  existing LLM-adapter bounded entity_sandbox_runner route and governed session path
  no new sandbox runtime is authorized by this task

Custody/reconstruction:
  master-records/orchestration
```

## Duplication-prevention resolution

Potential duplicates discovered and resolved:

1. Provider-specific InTr envelope schemas already exist for Z.ai, DeepSeek, Kimi/Moonshot, and Anthropic. They survive only as provider-edge wire-binding schemas; they are not independent governance, identity, capability, confinement, route, credential, or evidence contracts.
2. `LLMA-EXTERNAL-LLM-CONVERGENCE-306` already provides one provider-neutral external LLM connection primitive. It is reused and refactored rather than replaced.
3. `STEGOS-UNIVERSAL-INTR-BACKBONE-104` already owns canonical transport construction and one Universal InTr connector-profile registry. LLM-adapter consumes that layer and does not create a second transport registry.
4. StegOS #222 / PR #223 already added the provider-generic `external-provider-operation` profile. It remains the shared transport profile for provider operations.
5. `ProviderRequest`, `ProviderResponse`, and `ProviderClient` already normalize provider-facing inference. `ProviderRequest` is extended with optional `AIIngressContext`; no parallel normalized request/response stack is created.
6. Existing `entity_sandbox_runner` routing represents the current bounded sandbox responsibility. This task records shared confinement requirements and routes to that owner; it does not interpret missing runtime observation as a missing sandbox implementation.
7. `LLMA-CHAT-SESSION-BINDING-010` already owns provider-neutral chat/session binding. Browser/session-mediated access reuses that system and is not modeled as a provider or principal identity.
8. TVC already contains the canonical OpenAI `chat_completion_with_usage` provider-operation profile and vault reference. No new OpenAI route/profile/credential store is admissible in LLM-adapter. The remaining OpenAI predicate is only a thin LLM-adapter exact-request/response bridge into that existing TVC operation and the shared InTr path.
9. Direct hosted OpenAI/Anthropic API-key clients represented a stale alternate production credential path. They are demoted to explicit legacy test-only compatibility shims; production hosted execution remains TV/TVC-owned. Their convergence condition is removal once all test/compatibility consumers can use broker fixtures or canonical TVC paths.

## Reuse decisions

```text
PROPOSED RESPONSIBILITY: universal AI transport ingress
NEAREST EXISTING IMPLEMENTATION: StegOS Universal InTr backbone
DECISION: REUSE

PROPOSED RESPONSIBILITY: normalized AI request
NEAREST EXISTING IMPLEMENTATION: llm_adapter/provider_request.py::ProviderRequest
DECISION: EXTEND

PROPOSED RESPONSIBILITY: normalized AI response
NEAREST EXISTING IMPLEMENTATION: llm_adapter/provider_client.py::ProviderResponse
DECISION: REUSE

PROPOSED RESPONSIBILITY: provider adapter compatibility registry
NEAREST EXISTING IMPLEMENTATION: llm_adapter/external_llm_connection.py aliases + provider-neutral dispatch
DECISION: REFACTOR IN PLACE INTO DECLARATIVE DESCRIPTORS

PROPOSED RESPONSIBILITY: confinement / sandbox
NEAREST EXISTING IMPLEMENTATION: bounded entity_sandbox_runner route + governed session routing
DECISION: REUSE; NO NEW RUNTIME

PROPOSED RESPONSIBILITY: browser/session-mediated transport binding
NEAREST EXISTING IMPLEMENTATION: LLMA-CHAT-SESSION-BINDING-010 / chat_session_binding.py
DECISION: REUSE; NOT A PROVIDER ADAPTER

PROPOSED RESPONSIBILITY: identity
NEAREST EXISTING IMPLEMENTATION: provider/model/request/session/transition identities already carried across adapter/runtime paths
DECISION: EXTEND REQUEST CONTEXT; UNKNOWN REMAINS UNKNOWN

PROPOSED RESPONSIBILITY: evidence
NEAREST EXISTING IMPLEMENTATION: request/response hashes + InTr receipts + provider usage + Master Records
DECISION: REUSE

PROPOSED RESPONSIBILITY: hosted credentials
NEAREST EXISTING IMPLEMENTATION: TV/TVC provider_operation_profiles + non-exportable operation broker
DECISION: REUSE; RETIRE DIRECT-KEY PRODUCTION PATHS

PROPOSED RESPONSIBILITY: OpenAI hosted operation
NEAREST EXISTING IMPLEMENTATION: TVC openai/chat_completion_with_usage provider profile
DECISION: REUSE; THIN LLM-ADAPTER BRIDGE REMAINS
```

## Implemented shared contract

`ProviderRequest` remains the normalized inference request. Optional `AIIngressContext` carries provider-independent ingress facts without changing historical serialization/hashing when the context is absent. It distinguishes:

- StegVerse entity identity;
- provider identity;
- model identity;
- transport identity;
- adapter identity/version;
- session/conversation/transition/execution identities;
- claimed vs requested semantic capabilities;
- authority declaration;
- confinement profile and resource/network/filesystem/tool/persistence permissions;
- provenance/context lineage;
- evidence requirements;
- failure mode;
- correlation identifiers.

Unknown principal identity remains `UNKNOWN`. Provider name, API key, browser session, transport ID, or model name is never promoted into StegVerse principal identity.

The existing `external_llm_connection.py` now owns one declarative provider compatibility registry. It is not a replacement for the StegOS connector-profile registry: StegOS owns Universal InTr transport profiles, while LLM-adapter records provider-edge compatibility and dispatch. Registry discovery has `authority_effect = NONE` and grants no admission.

Current registry posture:

```text
Z.ai              -> existing shared external TVC connection; credential TV/TVC
DeepSeek          -> existing shared external TVC connection; credential TV/TVC
Kimi/Moonshot     -> existing shared external TVC connection; credential TV/TVC
Anthropic/Claude  -> existing shared external TVC connection; TVC-only production
OpenAI hosted     -> TVC profile exists; LLM-adapter thin exact-request/egress bridge remains
StegVerse local   -> existing sovereign OpenAI-compatible ProviderClient; credential_requirement NONE
browser/session   -> existing provider-neutral session binding; not a provider registry entry
```

## Capability rule

Capabilities are semantic operations, not provider brands. Shared vocabulary includes conversational inference, structured inference, retrieval, tool invocation, sandboxed code execution, multimodal input/output, artifact generation, local-model inference, agent delegation, governed persistence, repository read/mutation, workflow dispatch, evaluation, simulation, and transport.

Provider compatibility belongs in adapter descriptors and runtime profiles. A provider-specific capability is admissible only where the semantic operation itself is genuinely distinct.

## Adapter rule

A thin provider adapter may own authentication mechanics at the provider edge, endpoint formatting, request serialization, response parsing, streaming/tool/multimodal translation, provider error mapping, usage extraction, rate-limit metadata, retry behavior, and model discovery.

It may not own governance, transition authority, StegVerse identity authority, credential authority, route authority, sandbox policy, evidence authority, semantic capability definitions, runtime scheduling, or custody.

## Failure vocabulary

Common provider-independent classes:

```text
PROVIDER_UNAVAILABLE
INVALID_CREDENTIAL
MISSING_CREDENTIAL
ROUTE_UNAVAILABLE
SANDBOX_UNAVAILABLE
MODEL_UNAVAILABLE
RUNTIME_INACTIVE
RUNTIME_UNOBSERVED
DISPATCH_MISSING
RATE_LIMITED
TIMEOUT
MALFORMED_RESPONSE
UNSUPPORTED_CAPABILITY
INTR_DENY
CONFINEMENT_VIOLATION
IDENTITY_UNRESOLVED
EVIDENCE_INCOMPLETE
TRANSPORT_FAILURE
```

Provider-native errors are translated into these classes at the edge.

## Validation and runtime proof boundary

On PR #325 exact-head validation before the mutation-safety manifest correction, the shared external convergence suite, general validation, Z.ai, DeepSeek, Kimi, distributed-workload, and distributed-executor workflows passed. Work Mutation Safety correctly failed because a fresh manifest was initially absent, then again because the first manifest marked Master Records applicable without explicit refs. Both are repository safety-gate findings, not provider-runtime evidence. A corrected manifest now reuses the existing safety schema and includes explicit Master Records refs; its latest exact-head result remains a release predicate until observed PASS.

Implementation states remain evidence-sensitive:

```text
IMPLEMENTED_UNVALIDATED
TRANSPORT_VALIDATED
TWO_WAY_RUNTIME_VALIDATED
GOVERNED_RUNTIME_VALIDATED
BLOCKED
COMPLETE_RELEASED
```

Source, fixtures, mocks, documentation, constructed payloads, and CI are never converted into authentic runtime proof. A connector is runtime-working only after one correlated authentic execution proves governed request emission, real provider/model processing, response return, governed re-ingress, confinement application, Interlock/InTr evaluation, authorized consumer delivery, and evidence custody/reconstruction.

## Post-build one-owner audit

Current surviving owners:

```text
ingress transport: StegOS Universal InTr
AI normalized request/response: LLM-adapter ProviderRequest / ProviderResponse
provider compatibility/translation: LLM-adapter external_llm_connection + thin edge modules
browser/session binding: LLM-adapter chat_session_binding
identity authority: existing StegVerse identity owners; AI ingress only records asserted/resolved IDs
sandbox/confinement execution: existing entity_sandbox_runner/governed session route
transition authority: Interlock/InTr
credential/provider-operation authority: TV/TVC
runtime scheduling: WorkerCoordinator
local-model runtime: micro-node-runtime
evidence/custody: existing hashes/InTr receipts/provider usage + Master Records
HB/oscillator: observability/timing/liveness only
```

No intentional second owner was introduced. The StegOS connector-profile registry and LLM-adapter provider compatibility registry coexist because they own different semantic layers: transport profile materialization versus provider-edge compatibility/dispatch.

## README determination

`README_CHANGE_REQUIRED = YES` and `README_UPDATED = YES`.

README now documents the universal architecture, singular owners, `AIIngressContext`, identity distinctions, one LLM-adapter compatibility registry, semantic capabilities, shared failures, confinement routing, TV/TVC-only hosted credential production path, local `credential_requirement = NONE`, and authentic-runtime proof boundary.

## Release condition

Do not tag/release until:

- latest Work Mutation Safety exact-head check passes;
- latest general and universal convergence validation passes;
- the task/handoff remain current;
- post-build semantic duplication audit remains one-owner clean;
- the OpenAI thin bridge is either implemented using the existing TVC/OpenAI profile and shared InTr contract or explicitly split into a bounded unresolved predicate without misrepresenting OpenAI as connected;
- provider-specific modules remain edge-only or explicitly marked migration debt;
- evidence claims remain source/runtime accurate;
- no obsolete implementation remains production-authoritative.

Authentic provider runtime proof is required before any provider is promoted to `TWO_WAY_RUNTIME_VALIDATED` or `GOVERNED_RUNTIME_VALIDATED`, and release notes must not claim such proof from CI.
