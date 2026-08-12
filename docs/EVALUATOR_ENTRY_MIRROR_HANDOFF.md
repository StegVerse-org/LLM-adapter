# LLM Adapter Evaluator Entry Mirror Handoff

## Authority

This scoped handoff is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md` and `StegVerse-org/StegVerse-SDK/docs/EVALUATION_RELATIONSHIP_MIRROR_HANDOFF.md`.

```text
goal_id: LLMA-SDK-EVALUATOR-ENTRY-021
repository: StegVerse-org/LLM-adapter
branch: feat/sdk-evaluator-entry-20260811
owner: StegVerse-org/LLM-adapter
role: CLAIMED_FOR_IMPLEMENTATION_AND_VALIDATION
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

## v1 scope

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

## Reuse

The full LLM-adapter remains unchanged as the sovereign provider-transport/evidence owner. The evaluator facade is a narrower admission layer. It does not create a parallel provider registry, TV/TVC route authority, credential broker, heartbeat, model runtime, or custody system.

## Validation

```bash
python -m unittest tests.test_evaluator_entry
```

Validation must prove relationship-hash binding, terms-receipt binding, capability identity, route identity, local-reference-only scope, output-token bound, authority escalation rejection, no credential/provider-selection exposure, no GitHub-token dependency, and deterministic receipt integrity.

## Release condition

Release when SDK producer + adapter consumer + Demo capability catalog are mutually consistent and deterministically validated. Direct live provider execution is not required to validate this admission boundary; public Demo activation of an interactive route requires a separately available local reference runtime.
