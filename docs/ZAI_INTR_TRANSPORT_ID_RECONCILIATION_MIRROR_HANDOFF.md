# Z.ai InTr Transport ID Reconciliation Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Issue: `#284`
Branch: `fix/zai-transport-id-284`
State: `CLAIMED_FOR_BOUNDED_RECONCILIATION`
Authority effect: `NONE_METADATA_AND_INTERFACE_CORRECTION_ONLY`

## Source of truth

This scoped handoff records a newly observed contract mismatch supplied after the prior Z.ai source claim was released. It is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md`, `docs/ZAI_INTR_RELEASE_MIRROR_HANDOFF.md`, existing Interlock/InTr transition authority, TV/TVC credential/route authority, Master Records custody authority, and canonical resident runtime authority.

The prior Z.ai transport/executor implementation remains complete at its recorded scope. This task does not reopen or duplicate that implementation. It corrects one pre-activation v1 identity contract discrepancy.

## Newly observed evidence

The supplied reference contract for `stegverse.intr.zai.transport.v1` specifies:

```text
transport_id pattern: ^zait-[0-9a-f]{64}$
transport_id derivation: "zait-" + sha256(canonical transport basis)
```

Canonical merged source and schema currently use a bare 64-hex SHA-256 transport identifier.

## Machine preflight

```text
canonical sovereign route replaced: false
new heartbeat/oscillator: false
new WorkerCoordinator/scheduler: false
new transition authority: false
new route authority: false
new credential authority: false
new custody authority: false
provider output authority: NONE
live Z.ai execution already observed: false
runtime receipt migration required: false
interface behavior change: true
schema change required: true
deterministic test change required: true
README impact: REQUIRED
root handoff impact before validation/merge: NO_CHANGE_REQUIRED
```

README impact is required because the externally visible v1 transport identifier shape changes. No runtime migration is required because canonical handoffs explicitly state that live Z.ai execution has not been claimed.

## Bounded implementation goal

1. change canonical `transport_id` derivation to `zait-<sha256>`;
2. update the canonical envelope schema to the same pattern;
3. add deterministic tests that bind implementation to schema-visible identifier shape;
4. document the identifier contract in README;
5. validate the exact branch/PR head before merge;
6. preserve all existing authority boundaries and activation distinctions.

## Excluded work

- no `_ref` module duplication into canonical runtime surfaces;
- no hosted-provider activation claim;
- no credential materialization;
- no route or transition authority changes;
- no heartbeat/oscillator changes;
- no Site/Publisher/wiki activation or release claim from source validation alone.

## Completion accounting

```text
bounded mismatch identified: COMPLETE
handoff created: COMPLETE
source correction: PENDING
schema correction: PENDING
tests: PENDING
README: PENDING
PR validation: PENDING
merge: PENDING
live Z.ai execution: NOT CLAIMED
runtime activation: NOT CLAIMED
```

This handoff is the current scoped source of truth for issue #284 until merged, superseded, or explicitly released.
