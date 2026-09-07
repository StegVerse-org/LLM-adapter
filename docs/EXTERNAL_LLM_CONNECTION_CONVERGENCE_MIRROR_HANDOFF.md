# External LLM Connection Convergence Mirror Handoff

Updated: 2026-09-07
Repository: `StegVerse-org/LLM-adapter`
Issue: #306
Task: `LLMA-EXTERNAL-LLM-CONVERGENCE-306`
State: `SOURCE_COMPLETE_VALIDATED_MERGE_READY_RUNTIME_PROOF_REQUIRED`

## Goal

Make Z.ai, DeepSeek, Kimi/Moonshot, and Anthropic use one provider-neutral governed connection primitive while retaining provider-specific wire adapters only.

## Reused authority surfaces

- transition admission: existing Interlock/InTr only;
- credential/provider-operation authority: existing TV/TVC only;
- runtime work ownership: existing WorkerCoordinator only;
- custody/reconstruction: existing Master Records only;
- HB/oscillator: reference/carrier only, never execution or admission authority.

This lane creates none of those systems.

## Canonical sequence

```text
ProviderRequest
-> exact provider wire bytes
-> externally-produced ingress InTr ALLOW bound to exact request
-> TV/TVC single-use non-exportable provider operation
-> provider-specific transport
-> provider response / authority_effect NONE
-> provider usage event
-> Master Records usage/custody submission
-> exact response hash
-> externally-produced egress InTr ALLOW bound to exact response
-> downstream consequence
```

Provider aliases and dispatch are centralized in `llm_adapter/external_llm_connection.py`. `llm_adapter/governed_external_provider_client.py` exposes that complete sequence through the existing ProviderClient seam used by Ecosystem Chat distributed execution, and returns a provider response only after both exact ingress and exact-response egress admission validate.

## Canonical task and coordination resolution

```text
root handoff: LLM_ADAPTER_MIRROR_HANDOFF.md
provider handoffs:
  docs/ZAI_INTR_TRANSPORT_MIRROR_HANDOFF.md
  docs/DEEPSEEK_INTR_TRANSPORT_MIRROR_HANDOFF.md
  docs/KIMI_INTR_TRANSPORT_MIRROR_HANDOFF.md
  docs/ANTHROPIC_INTR_MIRROR_HANDOFF.md (or current Anthropic scoped handoff where renamed)
task registry: tasks/LLMA-EXTERNAL-LLM-CONVERGENCE-306.json
Master Records custody/reconstruction authority: master-records/orchestration
runtime owner: StegVerse-Labs/.github WorkerCoordinator resident lane
credential/provider-operation authority: StegVerse-Labs/TVC
cross-repo dependency: StegVerse-Labs/TVC#345 / PR #346
cross-repo dependency state: MERGED as 8faa70644dcb711aee73c976a50dd7a47f4ddf82
```

No duplicate Interlock/InTr, TV/TVC, WorkerCoordinator, heartbeat/oscillator, runtime-profile authority, custody path, or provider-secret architecture is created by this task.

## Provider state

- Z.ai: existing governed InTr transport/executor is reused. This change set adds `stegverse:runtime-profile:llm-adapter-zai:v1`, a TVC non-exportable broker binding, provider-usage/Master Records continuation, and exact-response egress verification. TVC PR #346 is merged and supplies the corresponding `zai` provider-operation profile under the existing broker.
- DeepSeek: existing InTr transport and existing TVC runtime-profile broker path remain the canonical production path and are dispatched through the shared connection primitive.
- Kimi/Moonshot: existing InTr transport and existing TVC runtime-profile broker path remain the canonical production path. Missing exact-response TVC runtime egress admission is repaired in this change set.
- Anthropic: the legacy direct HTTP client is compatibility-only for this purpose. This change set adds `stegverse.intr.anthropic.transport.v1`, `stegverse:runtime-profile:llm-adapter-anthropic:v1`, a TVC non-exportable broker binding using the already-existing Anthropic provider-operation profile, provider-usage/Master Records continuation, and exact-response egress verification.

The direct credential-resolver executors remain compatibility/test surfaces. The convergence target is TVC non-exportable provider execution for all four providers.

## Demo/test boundary

`StegVerse-org/stegverse-demo-suite` has no ownership, runtime, credential, custody, or production connection role in this lane.

## Runtime proof boundary

Source, CI, merge, public pages, and provider self-description are not live connection evidence. A provider is `CONNECTED` only after authentic same-execution evidence proves ingress ALLOW, TV/TVC single-use provider operation, provider response, Master Records custody/reconstruction, and exact-response egress ALLOW.

## Current evidence

```text
shared ProviderClient connection implementation: STAGED
Z.ai TVC runtime binding: STAGED
DeepSeek TVC runtime binding: EXISTING / REUSED
Kimi TVC runtime binding: EXISTING / REUSED; egress verification repaired
Anthropic TVC runtime binding: STAGED
TVC Z.ai provider profile: MERGED / 8faa70644dcb711aee73c976a50dd7a47f4ddf82
README completeness: SATISFIED_ON_BRANCH
machine preflight canonical resolution: PASS
canonical main integrated: 852718d0a1287953ea408511c47b3764e3410b77
validated integrated head: 46bd44149902a171074446a6c0fe7a219e4dceca
local convergence + integrated dependency tests: 68/68 PASS
hosted convergence validation: 34073656131 SUCCESS
hosted repository validation: 34073656180 SUCCESS
hosted Z.ai/Kimi/DeepSeek/distributed validations: ALL SUCCESS
live Z.ai execution: NOT CLAIMED
live DeepSeek execution: NOT CLAIMED
live Kimi execution: NOT CLAIMED
live Anthropic execution: NOT CLAIMED
```

## README completeness

This change materially affects provider/runtime semantics, interfaces, credential boundaries, evidence semantics, and failure behavior. The repository README has been updated in this same branch with the provider-neutral governed connection sequence, source surfaces, authority boundaries, runtime-profile semantics, and source-vs-live-evidence distinction. README completeness is therefore satisfied for this change set.

## Remaining admissibility gate

The preflight has resolved canonical handoffs, task registry, Master Records authority, cross-task coordination, duplicate-creation constraints, and README impact. Exact-head validation passed after integrating current canonical `main`. PR #309 is source-merge ready. Merge and post-merge reconciliation cannot infer live provider execution, activation, custody, or downstream publication.
