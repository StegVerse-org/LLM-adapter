# Manifest Ingress Mirror Handoff

## Authority

```text
goal_id: LLMA-MANIFEST-INGRESS-024
parent_issue: StegVerse-org/LLM-adapter#139
repository: StegVerse-org/LLM-adapter
branch: main
role: TRANCHE_1_COMPLETE_RELEASED / PARENT_ACTIVE
claim_created_at: 2026-08-15T18:49:00-05:00
claim_released_at: 2026-08-15T18:56:00-05:00
pull_request: #143
merge_commit: b64004da746f565fecfdbaabe9adcc1f627b0670
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

Issue #139 is therefore the successor capability for governed machine-manifest TEST/LIVE_STREAM ingress, not a missing base Demo evaluator route.

## Released tranche 1

```text
profiles/manifest-ingress.v1.json
llm_adapter/manifest_ingress.py
tests/test_manifest_ingress.py
tasks/LLMA-MANIFEST-INGRESS-024.json
```

Installed behavior:

1. accepts only versioned `stegverse.manifest-ingress.v1` envelopes;
2. supports `TEST` and `LIVE_STREAM` modes;
3. requires exact request/unit/idempotency identity;
4. requires predecessor receipt identity after the first live-stream unit;
5. canonicalizes and hashes the submitted manifest;
6. rejects provider, credential, route, governance, repository, wallet, publication, or release authority escalation;
7. rejects any runtime GitHub-token requirement;
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

## Validation evidence

Focused deterministic execution completed without network or credential use:

```text
TEST success: PASS
authority escalation fail closed: PASS
LIVE_STREAM predecessor requirement: PASS
non-ALLOW consequence execution refusal: PASS
callback exception-detail suppression: PASS
focused predicates: 5/5 PASS
```

All final-head repository workflow runs on `3aed03262e1946e794121e93133ca88b5dc61165` completed successfully:

```text
31915920427 Portable User-LLM Execution Receipt — SUCCESS
31915920445 HIL managed receiver validation — SUCCESS
31915920428 validate — SUCCESS
31915920436 Platform-Agnostic Runtime — SUCCESS
31915920433 Architecture Guard — SUCCESS
31915920432 Validate Provider-Owned Usage Event — SUCCESS
```

Qualification: those pre-existing GitHub-hosted validation workflows use GitHub Actions repository credentials for checkout/setup mechanics. They do not grant runtime/provider authority and are not part of the manifest-ingress production path. Removing that hosted-token validation debt belongs to the separate workflow-minimization/token-cleanup workstream; this tranche itself requires no GitHub token.

## Remaining parent #139 implementation

- bind `governed_ingest` to the ordinary canonical manifested-ingestion transaction path rather than a test callback;
- persist/reconcile exact `manifest_receipt_id` through Master Records;
- add durable idempotency/retry state at the canonical ingestion layer;
- add stream-ordering integration tests across persisted receipts;
- add replay/reconstruction proof that does not re-execute external consequences;
- add the SDK user-facing TEST/LIVE_STREAM relationship surface under `StegVerse-org/StegVerse-SDK#16`;
- expose the capability to the Demo suite only after the upstream contract is admitted; do not add a parallel demo-only route.

## Completion state

```text
profile_contract: COMPLETE_RELEASED
adapter_boundary: COMPLETE_RELEASED
focused_tests: 5/5 PASS
PR_final_head_repository_runs: 6/6 SUCCESS
canonical_ingestion_binding: PENDING
Master Records exact-run integration: PENDING
SDK relationship integration: PENDING
Demo suite successor-capability exposure: PENDING_UPSTREAM_ADMISSION
tranche_1_claim: COMPLETE_RELEASED
parent_issue_139: ACTIVE
```

## Canonical continuation

```text
StegVerse-org/LLM-adapter#139
StegVerse-org/StegVerse-SDK#16
StegVerse-Labs/StegCore#85
master-records/orchestration
StegVerse-org/stegverse-demo-suite/docs/DEMO_EVALUATOR_MIRROR_HANDOFF.md
```
