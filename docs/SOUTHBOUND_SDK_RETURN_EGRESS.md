# Generic SDK return SOUTH egress

This contract implements the final StegVerse-side transition for an external-framework return after Publisher and SDK return assembly have completed.

```text
Publisher
-> SDK `stegverse.sdk.publisher-return-binding/v1`
-> LLM Adapter final StegVerse-side transition
-> Interlock/InTr egress
-> far-side transition
```

The LLM Adapter consumes the exact canonical SDK binding bytes. It does not reinterpret the evidence, select processing, invoke Publisher, or become governance/evidence authority.

`prepare_sdk_return_for_intr()` requires:

- SDK binding schema `stegverse.sdk.publisher-return-binding/v1`;
- communication state `READY_FOR_FINAL_STEGVERSE_EGRESS_TRANSITION`;
- `authority_effect=NONE`;
- `communication_complete=false`;
- manifest-declared final surface `LLM_ADAPTER`;
- transport `INTERLOCK_INTR`;
- `far_side_transition_required=true`.

It emits `stegverse.llm-adapter.southbound-final-transition/v1` and an exact-byte InTr handoff. The SDK binding is preserved as base64 with an exact SHA-256 binding.

This is the final StegVerse-side transition, but it is not terminal communication. The transition retains:

```text
interlock_intr_egress_admitted=false
far_side_transition_observed=false
communication_complete=false
authority_effect=NONE
```

`admit_intr_egress()` may record an authentic Interlock/InTr ALLOW only when the InTr receipt binds the exact SDK return hash. It still leaves the far-side transition and communication completion false.

The far-side transition is outside LLM Adapter authority and remains the terminal communication transition.

This contract is distinct from provider-execution egress. Provider-specific `admit_*_egress` functions remain responsible only for provider-response paths and must not be reused as a substitute for this framework-return transition.

Source validation proves deterministic binding and fail-closed behavior only. It does not prove runtime Publisher execution, runtime SDK assembly, authentic InTr egress, or far-side receipt.
