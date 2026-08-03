# VA Claim Assistant Governed Retrieval — Adapter Handoff

## Identity

```yaml
program: VA Claim Assistant governed session layer
goal_id: VACP-ADAPTER-GOVERNED-ROUTES
originating_goal: expand Governed VA Claims Chat while preserving veteran authority, PII isolation, source precedence, custody, and fail-closed activation
repository: StegVerse-org/LLM-adapter
branch: main
canonical_issue: StegVerse-org/LLM-adapter#90
site_parent_issue: StegVerse-Labs/Site#113
site_document_issue: StegVerse-Labs/Site#116
tvc_issue: StegVerse-Labs/TVC#9
master_records_handoff: master-records/orchestration/docs/VA_PRIVACY_CUSTODY_MIRROR_HANDOFF.md
public_activation: NOT_AUTHORIZED
```

## Source of truth

The adapter consumes the Site-owned authority and answer contracts. It does not silently fork them.

```text
Site source registry:
  StegVerse-Labs/Site/data/va-claim-assistant/source-registry.json
  source commit e69e8421084b1343a9dc809fdb2a579089d37813
  current observed blob a83ff2dd8343f947265981609b154693cc5deecc

Site answer-record schema:
  StegVerse-Labs/Site/data/va-claim-assistant/answer-record.schema.json
  source commit ae64a81df7ac91a9b2df00e9b8ff1a8358fcb9ab

Pinned deterministic test projection:
  tests/fixtures/va_claim_assistant_source_registry.projection.json
```

## Claim history

```yaml
expired_claim:
  task_id: VACP-ADAPTER-DISPATCH-001
  state: EXPIRED
  expired_at: 2026-08-03T09:10:00Z
  disposition: superseded after no renewal or successor route-generator evidence

completed_claim:
  task_id: VACP-ADAPTER-ROUTES-002
  role: IMPLEMENTATION_AND_VALIDATION
  state: RELEASED_COMPLETE
  created_at: 2026-08-03T19:47:00Z
  released_at: 2026-08-03T20:06:00Z
  task_record: tasks/VACP-ADAPTER-ROUTES-002.json
```

The released claim covered route generators, dispatcher integration, deterministic tests, recurring workflow integration, and committed receipts only. It did not claim TVC execution, Master Records custody, deployment, Site activation, filing, representation, adjudication, medical opinion, or rating authority.

## Current implementation

```text
va_claim_assistant/route_classifier.py
  deterministic classification across all thirteen governed routes
  urgent-safety priority
  ambiguous or unsupported input -> REVIEW_REQUIRED
  all authority flags false

va_claim_assistant/route_generators.py
  eleven public-source route answers using admitted Site sources
  document_organization answer from sanitized derived context only
  urgent_safety generator present but fail-closed until an official admitted source exists
  stale, superseded, revoked, missing, or non-admitted required source -> AUTHORITY_RESOLUTION_REQUIRED
  raw-document and direct-identifier fields rejected
  Site answer-record additional properties rejected
  proposition-level source or user-record support required
  veteran authority and all adapter authority flags false

va_claim_assistant/governed_retrieval.py
  classifier-first dispatcher v2
  answer-ready routes -> ANSWER_READY_PENDING_TVC_AND_CUSTODY
  missing sanitized document context -> DOCUMENT_CONTEXT_REQUIRED
  missing official source -> AUTHORITY_RESOLUTION_REQUIRED
  privacy-boundary violation -> REVIEW_REQUIRED
  ambiguous or unsupported classification -> REVIEW_REQUIRED
  document answer binds source-document hashes, derived-record hash, privacy state, consent receipt hash, and session ID
```

## Route state

### Answer-ready public-source generators

```text
claim_type
 evidence_requirement
service_connection
rating_criteria
effective_date
appeal_or_supplemental_claim
cp_examination
lay_statement
private_record_collection
procedural_filing
representation_referral
```

