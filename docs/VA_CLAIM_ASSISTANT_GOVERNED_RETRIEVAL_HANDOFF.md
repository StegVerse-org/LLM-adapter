# VA Claim Assistant Governed Retrieval — Adapter Handoff

## State

```text
program: VA Claim Assistant governed session layer
state: BUILDING
public activation: NOT AUTHORIZED
adapter issue: #90
site parent issue: StegVerse-Labs/Site#113
site source/provenance issue: StegVerse-Labs/Site#115
tvc capability issue: StegVerse-Labs/TVC#9
master-records custody issue: master-records/orchestration#12
```

## Active claim

```text
task_id: VACP-ADAPTER-DISPATCH-001
repository: StegVerse-org/LLM-adapter
branch: main
role: IMPLEMENTATION_AND_VALIDATION
claim_state: CLAIMED_FOR_VALIDATION
claim_created_at: 2026-08-02T09:10:00Z
claim_expires_at: 2026-08-03T09:10:00Z
release_condition: hosted classifier, retrieval, and dispatch workflow produces valid secret-free receipts; then TVC/custody integration becomes the next implementation owner
collision_boundary: va_claim_assistant/**, tests/test_va_claim_assistant_*.py, .github/workflows/va-claim-assistant-governed-retrieval.yml
expected_evidence: workflow run, job logs, three hash-valid receipts, TVC capability receipt, custody receipt, reconstruction receipt, deployed observation
next_task_after_release: StegVerse-Labs/TVC#9 and master-records/orchestration#12
```

## Inputs owned by Site

- `StegVerse-Labs/Site/data/va-claim-assistant/source-registry.json`
- `StegVerse-Labs/Site/data/va-claim-assistant/source-registry.schema.json`
- `StegVerse-Labs/Site/data/va-claim-assistant/answer-record.schema.json`
- `StegVerse-Labs/Site/scripts/check_va_claim_assistant_governance.py`

The adapter must consume commit-pinned copies or immutable references. It must not silently fork the authority taxonomy or answer contract.

## Required pipeline

1. Classify the question into one governed VA route.
2. Resolve the current Site source-registry version.
3. Retrieve only admitted sources.
4. Preserve source authority class, effective date, retrieval time, supersession state, and proposition locator.
5. Keep controlling authority above official operational guidance, professional support, and experiential material.
6. Separate source fact, user-record fact, inference, contradiction, uncertainty, and procedural guidance.
7. Apply refusal and referral gates.
8. Request the named TVC capability rather than loading repository-local provider credentials.
9. Produce a secret-free answer record conforming to the Site schema.
10. Submit the answer record to Master Records custody and return the custody/reconstruction references.

## Required VA routes

- claim_type
- evidence_requirement
- service_connection
- rating_criteria
- effective_date
- appeal_or_supplemental_claim
- cp_examination
- document_organization
- lay_statement
- private_record_collection
- procedural_filing
- representation_referral
- urgent_safety

## Installed implementation

```text
va_claim_assistant/route_classifier.py
  deterministic selection across all thirteen governed routes
  urgent-safety priority
  ambiguous or unsupported input -> REVIEW_REQUIRED
  stable hash-bound classification record
  all authority flags false

va_claim_assistant/governed_retrieval.py
  classifier-first governed dispatcher
  evidence_requirement -> answer generation
  classified unimplemented route -> NOT_IMPLEMENTED_FAIL_CLOSED
  ambiguous or unsupported input -> REVIEW_REQUIRED
  answer-ready state remains PENDING_TVC_AND_CUSTODY
  admitted-source enforcement
  authority-class preservation
  proposition-level citations
  stable hash-bound answer and dispatch records

tests/test_va_claim_assistant_route_classifier.py
tests/test_va_claim_assistant_governed_retrieval.py
tests/test_va_claim_assistant_governed_dispatch.py
.github/workflows/va-claim-assistant-governed-retrieval.yml
```

Commits:

```text
474da441666efbfe026a418a829c1c49c5fe0215 route classifier
552e0f565ddce667dc112e099dad86dca7a6e86a classifier tests and receipt writer
58089180c8700657e278bf4f654014bfbe283d50 initial hosted workflow integration
44410baf062a3e333e3f5c86a0797455fa7eb3d3 classifier-first fail-closed dispatch
f44abb3f2d4d2a5fee734956f7f4243988292015 dispatch tests and receipt writer
06563224cf566942512d5d64b5aa99aaa0eda15a hosted dispatch validation integration
```

