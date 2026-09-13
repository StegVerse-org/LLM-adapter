# SOUTHBOUND SDK return egress mirror handoff

Updated: 2026-09-12
Parent Goal Task ID: `MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001`
Parent COSV ID: `50000000100000`
Status: `ACTIVE / SOURCE IMPLEMENTATION UNDER VALIDATION / RUNTIME UNPROVEN`

## Purpose

Provide the reusable LLM Adapter final StegVerse-side transition for a complete-manifest external-framework return after Publisher and SDK return assembly, without creating a duplicate processor, Publisher format, provider executor, Interlock/InTr implementation, or authority surface.

Canonical architecture:

```text
Publisher
-> SDK stegverse.sdk.publisher-return-binding/v1
-> LLM Adapter final StegVerse-side transition
-> Interlock/InTr egress
-> far-side transition
```

## Reuse decision

`EXTEND` existing LLM Adapter exact-response/fail-closed egress semantics.

Do not route generic SDK/framework returns through provider-specific `admit_*_egress` functions because those functions bind provider execution results. The generic SDK return is already a completed StegVerse result bound to the original initiator by SDK and requires only final protocol/framing transition plus the existing InTr seam.

## Source surfaces

```text
llm_adapter/southbound_sdk_return.py
tests/test_southbound_sdk_return.py
docs/SOUTHBOUND_SDK_RETURN_EGRESS.md
README.southbound-sdk-return.md
.github/workflows/southbound-sdk-return-validation.yml
receipts/work-safety/MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001-southbound-sdk-return.json
```

## Required input boundary

The input must be the exact canonical bytes of:

```text
stegverse.sdk.publisher-return-binding/v1
```

and must retain:

- `communication_state=READY_FOR_FINAL_STEGVERSE_EGRESS_TRANSITION`;
- `authority_effect=NONE`;
- `communication_complete=false`;
- `completion.egress.final_stegverse_transition_surface=LLM_ADAPTER` as projected into the SDK binding;
- `transport=INTERLOCK_INTR`;
- `far_side_transition_required=true`.

## Output boundary

`prepare_sdk_return_for_intr()` emits:

```text
stegverse.llm-adapter.southbound-final-transition/v1
```

plus an exact-byte InTr handoff. The SDK binding bytes are preserved in base64 and bound by SHA-256.

The transition may establish that the LLM Adapter final StegVerse-side surface has been reached, but it may not claim:

```text
Interlock/InTr egress admitted
far-side transition observed
communication complete
```

`admit_intr_egress()` may record `EGRESS_ADMITTED` only from an authentic Interlock/InTr ALLOW binding the exact SDK return hash. It still leaves the far-side transition and communication completion false.

## Authority invariants

- processing selection: admitted manifest capability + route only;
- Publisher: presentation/evidence assembly only;
- SDK: caller-return assembly and initiator binding;
- LLM Adapter: protocol/framing + final StegVerse-side framework transition only;
- Interlock/InTr: egress admission/transition authority;
- far-side system: terminal transition on its side;
- TV/TVC: credential authority where credentials are required;
- GitHub Actions: source validation only;
- this handoff/source change: authority effect `NONE`.

## Validation state

Initial PR head exposed two legitimate failures:

1. dedicated workflow omitted repository import path;
2. Work Mutation Safety required this local mirror handoff and fresh safety manifest.

The workflow import path and safety manifest have been corrected. Revalidation of the exact corrected head is required before merge.

## Runtime boundary

Source validation cannot prove:

- Publisher runtime execution;
- SDK runtime return assembly;
- LLM Adapter runtime visitation;
- authentic Interlock/InTr egress;
- far-side transition;
- terminal communication completion.

All remain `NOT_OBSERVED` until authentic same-execution evidence exists.
