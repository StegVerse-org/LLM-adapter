# MIR destination profile propagation mirror handoff

Goal Task ID: `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001`
COSV ID: `50000000100000`
Reusable component: `RTC-STEGVERSE-EGRESS-007`

## Purpose

Preserve the manifest-declared Interlock/InTr destination profile through the existing generic final StegVerse-side egress transition. No MIR-specific transport, scheduler, dispatcher, receiver prerequisite, or second runtime plane is added.

Required invariant:

```text
stegverse.sdk.publisher-return-binding/v1.egress.destination_profile
-> stegverse.llm-adapter.southbound-final-transition/v1.destination_profile
-> stegverse.llm-adapter.southbound-intr-egress-handoff/v1.destination_profile
```

For the owned MIR mirror exercise the exact destination profile is `MIR`, corresponding to `StegVerse-Labs/StegOS/config/external_counterpart_profiles/mir.json`.

## Fail-closed behavior

`prepare_sdk_return_for_intr()` now rejects a missing/empty destination profile. `admit_intr_egress()` independently verifies that the transition-level destination profile exactly matches the InTr handoff profile before recording authentic admission evidence. Profile mutation/substitution after final-transition preparation fails closed.

The profile grants no governance, credential, admission, execution, far-side, or completion authority. Runtime predicates remain false until authentic Interlock/InTr evidence exists.
