# Universal AI Ingress Mirror Handoff

Updated: 2026-09-07
Repository: `StegVerse-org/LLM-adapter`
Issue: `#324`
Task: `LLMA-UNIVERSAL-AI-INGRESS-324`
Branch: `feat/universal-ai-ingress-324`
State: `ACTIVE_UNIQUE_WORK`

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

This task does not create a second transport, runtime, credential broker, identity authority, governance engine, receipt system, sandbox runtime, or scheduler.

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

Transition authority:
  Interlock/InTr

Credential and provider-operation authority:
  TV/TVC

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

1. Provider-specific InTr envelope schemas already exist for Z.ai, DeepSeek, Kimi/Moonshot, and Anthropic. They survive only as provider-edge wire-binding schemas; they must not become independent governance or identity contracts.
2. `LLMA-EXTERNAL-LLM-CONVERGENCE-306` already provides one provider-neutral external LLM connection primitive. Reuse and extend it; do not create another external-provider orchestrator.
3. `STEGOS-UNIVERSAL-INTR-BACKBONE-104` already owns canonical transport construction and one connector registry. LLM-adapter must consume it and must not create a second transport registry.
4. StegOS #222 / PR #223 already added the provider-generic `external-provider-operation` profile. Reuse it for provider operations.
5. `ProviderRequest`, `ProviderResponse`, and `ProviderClient` already normalize provider-facing inference. Extend these seams rather than creating a parallel normalized request/response stack.
6. Existing `entity_sandbox_runner` routing represents the current bounded sandbox responsibility. This task will define shared confinement requirements at the ingress contract and route them to that owner; it will not create a new execution runtime merely because complete OS-level sandbox proof is not yet observed.

## Reuse decision

```text
PROPOSED RESPONSIBILITY: universal AI transport ingress
NEAREST EXISTING IMPLEMENTATION: StegOS Universal InTr backbone
DECISION: REUSE

PROPOSED RESPONSIBILITY: normalized AI request
NEAREST EXISTING IMPLEMENTATION: llm_adapter/provider_request.py::ProviderRequest
DECISION: EXTEND

PROPOSED RESPONSIBILITY: normalized AI response
NEAREST EXISTING IMPLEMENTATION: llm_adapter/provider_client.py::ProviderResponse
DECISION: REUSE / EXTEND ONLY IF REQUIRED

PROPOSED RESPONSIBILITY: provider adapter registry
NEAREST EXISTING IMPLEMENTATION: llm_adapter/external_llm_connection.py provider aliases + dispatch
DECISION: REFACTOR IN PLACE INTO DECLARATIVE DESCRIPTORS

PROPOSED RESPONSIBILITY: confinement / sandbox
NEAREST EXISTING IMPLEMENTATION: bounded entity_sandbox_runner route + governed session routing
DECISION: REUSE; NO NEW RUNTIME

PROPOSED RESPONSIBILITY: identity
NEAREST EXISTING IMPLEMENTATION: provider/model/request/session/transition identities already carried across adapter/runtime paths
DECISION: EXTEND REQUEST CONTEXT; UNKNOWN REMAINS UNKNOWN

PROPOSED RESPONSIBILITY: evidence
NEAREST EXISTING IMPLEMENTATION: request/response hashes + InTr receipts + provider usage + Master Records
DECISION: REUSE
```

## Canonical AI ingress context

The existing `ProviderRequest` remains the normalized inference request. A provider-independent ingress context may be attached without changing provider wire semantics. It distinguishes:

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

Unknown principal identity must remain `UNKNOWN`. Provider name, API key, browser session, transport ID, or model name are not promoted into StegVerse principal identity.

## Capability rule

Capabilities are semantic operations, not provider brands. Canonical examples include conversational inference, structured inference, retrieval, tool invocation, sandboxed code execution, multimodal input/output, artifact generation, local-model inference, agent delegation, governed persistence, repository read/mutation, workflow dispatch, evaluation, simulation, and transport.

Provider compatibility belongs in adapter descriptors and runtime profiles. A provider-specific capability is admissible only when its semantics are genuinely distinct.

## Adapter rule

One descriptor registry is maintained at the existing provider-neutral dispatch seam. A provider adapter may own authentication mechanics, endpoint formatting, serialization, parsing, streaming/tool/multimodal translation, provider error mapping, usage extraction, rate-limit metadata, retry behavior, and model discovery.

A provider adapter may not own governance, transition authority, identity authority, credential authority, route authority, sandbox policy, evidence authority, semantic capability definitions, runtime scheduling, or custody.

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

## Runtime proof boundary

Implementation states remain evidence-sensitive:

```text
IMPLEMENTED_UNVALIDATED
TRANSPORT_VALIDATED
TWO_WAY_RUNTIME_VALIDATED
GOVERNED_RUNTIME_VALIDATED
BLOCKED
COMPLETE_RELEASED
```

Existing canonical vocabulary may be retained where stronger/more specific. Source, fixtures, mocks, documentation, constructed payloads, and CI are never converted into authentic runtime proof.

A connector is only runtime-working after the same execution proves governed request emission, authentic provider/model processing, real response return, governed re-ingress, confinement application, Interlock/InTr evaluation, authorized consumer delivery, and correlated evidence.

## README determination

`README_CHANGE_REQUIRED = YES` because this task materially formalizes the public adapter interface, provider-independent identity/confinement/capability vocabulary, adapter registry semantics, failure semantics, and provider onboarding model.

## Release condition

Do not tag/release until:

- common adapter contract tests pass;
- post-build semantic duplication audit identifies one canonical owner per responsibility;
- README is updated;
- task/handoff are current;
- provider-specific modules are demonstrably edge-only or explicitly marked migration debt;
- evidence claims remain source/runtime accurate;
- any superseded duplicate owner is deprecated/redirected rather than left authoritative.
