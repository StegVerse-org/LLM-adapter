# Distributed LLM Workload Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Issue: `#272`
Branch: `feat/distributed-llm-workload-272`
State: `PREFLIGHT_ADMITTED / SOURCE_IMPLEMENTATION_ACTIVE`
Authority effect: `NONE_CONTRACT_ONLY`

## Source of truth

This bounded lane is subordinate to `docs/ECOSYSTEM_CHAT_MIRROR_HANDOFF.md` and `LLM_ADAPTER_MIRROR_HANDOFF.md`.

Canonical runtime, route, credential, and custody authority remain unchanged:

```text
runtime/carrier: StegVerse-Labs/.github#60 / SHWP-ECOSYSTEM-CHAT-INFERENCE-001
canonical local model: StegVerse-002/micro-node-runtime#16/#22
route authority: StegVerse-Labs/TVC
credential semantics: TC/TVC
custody/reconstruction: master-records/orchestration
```

## Goal

Implement the source contract for an Ecosystem Chat LLM capability that can distribute a canonical request across multiple **named** LLM sources and return a governed result with exact contributor provenance.

The distributed service is the current target architecture until a fully realized native Ecosystem Chat LLM exists.

## Core distinction

Distributed service:

```text
canonical request
-> named source selection
-> one or more provider requests
-> source-bound contributions
-> disagreement / refusal / uncertainty retained
-> governed reconciliation
-> governed result
-> provenance / receipt / custody
```

Future native Ecosystem Chat LLM:

> **No reactive guardrails. Native governance instead.**

This task does not implement or claim the native model.

## Required invariants

1. Every contributing source has a stable `source_id`, provider, and model identity.
2. Provider credentials never appear in workload, contribution, or result artifacts.
3. Duplicate/unknown source IDs fail closed.
4. Contribution request/response hashes bind to existing `ProviderRequest` / `ProviderResponse` envelopes.
5. A model output never grants governance, transition, route, credential, custody, or execution authority.
6. Disagreement is retained as evidence; no voting rule becomes governance authority.
7. Reconciliation packages evidence for the existing governance path; this module does not create a second governance engine.
8. The canonical sovereign local route remains independently sufficient for Ecosystem Chat operation.
9. Optional external named sources may expand capability but cannot become mandatory third-party production dependencies.
10. The unfinished 12-lane analysis is useful source-profile evidence but is not a prerequisite.

## Routing semantics

The source contract supports bounded routing declarations:

- `single`: one named source;
- `parallel`: multiple independent contributions;
- `sequential`: later sources may receive prior contribution refs through a separately governed prompt construction step;
- `challenge`: independent source(s) critique or test a prior contribution without becoming final authority;
- `fallback`: ordered sources may be attempted after declared refusal/failure conditions.

Routing mode describes workload execution intent only. It does not decide admissibility or final truth.

## Source milestones

```text
llm_adapter/distributed_workload.py
schemas/ecosystem-chat-distributed-llm-workload.schema.json
schemas/ecosystem-chat-llm-contribution.schema.json
schemas/ecosystem-chat-governed-result.schema.json
tests/test_distributed_workload.py
scripts/check_distributed_llm_workload.py
tasks/LLMA-DISTRIBUTED-LLM-WORKLOAD-272.json
data/preflight/LLMA-DISTRIBUTED-LLM-WORKLOAD-272-20260906.json
README.md
```

First milestone is deterministic source/fixture validation only. It must not be reported as live OpenAI, Anthropic, DeepSeek, GLM, or any other external-provider execution.

## Successor runtime milestone

After source merge and after current sovereign activation ownership remains intact:

```text
canonical request
-> admitted distributed workload
-> admitted named provider clients
-> bounded fan-out / sequential execution
-> per-source ProviderResponse + usage evidence
-> normalized contribution receipts
-> existing governance reconciliation
-> governed result receipt
-> Master Records custody/reconstruction
```

The local sovereign source should remain available as a qualifying source/fallback so distributed expansion does not turn third-party availability into a production dependency.

## README impact

README update is required in this change set because this task adds a repository interface, new evidence/failure semantics, and changes the meaning of the LLM-adapter's supported Ecosystem Chat capability.

## Completion predicates

1. Machine preflight PASS. COMPLETE.
2. Workload/source/contribution/result source contracts implemented. PENDING.
3. Deterministic fixture tests cover positive and fail-closed paths. PENDING.
4. README updated. PENDING.
5. Repository validation passes. PENDING.
6. No live-provider or activation claim is inferred. REQUIRED.