Each route emits a schema-conforming, hash-bound answer record with source authority classes, proposition-level support, material uncertainty, false authority flags, and no Site-incompatible `contract_refs` property inside the answer.

These generators are implemented and deterministically validated. They are not deployed or activated until TVC, custody, reconstruction, and Site projection evidence passes.

### Document route

```text
route: document_organization
generator: IMPLEMENTED
without sanitized context: DOCUMENT_CONTEXT_REQUIRED
with validated sanitized derived context: ANSWER_READY_PENDING_TVC_AND_CUSTODY
public private-document upload: DISABLED
```

Required sanitized context includes:

- session-bound source-document hashes;
- page-bound record facts;
- separately labeled inferences;
- contradictions and missing evidence;
- `PII_REDACTED_VERIFIED` or `SANITIZED_DERIVED_CONTEXT` privacy state;
- valid consent receipt hash;
- derived-record hash.

The adapter rejects raw-document fields, bytes, full text, direct identifier fields, credentials, identity-proofing artifacts, SSN patterns, email addresses, and telephone-number patterns. The document context session must match the dispatch session.

### Urgent-safety route

```text
route: urgent_safety
generator: IMPLEMENTED
current state: AUTHORITY_RESOLUTION_REQUIRED
exact blocker: required_admitted_source_unavailable:VA-CRISIS-LINE
```

The adapter will not invent, hard-code, or miscite crisis instructions. `StegVerse-Labs/Site#113` must admit and validate an official current safety source, or the route remains fail-closed. This source gap does not reduce safety handling by the assistant platform; it prevents the VA claim answer record from pretending the current Site registry supports a proposition that it does not yet support.

## Installed commits

```text
6e25d727921c9c5bdabe198e43c0ffaefb9bbefd  task claim
6b7c4eca8caabec48f884cbc53e277e21da12eb9  route generators
8abdf9865251b275d35401c94aabf61105b5ec18  dispatcher v2
80468c9bf730e9cef75d046dbb2b63ba89d8afb9  pinned Site source-registry projection
7292992bbad30d5c5f1faf4c115caf539773d3ce  route-generator fixtures
5f27523d68f4ebe9208697a65c745b2f0c8761b7  expanded dispatch fixtures
06cd70ac66d3eb3cdee598a3516dea8ef1721c91  recurring validation workflow
3b7fab83bcd28f6a8fc9bf3dd286b6af843af963  machine-persisted receipts
20b3b895ed68c24d3279329ef3368d669ee28981  released task record
```

## Validation evidence

```yaml
route_generator_receipt:
  path: receipts/va-claim-assistant-route-generators-validation.json
  state: PASS
  receipt_sha256: 641c76f9e88c26d88aa0d0b600d158f9b053c05d1875ca4da1a59c160ce77919
  answer_ready_public_routes: 11
  document_route: PASS_WITH_SANITIZED_DERIVED_CONTEXT
  urgent_safety: AUTHORITY_RESOLUTION_REQUIRED
  raw_document_and_direct_identifier_rejection: true
  Site_answer_schema_additional_properties_rejected: true
  authority_granted: false
  activation_granted: false

dispatch_receipt:
  path: receipts/va-claim-assistant-governed-dispatch-validation.json
  state: PASS
  receipt_sha256: 562e5528dd44a11a9b6c3f8b965d6449c258f6942f997939f916925a61be7f02
  implemented_route_generators: 13
  answer_ready_public_routes: 11
  document_answer_ready_with_sanitized_context: true
  document_missing_context_fails_closed: true
  privacy_boundary_rejection_verified: true
  urgent_safety_authority_resolution_required: true
  authority_granted: false
  activation_granted: false
```

The repository-owned workflow persisted the receipts in commit `3b7fab83bcd28f6a8fc9bf3dd286b6af843af963`. The committed receipt contents and bot commit were directly inspected. The complete hosted run, every job log, and retained artifact were not independently inspected, so this handoff does not claim a fully inspected hosted workflow run.

## Machine-owned continuation

