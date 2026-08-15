# Manifest Ingress Mirror Handoff

## Authority

```text
goal_id: LLMA-MANIFEST-INGRESS-024
parent_issue: StegVerse-org/LLM-adapter#139
repository: StegVerse-org/LLM-adapter
branch: feat/manifest-ingress-test-mode-20260815
role: CLAIMED_FOR_IMPLEMENTATION
claim_created_at: 2026-08-15T18:49:00-05:00
claim_release_condition: merge or explicit supersession with evidence
```

This scoped handoff extends the released evaluator-entry relationship without creating a demo-specific evaluator, provider registry, credential path, StegGate evaluator, route authority, wallet authority, or custody authority.

## Existing released Demo/Testing support

The Demo/Testing LLM-adapter binding already exists and is released:

```text
StegVerse-org/stegverse-demo-suite/docs/DEMO_EVALUATOR_MIRROR_HANDOFF.md
StegVerse-org/LLM-adapter/docs/EVALUATOR_ENTRY_MIRROR_HANDOFF.md
capability_id: llm_adapter.evaluator_interaction
route: sdk://StegVerse-org/LLM-adapter/evaluator-entry
scope: local_reference_only
github_token_required: false
authority_effect: NONE
```

Therefore issue #139 is a successor capability for governed machine-manifest TEST/LIVE_STREAM ingress, not a missing base Demo evaluator route.

## Installed tranche

```text
profiles/manifest-ingress.v1.json
llm_adapter/manifest_ingress.py
tests/test_manifest_ingress.py
tasks/LLMA-MANIFEST-INGRESS-024.json
```

Implemented behavior:

1. accepts only versioned `stegverse.manifest-ingress.v1` envelopes;
2. supports `TEST` and `LIVE_STREAM` modes;
3. requires exact request/unit/idempotency identity;
4. requires predecessor receipt identity after the first live-stream unit;
5. canonicalizes and hashes the submitted manifest;
6. rejects provider, credential, route, governance, repository, wallet, publication, or release authority escalation;
7. rejects any GitHub-token requirement;
8. delegates only through an injected canonical `governed_ingest` boundary rather than implementing a parallel evaluator;
9. preserves ALLOW/DENY/REVIEW/FAIL_CLOSED distinctly;
10. refuses non-ALLOW consequence execution;
11. requires a manifest receipt locator and verification references from canonical governance;
12. returns a hash-bound, non-authorizing result envelope;
13. strips callback exception detail to avoid leaking secret/runtime information.

## Credential and production boundary

```text
credential_authority: TV/TVC
github_token_runtime_authority: NONE
external_provider_credentials_in_ingress: false
provider_selection_authority: false
sovereign_route_authority_exposed: false
authority_effect: NONE
```

The ingress layer does not choose or launch a model. Sovereign local-model execution remains owned by the released micro-node/TVC/LLM-adapter carrier chain.

## Validation

Required before release:

```text
python -m unittest tests.test_manifest_ingress
existing repository test/readiness checks on final PR head
```

The focused tests cover TEST success, authority-escalation fail-closed behavior, live-stream predecessor enforcement, non-ALLOW execution refusal, and exception-detail suppression.

## Remaining implementation after this tranche

- bind `governed_ingest` to the ordinary canonical manifested-ingestion transaction path rather than a test callback;
- persist/reconcile exact `manifest_receipt_id` through Master Records;
- add durable idempotency/retry state at the canonical ingestion layer;
- add stream-ordering integration tests across persisted receipts;
- add replay/reconstruction proof that does not re-execute external consequences;
- add the SDK user-facing TEST/LIVE_STREAM relationship surface under `StegVerse-org/StegVerse-SDK#16`;
- expose the capability to the Demo suite only after the upstream contract is admitted; do not add a parallel demo-only route.

## Completion state

```text
profile_contract: IMPLEMENTED
adapter_boundary: IMPLEMENTED
focused_tests: IMPLEMENTED / EXECUTION_PENDING
canonical_ingestion_binding: PENDING
Master Records exact-run integration: PENDING
SDK relationship integration: PENDING
Demo suite successor-capability exposure: PENDING_UPSTREAM_ADMISSION
claim: ACTIVE
```

## Canonical continuation

```text
StegVerse-org/LLM-adapter#139
StegVerse-org/StegVerse-SDK#16
StegVerse-Labs/StegCore#85
master-records/orchestration
StegVerse-org/stegverse-demo-suite/docs/DEMO_EVALUATOR_MIRROR_HANDOFF.md
```