## Mandatory fail-closed rules

The adapter must refuse or stop when:

- no admitted source supports a material source proposition;
- a lower authority source conflicts with controlling authority;
- a controlling source is stale, superseded, or unresolved;
- route classification is ambiguous or unsupported;
- a classified route lacks an implemented answer generator;
- a requested answer would invent a diagnosis, nexus, event, symptom, record, or rating result;
- a user asks for a guaranteed outcome or percentage targeting;
- TVC returns unavailable, unauthorized, revoked, expired, or incompatible capability status;
- custody or reconstruction cannot preserve the final receipt.

Missing repository-local credentials mean `AUTHORITY_RESOLUTION_REQUIRED`, not `BLOCKED`, until TVC resolution has been attempted.

## Dispatch states

```text
ANSWER_READY_PENDING_TVC_AND_CUSTODY
  only evidence_requirement may currently reach this state
  not deployable or publishable until TVC and Master Records gates pass

NOT_IMPLEMENTED_FAIL_CLOSED
  a valid governed route was classified but has no answer generator
  no answer is emitted

REVIEW_REQUIRED
  classification was ambiguous or unsupported
  no answer is emitted
```

None of these states grants adjudication, representation, medical-opinion, rating, execution, publication, deployment, or activation authority.

## Current validation posture

```text
file presence: VERIFIED
classifier implementation: COMMITTED
classifier deterministic fixtures: COMMITTED
governed dispatcher: COMMITTED
dispatch deterministic fixtures: COMMITTED
workflow binding for classifier/retrieval/dispatch: COMMITTED
hosted workflow result for latest implementation: NOT YET DIRECTLY OBSERVED
route-classifier persisted receipt: NOT YET DIRECTLY OBSERVED
governed-dispatch persisted receipt: NOT YET DIRECTLY OBSERVED
public deployment: NOT VERIFIED
TVC capability receipt: MISSING
Master Records custody receipt: MISSING
Master Records reconstruction receipt: MISSING
Site projection: NOT VERIFIED
```

## Minimal implementation slice

The first source-grounded adapter slice supports one public-source answer route without private documents:

- route: `evidence_requirement`
- admitted sources: official VA evidence guidance
- output: schema-oriented answer record with proposition-level citations
- authority flags: all false
- dispatch state: `ANSWER_READY_PENDING_TVC_AND_CUSTODY`

The classifier identifies all required routes, but classification does not imply that every route has an implemented answer generator. All other answer routes fail closed.

This slice may establish `SOURCE_GROUNDED_ASSISTANT` only after deployed verification. It does not establish `DOCUMENT_AWARE_ASSISTANT` or `GOVERNED_CLAIM_SESSION`.

## Exact next tasks

1. Observe the hosted `VA Claim Assistant Governed Retrieval` workflow for commit `06563224cf566942512d5d64b5aa99aaa0eda15a` or a successor receipt commit.
2. Inspect job logs and all three generated receipts; repair only exact deterministic failures.
3. Resolve `StegVerse-Labs/TVC#9` capability/readiness receipt without repository-local secrets.
4. Bind TVC result states into dispatch: authorized capability may proceed; unavailable, unauthorized, revoked, expired, or incompatible must fail closed.
5. Submit the final answer record to `master-records/orchestration#12` and require custody `RECORDED` plus reconstruction `PASS`.
6. Project only the verified capability state into `StegVerse-Labs/Site#113`.
7. Keep all non-evidence routes fail-closed until their source contracts, generators, tests, and receipts are independently installed.

## Exit evidence

Issue #90 may close only after one deployed request produces:

- deterministic route classification;
- admitted and authority-ranked citations;
- schema-valid answer record;
- no unsupported propositions;
- all authority flags false;
- TVC execution/readiness receipt;
- Master Records custody and reconstruction references;
- stable final receipt hash;
- Site projection that does not overstate the capability.

## Archive condition

A handoff is not execution transfer. This workstream may be treated as transferred only after a named executor with mutation authority accepts the next bounded claim and produces current inspectable execution evidence. Until then, incomplete adapter work remains active.
