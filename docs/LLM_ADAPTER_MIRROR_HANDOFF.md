# LLM Adapter Mirror Handoff

## Current source of truth

This file is the authoritative continuation record for provider-owned usage-event and bounded reasoning-provenance integration until superseded.

## Active goal

```text
Goal: provider-owned LLM usage events and bounded reasoning provenance
Goal number: 8
Schema: schemas/provider_usage_event.schema.json
Fixture: fixtures/provider_usage_event.json
Validator: scripts/verify_provider_usage_event.py
Tests: tests/test_provider_usage_event.py
Workflow: .github/workflows/validate-provider-usage-event.yml
Documentation: docs/PROVIDER_OWNED_USAGE_EVENTS.md
Manual user action required: false
State: IMPLEMENTED_PENDING_CANONICAL_VALIDATION
```

## Required invariants

```text
adapter_is_execution_authority == false
provider_response_is_admissibility == false
model_output_is_publication_authority == false
reasoning_provenance_is_full_chain_of_thought == false
usage_measurement_is_value_claim == false
provider_identity_is_actor_authority == false
return_receipt_required == true
hashes_are_independently_recomputed == true
```

## Completion boundary

Goal 8 is complete only when the canonical fixture validates deterministically, request and response hashes are well formed, token totals reconcile, bounded reasoning provenance excludes full chain-of-thought, all authority dimensions remain false, return-to-origin receipt requirement remains true, adversarial tests pass on Python 3.9, 3.11, and 3.12, canonical CI succeeds, and the work is merged to `main`.

## Successor integration

After Goal 8 is complete, connect provider-owned events to the StegVerse SDK session-usage aggregation path while preserving:

```text
sdk_validation_is_execution == false
aggregation_is_authority == false
session_receipt_is_custody == false
```
