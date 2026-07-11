# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: LLM-origin governed transition candidate emission
Phase: emitter-fixture-validator-tests-and-aggregate-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_VALIDATION_PENDING
```

## Architecture

```text
LLM-origin request
-> emit schema-compatible DECLARED transition candidate
-> hybrid-collab-bridge normalization
-> Ecosystem-Delegation decision
-> master-records/orchestration lifecycle
-> final receipt / custody / reconstruction
-> Site projection
```

The LLM adapter is a sibling input nest. It does not consume SDK output as authority and does not grant execution, delegation, publication, retention, orchestration, final-receipt, or Master-Records authority.

## Installed files

```text
llm_adapter/transition_candidate.py
examples/llm_transition_candidate.json
scripts/verify_llm_transition_candidate.py
tests/test_transition_candidate.py
scripts/verify_goal4.py
```

The emitter uses the canonical relationship shape owned by `master-records/orchestration` and emits:

```text
origin_class: LLM_ADAPTER_INPUT
lifecycle_state: DECLARED
admissibility_result: PENDING
commit_time_validity: PENDING
final_receipt_id: null
master_record_status: NOT_YET_SUBMITTED
```

## Preserved HPS role

```text
StegVerse-org/HPS-runtime -> runtime standing state
StegVerse-Labs/hybrid-collab-bridge -> sibling input normalization
StegVerse-Labs/Ecosystem-Delegation -> governed delegation evaluation
master-records/orchestration -> lifecycle, receipts, custody references, reconstruction
```

## Next task

```text
1. Verify the aggregate adapter validation.
2. Connect LLM candidate output to hybrid-collab-bridge normalization.
3. Record observed workflow evidence in master-records/orchestration.
4. Preserve transition_id and run_id through delegation and final receipt.
```

## Boundary

A candidate manifest is not execution authority. Adapter ALLOW permits only progression to the next governed boundary.

## Archive readiness

This handoff contains the complete current LLM transition-candidate state. Earlier thread context is not required.
