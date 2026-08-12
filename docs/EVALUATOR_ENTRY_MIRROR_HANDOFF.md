# LLM Adapter Evaluator Entry Mirror Handoff

## Authority

This scoped handoff is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md` and `StegVerse-org/StegVerse-SDK/docs/EVALUATION_RELATIONSHIP_MIRROR_HANDOFF.md`.

```text
goal_id: LLMA-SDK-EVALUATOR-ENTRY-021
repository: StegVerse-org/LLM-adapter
branch: main
owner: StegVerse-org/LLM-adapter
role: COMPLETE_RELEASED
```

## Goal

Expose a deliberately restricted LLM-adapter evaluator facade only through an admitted StegVerse SDK Demo relationship. Do not expose the adapter's broader sovereign provider, route, custody, credential, heartbeat, repository, wallet, or internal evidence surfaces.

## Required sequence

```text
Demo TOS + TOU accepted
-> SDK relationship receipt
-> relationship admits llm_adapter.evaluator_interaction
-> SDK builds exact evaluator LLM request envelope
-> LLM-adapter verifies relationship + request hashes
-> local-reference-only evaluator execution
-> bounded measured response receipt
-> SDK/evaluator
```

## Released v1 scope

```text
capability_id: llm_adapter.evaluator_interaction
route: sdk://StegVerse-org/LLM-adapter/evaluator-entry
evaluation_model_scope: local_reference_only
max_output_tokens: 512
provider_selection_authority: false
provider_credentials_exposed: false
sovereign_route_authority_exposed: false
github_token_required: false
third_party_execution_platform_required: false
authority_effect: NONE
```

Provider comparison or arbitrary provider selection is not part of evaluator-entry v1. It requires a separately catalogued SDK capability and governance decision.

## Canonical surfaces

```text
llm_adapter/evaluator_entry.py
tests/test_evaluator_entry.py
docs/EVALUATOR_ENTRY_MIRROR_HANDOFF.md
StegVerse-org/StegVerse-SDK/stegverse/evaluator_llm_entry.py
StegVerse-org/stegverse-demo-suite/config/evaluator_capability_catalog.json
```

## Validation evidence

Local deterministic validation performed 2026-08-12 without GitHub Actions or hosted runtime:

```text
python -m unittest tests.test_evaluator_entry
result: 4/4 PASS
cross_repository_contract: Demo terms -> SDK relationship -> SDK LLM request -> independent adapter verification -> bounded local-reference receipt PASS
credential/provider escalation negative cases: PASS
github_token_required: false
third_party_execution_platform_required: false
```

The full LLM-adapter remains unchanged as the sovereign provider-transport/evidence owner. The evaluator facade is a narrower admission layer and creates no parallel provider registry, TV/TVC authority, credential broker, heartbeat, model runtime, or custody system.

## Release state

```text
implementation: COMPLETE
validation: COMPLETE
integration: COMPLETE
claim: COMPLETE_RELEASED
public evaluator route availability: OPTIONAL / requires an available local reference runtime
frozen evaluator package dependency on live LLM route: NONE
```

If the local reference runtime is unavailable, only this optional interactive capability is unavailable; the frozen evaluator package and StegVerse continuity remain operational.
