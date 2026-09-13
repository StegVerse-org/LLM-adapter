# SOUTHBOUND SDK return egress mirror handoff

Updated: 2026-09-12
Originating Goal Task ID: `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`
Originating COSV ID: `50000000100000`
Reusable Task Component Model: `StegVerse-Labs/.github@b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`
Reusable component binding: `RTC-STEGVERSE-EGRESS-007`
Companion transport component: `RTC-INTERLOCK-INTR-TRANSPORT-008`
Component family: `framework_provider_adapter` + reusable transport component
Status: `ACTIVE / REUSABLE SOURCE IMPLEMENTATION VALIDATED / MERGE PENDING / RUNTIME UNPROVEN`

## Purpose

Provide the reusable LLM Adapter implementation of the **final StegVerse-side egress transition** for complete-manifest external-framework returns after Publisher and SDK return assembly. This is a reusable capability discovered while executing `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`; it is not permanently MIR-specific and does not create a separate Goal Task because it has no independent goal-level completion semantics.

Canonical composition:

```text
RTC-PUBLISHER-005
-> RTC-SDK-RETURN-006
-> RTC-STEGVERSE-EGRESS-007  [this implementation for LLM_ADAPTER framework paths]
-> RTC-INTERLOCK-INTR-TRANSPORT-008
-> RTC-FARSIDE-FINAL-009
```

The originating MIR Goal Task consumes this component through its reusable component profile. Other Goal Tasks may consume the same component when their complete manifest selects `LLM_ADAPTER` as the final StegVerse-side framework egress surface.

## Reuse decision

`EXTEND` existing LLM Adapter exact-response/fail-closed egress semantics; do not create provider-specific or Goal-Task-specific parallel return transports.

Provider-specific `admit_*_egress` functions remain scoped to provider execution results. A generic SDK return is already a completed StegVerse result bound to the original initiator by SDK and therefore requires only the reusable final StegVerse-side transition plus the canonical InTr seam.

## Stable component interface

### Inputs

- exact canonical bytes of `stegverse.sdk.publisher-return-binding/v1`;
- manifest-declared final StegVerse transition surface `LLM_ADAPTER`;
- declared transport `INTERLOCK_INTR`;
- far-side-transition requirement.

### Outputs

- `stegverse.llm-adapter.southbound-final-transition/v1`;
- exact-byte InTr handoff bound to the SDK return SHA-256;
- after authentic InTr ALLOW only, an `EGRESS_ADMITTED` observation that still leaves far-side transition and communication completion false.

### Preconditions

- `communication_state=READY_FOR_FINAL_STEGVERSE_EGRESS_TRANSITION`;
- `authority_effect=NONE`;
- `communication_complete=false`;
- SDK return binding is exact and hash-verifiable;
- manifest-selected final surface is `LLM_ADAPTER`.

### Expected evidence

- deterministic SDK-return binding hash;
- deterministic LLM Adapter final-transition object;
- authentic InTr egress receipt bound to the same return hash when runtime executes;
- authentic far-side transition separately, outside this component.

### Authority owner/effect

- this reusable component: `NONE` authority creation;
- LLM Adapter: protocol/framing and final StegVerse-side framework surface only;
- Interlock/InTr: egress admission and state-transition authority;
- TV/TVC: credential authority where required;
- far-side Interlock/InTr: terminal receive/final transition;
- component reuse does not authorize the next component.

### Failure/reentry semantics

Fail closed on malformed SDK return bytes, wrong schema, wrong communication state, wrong declared egress surface, weakened InTr requirement, authority escalation, hash mismatch, non-ALLOW egress disposition, or mismatched admitted response hash. Reentry requires a fresh valid input or authentic corrected InTr evidence; source validation alone cannot advance runtime state.

## Source surfaces

```text
llm_adapter/southbound_sdk_return.py
tests/test_southbound_sdk_return.py
docs/SOUTHBOUND_SDK_RETURN_EGRESS.md
README.southbound-sdk-return.md
.github/workflows/southbound-sdk-return-validation.yml
receipts/work-safety/MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001-southbound-sdk-return.json
```

## Duplicate-orchestration rule

Do not implement another MIR-specific or provider-specific generic SDK-result egress path. Goal Tasks must parameterize and consume this reusable component through `RTC-STEGVERSE-EGRESS-007`, then use `RTC-INTERLOCK-INTR-TRANSPORT-008` for the actual governed transport transition.

Historical task-specific source/evidence is retained for provenance and must not be deleted merely because the capability is now reusable.

## Validation state

Exact head `b610eeedd0c32a63cd6f55770fb5928d357ea27b` passed:

- `Work Mutation Safety - Non-Authorizing #53` — SUCCESS;
- `Southbound SDK Return Validation #7` — SUCCESS;
- repository-wide `validate #3466` — SUCCESS.

This handoff update rebinds that validated source to the canonical Reusable Task Component Model; the new exact head must re-run applicable source validation before merge.

## Runtime boundary

The reusable source implementation and CI do **not** prove:

- Publisher runtime execution;
- SDK runtime return assembly;
- LLM Adapter runtime visitation;
- authentic Interlock/InTr egress;
- far-side transition;
- terminal communication completion.

All remain `NOT_OBSERVED` until authentic same-execution evidence exists.
