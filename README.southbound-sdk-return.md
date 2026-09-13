# LLM Adapter SOUTH SDK return

The LLM Adapter is the final StegVerse-side state-transition surface for external-framework returns whose complete manifest declares `LLM_ADAPTER` as `completion.egress.final_stegverse_transition_surface`.

```text
Publisher -> SDK return binding -> LLM Adapter -> Interlock/InTr -> far-side transition
```

`llm_adapter/southbound_sdk_return.py` consumes exact canonical `stegverse.sdk.publisher-return-binding/v1` bytes, preserves the exact payload/hash, and prepares a non-authorizing InTr egress handoff.

The LLM Adapter transition is not terminal communication. Interlock/InTr remains transition authority for egress admission, and the far-side transition remains required before `communication_complete` can become true.

This surface is separate from provider-response egress. Provider-specific `admit_*_egress` functions remain scoped to provider execution results and are not reused for generic SDK/framework returns.

Source validation grants no runtime, transport, governance, credential, or completion authority.
