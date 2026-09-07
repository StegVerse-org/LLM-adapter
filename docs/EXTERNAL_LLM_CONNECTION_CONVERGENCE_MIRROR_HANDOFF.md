# External LLM Connection Convergence Mirror Handoff

Updated: 2026-09-07
Repository: `StegVerse-org/LLM-adapter`
Issue: #306
Task: `LLMA-EXTERNAL-LLM-CONVERGENCE-306`
State: `SOURCE_IMPLEMENTATION_IN_PROGRESS_RUNTIME_PROOF_REQUIRED`

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

## Provider state

- Z.ai: existing governed InTr transport/executor is reused. This change set adds `stegverse:runtime-profile:llm-adapter-zai:v1`, a TVC non-exportable broker binding, provider-usage/Master Records continuation, and exact-response egress verification. TVC issue #345 / PR #346 stages the corresponding `zai` provider-operation profile under the existing broker.
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
TVC Z.ai provider profile: CROSS-REPO PR #346 / NOT MERGED
source validation: RUNNING
live Z.ai execution: NOT CLAIMED
live DeepSeek execution: NOT CLAIMED
live Kimi execution: NOT CLAIMED
live Anthropic execution: NOT CLAIMED
```

## README completeness

This change materially affects provider/runtime semantics. Repository README update is mandatory before merge. Until that update, TVC #346 resolution, and validation pass, the preflight remains incomplete and this branch is not admissible for merge.
