# External LLM Connection Convergence Mirror Handoff

Updated: 2026-09-07
Repository: `StegVerse-org/LLM-adapter`
Issue: #306
Task: `LLMA-EXTERNAL-LLM-CONVERGENCE-306`
State: `SOURCE_COMPLETE_MERGED_RUNTIME_PROOF_REQUIRED`

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
Anthropic #288 canonical mainline: MERGED / cde350e41d16a9932932b96d77c0dbd37b950284
#309 merge commit: fd6b887a046bc6016f4891d2f595679b6564da36
postmerge main reconciliation: 02346f925c232a47f9df4b11d336e7c36c0e9b62
bounded canonical repair: PR #318
repair merge: f1deee785736075bb5d89a2678fd92d34b3dad1e
latest evidence reconciliation: PR #319 / 3a8d9336ff2791b8dc428950ce8a50282a8722f7
next integration task: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
```

No duplicate Interlock/InTr, TV/TVC, WorkerCoordinator, heartbeat/oscillator, runtime-profile authority, custody path, or provider-secret architecture is created by this task.

## Provider state

- Z.ai: existing governed InTr transport/executor is reused. This change set adds `stegverse:runtime-profile:llm-adapter-zai:v1`, a TVC non-exportable broker binding, provider-usage/Master Records continuation, and exact-response egress verification. TVC PR #346 is merged and supplies the corresponding `zai` provider-operation profile under the existing broker.
- DeepSeek: existing InTr transport and existing TVC runtime-profile broker path remain the canonical production path and are dispatched through the shared connection primitive.
- Kimi/Moonshot: existing InTr transport and existing TVC runtime-profile broker path remain the canonical production path. Missing exact-response TVC runtime egress admission is repaired in this change set.
- Anthropic: canonical task #288 now owns `stegverse.intr.anthropic.transport.v1`. This change set reuses that implementation through a provider-request bridge and the TVC non-exportable broker binding using the already-existing Anthropic provider-operation profile, provider-usage/Master Records continuation, and exact-response egress verification. The superseded direct-credential compatibility route fails closed.

Direct credential-resolver executors remain compatibility/test surfaces for Z.ai, DeepSeek, and Kimi. Anthropic requires its canonical TVC non-exportable path. The convergence target is TVC non-exportable provider execution for all four providers.

## Demo/test boundary

`StegVerse-org/stegverse-demo-suite` has no ownership, runtime, credential, custody, or production connection role in this lane.

## Runtime proof boundary

Source, CI, merge, public pages, and provider self-description are not live connection evidence. A provider is `CONNECTED` only after authentic same-execution evidence proves ingress ALLOW, TV/TVC single-use provider operation, provider response, Master Records custody/reconstruction, and exact-response egress ALLOW.

## Current evidence

```text
shared ProviderClient connection implementation: MERGED
Z.ai TVC runtime binding: MERGED
DeepSeek TVC runtime binding: EXISTING / REUSED
Kimi TVC runtime binding: EXISTING / REUSED; egress verification repaired
Anthropic TVC runtime binding: MERGED / CANONICAL #288 REUSED
TVC Z.ai provider profile: MERGED / 8faa70644dcb711aee73c976a50dd7a47f4ddf82
README completeness: SATISFIED_ON_BRANCH
machine preflight canonical resolution: PASS
canonical main integrated: cde350e41d16a9932932b96d77c0dbd37b950284
PR #309 merge: fd6b887a046bc6016f4891d2f595679b6564da36
validated bounded-repair functional tree: ef3f051dcc3c80192fcbce6deafde8afc0132dc7
published repair head: b7cfe5a0b99842dbe2e2ff08281fc853e37d6fb2
repair PR: #318
repair PR head: 26164ad40209e1ad5302f740236c0ba56678e604
repair merge: f1deee785736075bb5d89a2678fd92d34b3dad1e
repair hosted workflows: 8/8 SUCCESS
canonical Anthropic #288 source validator: 43/43 PASS
local convergence + integrated dependency tests: 127/127 PASS
hosted convergence validation: 34073656131 SUCCESS
hosted repository validation: 34073656180 SUCCESS
hosted Z.ai/Kimi/DeepSeek/distributed validations: ALL SUCCESS
latest evidence reconciliation: PR #319 MERGED / 3a8d9336ff2791b8dc428950ce8a50282a8722f7
live Z.ai execution: NOT CLAIMED
live DeepSeek execution: NOT CLAIMED
live Kimi execution: NOT CLAIMED
live Anthropic execution: NOT CLAIMED
```

## README completeness

This change materially affects provider/runtime semantics, interfaces, credential boundaries, evidence semantics, and failure behavior. The repository README has been updated in this same branch with the provider-neutral governed connection sequence, source surfaces, authority boundaries, runtime-profile semantics, and source-vs-live-evidence distinction. README completeness is therefore satisfied for this change set.

## Remaining admissibility gate

The preflight resolved canonical handoffs, task registry, Master Records authority, cross-task coordination, duplicate-creation constraints, and README impact before functional mutation. PR #309 merged with the superseded Anthropic conflict side; bounded repair PR #318 restored canonical #288 and merged after all eight hosted workflows passed. PR #319 then reconciled that merged validation state without changing runtime behavior or authority semantics. This evidence-only reconciliation requires no README change because it alters no behavior, interface, authority boundary, evidence meaning, prerequisite, dependency, failure behavior, or capability meaning. No merge or validation evidence implies live provider execution, activation, custody, or downstream publication.

## Runtime continuation

The source lane is closed. The canonical successor is `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` in `StegVerse-Labs/.github`. That task must reuse the existing WorkerCoordinator/independent task-control resident lane, Interlock/InTr admission, TV/TVC provider-operation authority, LLM-adapter provider-neutral transport, and Master Records custody/reconstruction. No provider is `CONNECTED` until the authentic same-execution chain produces exact ingress ALLOW, a TV/TVC single-use provider operation, an authentic provider response, Master Records custody/reconstruction PASS, and exact-response egress ALLOW.

Do not reopen this repository's functional convergence source unless that authentic runtime proof exposes a bounded defect.
