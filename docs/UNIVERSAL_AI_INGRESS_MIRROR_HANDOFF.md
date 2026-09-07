# Universal AI Ingress Mirror Handoff

Issue: #324
Task: `LLMA-UNIVERSAL-AI-INGRESS-324`
Repository: `StegVerse-org/LLM-adapter`
State: `SOURCE_IMPLEMENTATION_IN_PROGRESS_README_COMPLETENESS_PENDING`

## Source of truth

This bounded lane is subordinate to:

```text
docs/LLM_ADAPTER_MIRROR_HANDOFF.md
docs/EXTERNAL_LLM_CONNECTION_CONVERGENCE_MIRROR_HANDOFF.md
tasks/LLMA-EXTERNAL-LLM-CONVERGENCE-306.json
StegVerse-Labs/.github::WorkerCoordinator
Interlock/InTr
TV/TVC
master-records/orchestration
```

It does not reopen the already-released provider convergence implementation. It extends the shared `ProviderRequest` / `ProviderResponse` / `ProviderClient` semantics into one canonical ingress vocabulary and adapter registry.

## Authority boundary

```text
AI ingress envelope authority effect: NONE
transition admission authority: Interlock/InTr
credential/provider-operation authority: TV/TVC
runtime work owner: StegVerse-Labs/.github::WorkerCoordinator
local/resident runtime owner: StegVerse-002/micro-node-runtime
custody/reconstruction authority: master-records/orchestration
heartbeat/oscillator: reference carrier only
GitHub Actions activation authority: NONE
```

Registration, capability description, route selection, source validation, CI success, or merge do not create runtime authority or prove a provider/entity is connected.

## Implemented source

```text
llm_adapter/universal_ai_ingress.py
tests/test_universal_ai_ingress.py
data/preflight/LLMA-UNIVERSAL-AI-INGRESS-324-20260907.json
tasks/LLMA-UNIVERSAL-AI-INGRESS-324.json
```

The new source provides:

1. `AIIngressEnvelope`, layered on the existing `ProviderRequest` rather than a replacement schema.
2. One provider-independent capability vocabulary.
3. One provider-independent confinement vocabulary.
4. One declarative adapter contract and registry.
5. A duplicate-owner audit for canonical provider names and aliases.
6. Fail-closed routing for registered ingress families whose execution remains owned elsewhere.
7. Direct reuse of `execute_governed_external_llm` and `admit_external_llm_egress` for existing Z.ai, DeepSeek, Kimi/Moonshot, and Anthropic execution.

## Provider / entity reconciliation

```text
Z.ai                 -> existing external_llm_connection execution seam
DeepSeek             -> existing external_llm_connection execution seam
Kimi / Moonshot      -> existing external_llm_connection execution seam
Anthropic / Claude   -> existing external_llm_connection execution seam
OpenAI               -> registered identity; execution remains fail-closed here until an existing admitted owner is bound
OpenAI-compatible    -> registered identity family; execution remains fail-closed here until an existing admitted owner is bound
sovereign/local      -> execution owner StegVerse-002/micro-node-runtime; not reimplemented here
resident             -> same sovereign/local owner; not reimplemented here
browser/session      -> bounded entity/session execution path; not reimplemented here
future AI entities   -> must register exactly one canonical owner before execution is admissible
```

Provider-specific transports remain edge translators only. No provider-specific ingress governance schema is created by this task.

## Failure semantics

The universal ingress path fails closed when:

- Interlock/InTr ingress disposition is not `ALLOW`;
- the session/transition/measurement binding is incomplete;
- the ingress receipt hash or carrier reference is absent/invalid;
- purpose, source, or temperature violates the declared confinement;
- an AI identity is unregistered;
- two registry entries claim the same canonical name/alias;
- an adapter is registered but its execution owner is outside the existing external connection seam.

A route directive explicitly records `connected=false` and `runtime_proof=false`. It is architecture/routing evidence only.

## README completeness predicate

Issue #324 materially changes interface, capability, confinement, failure, and ownership semantics. Therefore `README.md` must be updated in this same change set before merge. Until that edit is present and branch validation is green, this task remains source-in-progress.

## Validation target

Minimum branch validation:

```text
pytest tests/test_universal_ai_ingress.py -q
pytest tests/test_external_llm_connection.py -q
pytest tests/test_governed_external_provider_client.py -q
```

Repository/global validation should also run before merge. The registry duplicate-owner audit must remain green against the exact merge head.

## Runtime proof boundary

Even after source merge, `CONNECTED` requires authentic same-execution evidence for:

```text
exact ingress Interlock/InTr ALLOW
-> admitted runtime/provider execution by the existing owner
-> provider/runtime result
-> Master Records custody/reconstruction
-> exact-response Interlock/InTr egress ALLOW
```

Source/CI/merge alone cannot satisfy those predicates.

## Next

1. Complete required `README.md` update.
2. Run exact-head contract/repository validation.
3. Repair any failures without creating duplicate owners.
4. Perform post-build duplicate-owner audit.
5. Merge only after validation and README completeness pass.
6. Continue authentic runtime proof through the existing WorkerCoordinator + Interlock/InTr + TV/TVC + Master Records chain.
