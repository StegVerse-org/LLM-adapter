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

Installation commits:

```text
74ea2f5e15dad269249ebd29a617eb847bfa8137  implementation
a5fb577a867daad54dd561b14739ab56a240faf0  tests
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
verification_refs
receipt_refs
consequence_executed
stream_id / sequence when applicable
adapter_is_governance_authority: false
provider_output_grants_consequence_authority: false
```

Malformed manifests, invalid governance states, missing manifest receipt identity, unavailable governance dependencies, stream-order violations, and unsafe non-ALLOW consequence claims fail closed.

## Cross-repository implementation now available

```text
StegVerse-org/StegVerse-SDK/stegverse/governance_navigation.py
  canonical stegverse.ingress-manifest.v1 user/developer contract

StegVerse-Labs/StegCore/src/stegcore/manifest_receipts.py
  canonical manifest_receipt_id + evidence/replay/reconstruct semantics

master-records/orchestration/services/manifest_receipt_custody.py
master-records/orchestration/services/manifest_receipt_custody_api.py
  exact-run immutable custody and authenticated lookup/reconstruction
```

## Worker continuation boundary

Do not create a parallel StegGate evaluator, provider registry, custody store, or receipt authority in the adapter.

Next executable tasks:

```text
1. bind the injected governance_handler to the canonical StegCore manifested-transaction path;
2. after governance, register/retain the exact evidence package through the canonical manifest-receipt custody provider;
3. return the same canonical manifest_receipt_id to the external caller's LLM/application;
4. keep TEST and LIVE_STREAM on the same governance semantics;
5. add end-to-end tests for ALLOW, DENY, REVIEW, FAIL_CLOSED, malformed manifests, dependency failure, stream ordering, idempotent retry, and non-ALLOW consequence rejection;
6. prove per-unit live-stream identity remains independent from stream/session identity;
7. run sovereign/local validation and record inspectable PASS evidence here.
```

The external LLM must never receive an ungoverned or fail-open answer presented as a governed ALLOW.

## Validation status

Implementation and tests are installed but no sovereign/local test execution receipt was produced during this change session. Do not claim COMPLETE_RELEASED until local validation, integration with the canonical governance handler, durable master-record backing, and owning release authority are evidenced.
