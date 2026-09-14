# SOUTHBOUND SDK return egress mirror handoff

Updated: 2026-09-14
Originating Goal Task ID: `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`
Active successor Goal Task ID: `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001`
Originating COSV ID: `50000000100000`
Canonical successor issue: `StegVerse-Labs/.github#1891`
Canonical successor handoff: `StegVerse-Labs/Site/docs/MIR_ROUNDTRIP_EGRESS_AUTHENTICITY_MIRROR_HANDOFF.md`
Reusable Task Component Model: `StegVerse-Labs/.github@b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`
Reusable component binding: `RTC-STEGVERSE-EGRESS-007`
Companion transport component: `RTC-INTERLOCK-INTR-TRANSPORT-008`
Component family: `framework_provider_adapter` + reusable transport component
Source implementation merge: `StegVerse-org/LLM-adapter@7c7c43a0171360ce7ed4cc2873b29686147845ae`
Upstream SDK return assembly merge: `StegVerse-org/StegVerse-SDK@b4927ed277c4993662f9e7e4ffd717f677ad5459`
Status: `ACTIVE / REUSABLE SOURCE IMPLEMENTATION MERGED / SUCCESSOR CONSUMPTION NOT YET OBSERVED`

## Purpose

Provide and reuse the LLM Adapter implementation of the **final StegVerse-side egress transition** for complete-manifest external-framework returns after Publisher and SDK return assembly. The implementation remains framework-reusable rather than MIR-specific.

The exhausted originating parent no longer consumes prompts directly. Active downstream coordination now belongs to `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001`.

Canonical composition:

```text
RTC-PUBLISHER-005
-> RTC-SDK-RETURN-006
-> RTC-STEGVERSE-EGRESS-007  [this implementation for LLM_ADAPTER framework paths]
-> RTC-INTERLOCK-INTR-TRANSPORT-008
-> RTC-FARSIDE-FINAL-009
-> authentic external MIR endpoint substitution without choreography redesign
```

## Reuse decision

`REUSE` the existing LLM Adapter exact-response/fail-closed egress semantics. Do not create provider-specific, MIR-specific, or successor-specific parallel return transports.

Provider-specific `admit_*_egress` functions remain scoped to provider execution results. A generic SDK return is already a StegVerse result bound to the original initiator by SDK and therefore requires only the reusable final StegVerse-side transition plus the canonical InTr seam.

## Stable component interface

### Inputs

- exact canonical bytes of `stegverse.sdk.publisher-return-binding/v1`;
- `communication_state = READY_FOR_FINAL_STEGVERSE_EGRESS_TRANSITION`;
- `sdk_return_binding_observed = true` for the SDK binding transition;
- manifest-declared final StegVerse transition surface `LLM_ADAPTER`;
- declared transport `INTERLOCK_INTR`;
- `far_side_transition_required = true`;
- `authority_effect = NONE`;
- `communication_complete = false`.

### Outputs

- `stegverse.llm-adapter.southbound-final-transition/v1`;
- exact-byte InTr handoff bound to the SDK return SHA-256;
- after authentic InTr ALLOW only, an `EGRESS_ADMITTED` observation that still leaves far-side transition and communication completion false.

### Expected evidence

- deterministic SDK-return binding hash;
- deterministic LLM Adapter final-transition object;
- authentic InTr egress receipt bound to the same return hash when runtime executes;
- authentic far-side transition separately, outside this component;
- endpoint provenance independently identifying MIR NODE MIRROR versus authentic external MIR.

### Authority owner/effect

- this reusable component: no authority creation;
- LLM Adapter: protocol/framing and final StegVerse-side framework surface only;
- Interlock/InTr: egress admission and state-transition authority;
- TV/TVC: credential authority where required;
- far-side Interlock/InTr: terminal receive/final transition;
- component reuse does not authorize the next component.

### Failure/reentry semantics

Fail closed on malformed SDK return bytes, wrong schema, wrong communication state, missing SDK return observation, wrong declared egress surface, weakened InTr requirement, authority escalation, hash mismatch, non-ALLOW egress disposition, or mismatched admitted response hash. Reentry requires fresh valid input or authentic corrected InTr evidence; source validation alone cannot advance runtime state.

## Source surfaces

```text
llm_adapter/southbound_sdk_return.py
tests/test_southbound_sdk_return.py
docs/SOUTHBOUND_SDK_RETURN_EGRESS.md
README.southbound-sdk-return.md
.github/workflows/southbound-sdk-return-validation.yml
receipts/work-safety/MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001-southbound-sdk-return.json
```

## Source/validation truth

Reusable source merged as `StegVerse-org/LLM-adapter@7c7c43a0171360ce7ed4cc2873b29686147845ae` with the existing source-validation workflow and task-specific README/documentation surfaces. The source contract already implements the reusable `RTC-STEGVERSE-EGRESS-007` transition and exact InTr handoff preparation.

Historical validation retained for that source path includes:

```text
Work Mutation Safety - Non-Authorizing: SUCCESS
Southbound SDK Return Validation: SUCCESS
repository-wide validate: SUCCESS
```

This handoff reconciliation does not transform those source checks into a claim that the active successor has executed the component against an authentic same-execution SDK/MIR runtime packet.

## Successor current truth

Established:

- SDK exact Publisher-return continuity source/build-test merge `b4927ed277c4993662f9e7e4ffd717f677ad5459`;
- reusable `RTC-STEGVERSE-EGRESS-007` source merge `7c7c43a0171360ce7ed4cc2873b29686147845ae`.

Not yet established for `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001`:

```text
exact SDK return input consumed by this egress component in the required successor execution: false
final StegVerse-side egress transition observed for the required successor execution: false
authentic Interlock/InTr egress admission observed: false
far-side final transition/caller receipt observed: false
authentic external MIR endpoint substitution observed: false
communication_complete: false
```

## Next bounded transition

Materialize or consume an exact `stegverse.sdk.publisher-return-binding/v1` input satisfying SDK PR #242 continuity, without fabricating live/authentic MIR provenance, then execute or classify the existing `RTC-STEGVERSE-EGRESS-007` path. If an authentic runtime carrier/input is unavailable, record the precise missing owner/path and route that condition instead of creating a duplicate egress implementation.

## Runtime boundary

Source implementation and CI do **not** prove:

- live SDK runtime return assembly against authentic MIR;
- LLM Adapter runtime visitation for this successor;
- authentic Interlock/InTr egress;
- far-side transition;
- authentic external MIR substitution;
- terminal communication completion;
- release or deployment.

All remain false until supporting evidence exists.
