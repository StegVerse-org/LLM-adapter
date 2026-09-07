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
-> TV/TVC credential or non-exportable provider operation
-> provider-specific transport
-> provider response / authority_effect NONE
-> provider usage event
-> Master Records usage/custody submission
-> exact response hash
-> externally-produced egress InTr ALLOW bound to exact response
-> downstream consequence
```

Provider aliases and dispatch are centralized in `llm_adapter/external_llm_connection.py`.

## Provider state

- Z.ai: existing governed InTr transport/executor reused; current implementation still requires the existing TV/TVC credential resolver path until a canonical non-exportable TVC Z.ai operation profile is admitted.
- DeepSeek: existing InTr transport plus existing TVC runtime-profile broker path remains canonical production path.
- Kimi/Moonshot: existing InTr transport plus existing TVC runtime-profile broker path remains canonical production path; exact-response TVC runtime egress admission is completed by this change set.
- Anthropic: existing legacy HTTP client is no longer sufficient for governed production semantics. This change set adds `stegverse.intr.anthropic.transport.v1` plus governed executor semantics. TVC already has an Anthropic non-exportable provider-operation profile; production convergence must bind this executor to that existing broker instead of exposing credential plaintext.

## Demo/test boundary

`StegVerse-org/stegverse-demo-suite` has no ownership, runtime, credential, custody, or production connection role in this lane.

## Runtime proof boundary

Source, CI, merge, public pages, and provider self-description are not live connection evidence. A provider is `CONNECTED` only after authentic same-execution evidence proves ingress ALLOW, TV/TVC operation/credential resolution, provider response, Master Records custody/reconstruction, and exact-response egress ALLOW.

## README completeness

This change materially affects provider/runtime semantics. Repository README update is mandatory before merge. Until that update and validation pass, the preflight remains incomplete and this branch is not admissible for merge.