```text
workflow: .github/workflows/va-claim-assistant-governed-retrieval.yml
triggers: owned-path push, pull request, six-hour schedule, workflow dispatch
concurrency: newest run cancels an older duplicate for the same ref
outputs:
  receipts/va-claim-assistant-public-source-fixture.json
  receipts/va-claim-assistant-route-classifier-validation.json
  receipts/va-claim-assistant-route-generators-validation.json
  receipts/va-claim-assistant-governed-dispatch-validation.json
artifact_retention: 30 days
```

## Cross-repository continuation

### StegVerse-Labs/Site#113

- admit and validate a current official urgent-safety source or preserve `AUTHORITY_RESOLUTION_REQUIRED`;
- continue projecting only receipt-verified capability;
- keep private upload, identity linkage, filing, signature, and submission inactive;
- do not present generator implementation as deployed activation.

### StegVerse-Labs/Site#116

- emit admitted PII detector, redaction-manifest, and model-leakage receipts;
- supply only sanitized derived context matching the document contract;
- retain raw document bytes inside the privacy boundary.

### StegVerse-Labs/TVC#9

- provide route capability invocation evidence without repository-local credentials;
- enforce capability scope, expiry, revocation, and compatibility;
- credentialing or identity-linkage evidence must not reinsert PII into adapter context.

### master-records/orchestration

- accept only privacy-minimized, hash-bound answer and adapter enforcement receipts;
- return custody `RECORDED` and reconstruction `PASS`;
- reject prompts, outputs, traces, logs, direct identifiers, raw documents, credentials, and medical narratives.

## Exact incomplete tasks

1. `StegVerse-Labs/Site#113`: add an admitted official `VA-CRISIS-LINE` source or keep urgent safety fail-closed.
2. `StegVerse-Labs/TVC#9`: invoke a scoped capability for one expanded public route and retain expiry/revocation evidence.
3. `master-records/orchestration`: custody and reconstruct the expanded-route answer receipt.
4. `StegVerse-org/LLM-adapter#90`: execute one deployed expanded-route request after TVC and custody bindings are available.
5. `StegVerse-Labs/Site#113`: import the final receipt and project only the verified capability state.
6. `StegVerse-Labs/Site#116`: complete production PII detection, redaction, leakage, and substantive document execution evidence.
7. Filing remains blocked until the separately governed veteran-approved transport and custody chain is admitted.

## Validation commands

```bash
python tests/test_va_claim_assistant_route_classifier.py
python tests/test_va_claim_assistant_route_generators.py
python tests/test_va_claim_assistant_governed_retrieval.py
python tests/test_va_claim_assistant_governed_dispatch.py
```

## Authority boundary

```text
generator implementation != deployment
deterministic PASS != TVC authorization
TVC readiness != claim authority
answer record != adjudication
source guidance != legal or medical opinion
rating criteria organization != rating prediction
sanitized derived context != raw-document access
document answer != public upload activation
custody != execution
reconstruction != filing authority
draft package != signature or submission
provider output != authority
```

## Session consolidation

```text
MERGED INTO: StegVerse-org/LLM-adapter/docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md
MERGED INTO: StegVerse-org/LLM-adapter#90
MERGED INTO: StegVerse-Labs/Site#113
MERGED INTO: StegVerse-Labs/Site#116
MERGED INTO: StegVerse-Labs/TVC#9
MERGED INTO: master-records/orchestration/docs/VA_PRIVACY_CUSTODY_MIRROR_HANDOFF.md
```

## Metrics

```yaml
developed_files_percent: 100
route_generator_implementation_percent: 100
route_generator_validation_percent: 100
cross_repository_operational_integration_percent: 35
deployed_activation_percent: 15
session_consolidation_percent: 100
```

## Archive condition

The bounded route-generator implementation lane is complete and released. The broader VA Claims Chat goal remains active in repository-native cross-repository work until TVC invocation, Master Records custody/reconstruction, deployed request evidence, Site projection, production document privacy evidence, credential linkage, and veteran-approved filing transport are verified.
