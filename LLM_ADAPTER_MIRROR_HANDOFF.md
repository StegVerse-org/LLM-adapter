# LLM Adapter Mirror Handoff

## Source of truth

This file is the current handoff and task source of truth for `StegVerse-org/LLM-adapter`.

## Active goal

```text
Goal: LLM-origin governed transition candidate emission
Phase: emitter-fixture-validator-tests-and-aggregate-installed
Result: LOCAL_IMPLEMENTATION_INSTALLED_VALIDATION_PENDING
```

Goal 7 bounded free-tier trust activation and decision-authority compatibility remain installed as supporting surfaces for the active transition-candidate goal.

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

## Installed transition-candidate files

```text
llm_adapter/transition_candidate.py
examples/llm_transition_candidate.json
scripts/verify_llm_transition_candidate.py
tests/test_transition_candidate.py
scripts/verify_goal4.py
scripts/verify_goal4_full.py
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

## Installed free-tier trust surface

```text
docs/FREE_TIER_TRUST_POLICY.md
examples/free_tier_trust_policy.json
llm_adapter/free_tier_quota.py
llm_adapter/free_tier_limits.py
llm_adapter/ai_entry_backend_service.py
adapter.capabilities.json
scripts/verify_free_tier_quota.py
scripts/verify_free_tier_limits.py
scripts/verify_ai_entry_free_tier_metadata.py
scripts/verify_free_tier_capability_manifest.py
tests/test_free_tier_quota.py
tests/test_free_tier_limits.py
tests/test_ai_entry_free_tier_trust_metadata.py
```

## Installed decision-authority compatibility

```text
governance/decision-authority-compatibility.json
reports/decision-authority-compatibility.report.md
```

Observed local decision mapping:

```text
ADMIT -> allowed
DENY -> denied
DEFER -> requires-human-review
FAIL_CLOSED -> fail-closed (reserved)
ADVISORY_ONLY -> advisory-only (reserved)
```

These mappings provide vocabulary compatibility only. LLM-adapter decisions are not transition authority unless supported by policy, delegation, evidence, and commit-time validation.

## Required invariants

```text
provider_output_is_authority == false
comparison_only == true
live_provider_call_enabled == false
credential_surface_enabled == false
provider_secret_required_for_tests == false
receipt_capture_preview_only == true
endpoint_side_effects_performed == false
service_wrapper_live_calls_enabled == false
fixture_mode_default == true
returned_to_origin == true
free_tier_is_bounded_live_use == true
static_demo_is_sufficient_trust_proof == false
quota_allow_is_admissibility == false
quota_allow_is_execution_authority == false
limit_allow_is_admissibility == false
limit_allow_is_execution_authority == false
replay_grants_commit_time_standing == false
reconstruction_grants_commit_time_standing == false
upgrade_changes_admissibility_requirements == false
```

## Canonical verification command

```bash
python scripts/verify_goal4_full.py
```

The full aggregate includes the adapter checks, workflow parity, authority and receipt boundaries, provider capture checks, recovery checks, free-tier checks, and transition-candidate validation.

## Preserved HPS role

```text
StegVerse-org/HPS-runtime -> runtime standing state
StegVerse-Labs/hybrid-collab-bridge -> sibling input normalization
StegVerse-Labs/Ecosystem-Delegation -> governed delegation evaluation
master-records/orchestration -> lifecycle, receipts, custody references, reconstruction
```

## Remaining files or modules to install

```text
StegVerse-org/LLM-adapter:
  - hybrid-collab-bridge normalization adapter for emitted transition candidates

master-records/orchestration:
  - observed workflow evidence record
  - transition_id and run_id lifecycle preservation record

StegVerse-Labs/Site:
  - public projection after governed normalization and receipt evidence are available
```

## Next task

```text
1. Verify the aggregate adapter validation on the resolved PR head.
2. Connect LLM candidate output to hybrid-collab-bridge normalization.
3. Record observed workflow evidence in master-records/orchestration.
4. Preserve transition_id and run_id through delegation and final receipt.
```

## Boundary

A candidate manifest is not execution authority. Adapter ALLOW permits only progression to the next governed boundary.

## Archive readiness

None for the adapter-side preview/service-wrapper boundary remains manual. This handoff contains the complete current transition-candidate, free-tier trust, and decision-authority compatibility state; the complete thread can be archived without needing earlier context.
