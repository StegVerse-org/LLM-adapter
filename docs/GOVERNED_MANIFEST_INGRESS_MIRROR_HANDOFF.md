# Governed Manifest Ingress Mirror Handoff

## Authority

```text
goal_id: LLMA-GOVERNED-MANIFEST-INGRESS-001
repository: StegVerse-org/LLM-adapter
branch: main
parent_handoff: LLM_ADAPTER_MIRROR_HANDOFF.md
related_released_handoff: docs/EVALUATOR_ENTRY_MIRROR_HANDOFF.md
issue: #139
implementation_state: INSTALLED_UNVALIDATED
release_state: NOT_RELEASED
```

## Goal

Accept StegVerse-compatible machine manifests from external frameworks/models in finite TEST mode or ordered LIVE_STREAM mode, delegate each unit to the canonical StegVerse governance handler, and return a bounded machine/model-facing governed result envelope.

The adapter is ingress/egress transport. It is not StegGate authority.

## Installed surfaces

```text
llm_adapter/governed_manifest_ingress.py
tests/test_governed_manifest_ingress.py
```

Recent installation commits:

```text
a5f30efcd86c069fe6d22ef4eb665bc805ea9ec2  manifest return projection semantics
fa4e354b6db14e9cef450265f7ea953e59e2cdaf  caller-projection vs custody tests
```

## Modes

```text
TEST        finite manifest or bounded batch
LIVE_STREAM ordered manifest-framed units with per-unit identity/receipt
```

LIVE_STREAM preserves stream identity, sequence, and idempotency while requiring independent governance identity for each unit. The stream itself never becomes the authority object.

## Result envelope

```text
schema: stegverse.llm-adapter.governed-result.v1
governance_state: ALLOW | DENY | REVIEW | FAIL_CLOSED
governed_result
manifest_receipt_id
return_projection
transition_evidence
verification_refs
receipt_refs
consequence_executed
stream_id / sequence when applicable
adapter_is_governance_authority: false
provider_output_grants_consequence_authority: false
```

Malformed manifests, invalid governance states, missing manifest receipt identity, unavailable governance dependencies, stream-order violations, and unsafe non-ALLOW consequence claims fail closed.

## Manifest return-projection boundary

The manifest may declare how transition evidence is projected back to the external caller/LLM:

```text
ALL       -> all user-disclosable transition evidence
SELECTED  -> only named user-disclosable transition classes
NONE      -> no transition-detail projection to the caller
```

This is an egress/disclosure rule only. It does not control canonical ecosystem custody.

Mandatory invariants:

```text
controls_user_return_only: true
suppresses_master_records_custody: false
erases_ecosystem_transitions: false
grants_authority: false
master_records_transition_custody_independent_of_return_projection: true
```

If `NONE` is selected, the adapter returns no transition-detail projection, receipt refs, or verification refs to the caller through this result envelope. The canonical `manifest_receipt_id` and governed result/disposition remain available as the exact-run handle/result. `NONE` MUST NOT be interpreted as evidence that no transitions occurred or that Master Records recorded nothing.

## Cross-repository implementation now available

```text
StegVerse-org/StegVerse-SDK/stegverse/governance_navigation.py
  canonical stegverse.ingress-manifest.v1 + 00 user-parameter/return-projection contract

StegVerse-Labs/StegCore/src/stegcore/manifest_receipts.py
StegVerse-Labs/StegCore/src/stegcore/manifest_receipt_provider.py
  canonical manifest_receipt_id + evidence/replay/reconstruct semantics + shared-backing provider contract

master-records/orchestration/services/manifest_receipt_custody.py
master-records/orchestration/services/manifest_receipt_custody_api.py
master-records/orchestration/services/canonical_custody_app.py
master-records/orchestration/render-custody.yaml
  exact-run immutable custody and authenticated lookup/reconstruction composed into the canonical custody deployment target
```

## Completed handoff tasks

```text
[done] TEST and LIVE_STREAM ingress modes installed
[done] per-unit stream identity/sequence/idempotency enforcement installed
[done] governed model-facing result envelope installed
[done] ALL / SELECTED / NONE caller return projection installed
[done] explicit caller-return vs Master Records custody separation installed
[done] ALLOW/DENY/REVIEW/FAIL_CLOSED preservation installed
[done] malformed/dependency/non-ALLOW-consequence fail-closed behavior installed
[done] StegCore exact-run receipt semantics available
[done] StegCore shared-backing provider contract available
[done] Master Records exact-run custody routes available on canonical deployment target
```

## Worker continuation boundary

Do not create a parallel StegGate evaluator, provider registry, custody store, receipt authority, or separate Master Records service in the adapter.

Next executable tasks:

```text
1. bind the injected governance_handler to the canonical StegCore manifested-transaction path;
2. after governance, register the canonical manifest receipt and retain the full exact evidence package through the StegCore shared-backing provider BEFORE caller return projection is applied;
3. return the same canonical manifest_receipt_id to the external caller's LLM/application;
4. apply ALL/SELECTED/NONE only to the caller-facing egress projection;
5. prove NONE hides caller transition detail while shared backing retains the full canonical transition package;
6. keep TEST and LIVE_STREAM on the same governance semantics;
7. add end-to-end tests for ALLOW, DENY, REVIEW, FAIL_CLOSED, malformed manifests, dependency failure, stream ordering, idempotent retry, shared-backing conflict, return projection, and non-ALLOW consequence rejection;
8. prove per-unit live-stream identity remains independent from stream/session identity;
9. prove retained shared backing resolves the returned manifest_receipt_id to the same immutable run;
10. run sovereign/local validation and record inspectable PASS evidence here.
```

The external LLM must never receive an ungoverned or fail-open answer presented as a governed ALLOW.

## Activation boundary

Master Records route composition is installed, but production custody activation remains gated by the Master Records repository-wide persistent-storage, backup/restore, and live-authenticated round-trip readiness requirements. The adapter must not represent installed custody code as live production custody until those conditions are evidenced.

## Validation status

Implementation and tests are installed but no sovereign/local test execution receipt was produced during this change session. Do not claim COMPLETE_RELEASED until local validation, canonical governance-handler integration, durable shared-backing proof, and owning release authority are evidenced.
