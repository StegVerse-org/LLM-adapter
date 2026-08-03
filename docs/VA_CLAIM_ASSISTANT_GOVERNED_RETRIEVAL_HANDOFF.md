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
master_records_issue: master-records/orchestration#15
public_activation: NOT_AUTHORIZED
```

## Source of truth

```text
Site source registry:
  StegVerse-Labs/Site/data/va-claim-assistant/source-registry.json
  source commit e69e8421084b1343a9dc809fdb2a579089d37813
  observed blob a83ff2dd8343f947265981609b154693cc5deecc

Site answer-record schema:
  StegVerse-Labs/Site/data/va-claim-assistant/answer-record.schema.json
  source commit ae64a81df7ac91a9b2df00e9b8ff1a8358fcb9ab

TVC expanded-route admission:
  StegVerse-Labs/TVC/docs/VA_CLAIM_ASSISTANT_TVC_MIRROR_HANDOFF.md
  handoff commit 7ddcdd03866b37d61f7ac03f19ec520fe5768a00
  receipt commit fdaa860a7e3b8bd7a5caa386e6a1448f235b9bf1
  receipt hash aec5c2fa8c2c6b73e6dd9dddbafa39314a30bd0ccf19bb881349be2d3e9724f8
```

The adapter consumes these authority and capability records. It does not silently fork them.

## Claim history

```yaml
VACP-ADAPTER-DISPATCH-001:
  state: EXPIRED
  expired_at: 2026-08-03T09:10:00Z

VACP-ADAPTER-ROUTES-002:
  state: RELEASED_COMPLETE
  task_record: tasks/VACP-ADAPTER-ROUTES-002.json
  route implementation and deterministic validation: COMPLETE

VACP-ADAPTER-SERVICE-CONNECTION-EXEC-003:
  state: RELEASED_COMPLETE
  task_record: tasks/VACP-ADAPTER-SERVICE-CONNECTION-EXEC-003.json
  execution evidence schema and observer: COMPLETE
  real provider/model execution: BLOCKED
```

No active adapter implementation claim remains for the completed definition and observer lanes.

## Current route implementation

```text
va_claim_assistant/route_classifier.py
  deterministic classification across all thirteen governed routes
  urgent safety priority
  ambiguous or unsupported input -> REVIEW_REQUIRED

va_claim_assistant/route_generators.py
  eleven public-source answer generators
  document_organization from sanitized derived context only
  urgent_safety fail-closed until Site admits an official source
  raw documents and direct identifiers rejected
  proposition-level support and false authority flags required

va_claim_assistant/governed_retrieval.py
  classifier-first dispatcher v2
  answer-ready -> ANSWER_READY_PENDING_TVC_AND_CUSTODY
  missing document context -> DOCUMENT_CONTEXT_REQUIRED
  missing authority source -> AUTHORITY_RESOLUTION_REQUIRED
  privacy violation or ambiguous input -> REVIEW_REQUIRED
```

### Answer-ready public-source routes

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

### Document route

```text
route: document_organization
generator: IMPLEMENTED
without sanitized context: DOCUMENT_CONTEXT_REQUIRED
with validated sanitized context: ANSWER_READY_PENDING_TVC_AND_CUSTODY
private upload: DISABLED
```

The adapter accepts only session-bound hashes, page-bound record facts, separately labeled inferences, contradictions, missing evidence, verified privacy state, consent-receipt hash, and derived-record hash. Raw bytes, full text, credentials, identity artifacts, direct identifiers, SSNs, emails, and telephone patterns are rejected.

### Urgent-safety route

```text
route: urgent_safety
generator: IMPLEMENTED
state: AUTHORITY_RESOLUTION_REQUIRED
blocker: required_admitted_source_unavailable:VA-CRISIS-LINE
```

## Route-generator evidence

```text
route generator receipt:
  path: receipts/va-claim-assistant-route-generators-validation.json
  state: PASS
  hash: 641c76f9e88c26d88aa0d0b600d158f9b053c05d1875ca4da1a59c160ce77919
  answer-ready public routes: 11
  document route: PASS_WITH_SANITIZED_DERIVED_CONTEXT
  urgent safety: AUTHORITY_RESOLUTION_REQUIRED

dispatch receipt:
  path: receipts/va-claim-assistant-governed-dispatch-validation.json
  state: PASS
  hash: 562e5528dd44a11a9b6c3f8b965d6449c258f6942f997939f916925a61be7f02
  implemented generators: 13
  privacy refusal: PASS
  authority and activation: false

machine receipt commit: 3b7fab83bcd28f6a8fc9bf3dd286b6af843af963
```

## TVC service-connection admission

```text
route: service_connection
TVC state: ADMITTED_PENDING_PROVIDER_EXECUTION
TVC receipt hash: aec5c2fa8c2c6b73e6dd9dddbafa39314a30bd0ccf19bb881349be2d3e9724f8
adapter answer hash: bd1f6c3e751b1adf2345383f724f133c321e0e42096b4556f682837caf73ee29
adapter dispatch hash: 55419dc015db717f10914c86286b3222493753545f03fb4bd675a7dd2db4bd4e
purpose: SOURCE_GROUNDED_VA_CLAIM_GUIDANCE
scope: PUBLIC_SOURCE_SERVICE_CONNECTION_PROCEDURAL_GUIDANCE
admission lifetime: 900 seconds
revocation checked: true
commit-time validity: PASS
provider execution: false
```

## Provider-execution evidence gate

Authoritative files:

```text
contracts/va-service-connection-execution-evidence.schema.json
tests/fixtures/tvc_va_service_connection_admission.projection.json
scripts/observe_va_service_connection_execution.py
receipts/va-claim-assistant-service-connection-execution-readiness.json
tasks/VACP-ADAPTER-SERVICE-CONNECTION-EXEC-003.json
.github/workflows/va-claim-assistant-governed-retrieval.yml
```

Installed commits:

```text
b25f3dac9ac8605c27c3822be7120043e566e305  observer task claim
8380eba7b13aa72afa2d6f3ad722212c217bcd2a  pinned TVC admission
3b12d7ffdb177aab3e37cf80c6a48c862fab742a  execution evidence schema
a312a6dcc8fd9648339660eb423890ec0d15069d  fail-closed observer
ca91638f171d78ba73646759c31561a548303d83  existing-workflow integration
1b0752f630bd032870bf218eadf22c6cad585490  machine-retained readiness receipt
d2211f571e776a2f40d09b9b0557cac26c791cc9  released observer claim
```

Current receipt:

```text
path: receipts/va-claim-assistant-service-connection-execution-readiness.json
state: BLOCKED
blocker: provider_execution_evidence_missing
receipt hash: cebcf992a866ae308c0fb23533b283abc1892c37d413122701bc7cf1f102aa83
provider execution observed: false
custody: PENDING_REAL_ADAPTER_EXECUTION
reconstruction: PENDING_REAL_ADAPTER_EXECUTION
authority effect: false
activation effect: false
```

A qualifying future receipt at `receipts/va-claim-assistant-service-connection-execution.json` must prove:

- actual provider use;
- model class `retrieval_grounded_text_generation`;
- TVC-controlled credential source with no credential value present;
- exact TVC, answer, and dispatch hash binding;
- only admitted source domains;
- bounded cost no greater than USD 1.00;
- valid execution time order;
- no secrets, PII, raw documents, identity artifacts, prompts, traces, prohibited logs, or medical narrative;
- every authority and activation flag false;
- valid canonical receipt hash.

The observer emits `COMPLETE` only when all checks pass. Invalid evidence becomes `REVIEW_REQUIRED`; absent evidence remains `BLOCKED`.

## Machine-owned continuation

```text
workflow: .github/workflows/va-claim-assistant-governed-retrieval.yml
triggers: owned-path push, pull request, every six hours, workflow dispatch
concurrency: newest duplicate run cancels older run
outputs:
  receipts/va-claim-assistant-public-source-fixture.json
  receipts/va-claim-assistant-route-classifier-validation.json
  receipts/va-claim-assistant-route-generators-validation.json
  receipts/va-claim-assistant-governed-dispatch-validation.json
  receipts/va-claim-assistant-service-connection-execution-readiness.json
artifact retention: 30 days
```

The committed receipts and bot commits were inspected directly. The complete hosted run, every job log, and retained artifact were not independently inspected; no fully inspected hosted-workflow claim is made.

## Exact remaining tasks

1. `StegVerse-org/LLM-adapter#90` repository-native runtime must perform one real `service_connection` provider/model execution and write the schema-valid execution receipt.
2. The machine observer must change from `BLOCKED` to `COMPLETE`.
3. `master-records/orchestration#15` must record the execution and TVC receipts, return custody `RECORDED`, and prove reconstruction `PASS`.
4. `StegVerse-Labs/Site#113` must project only the resulting receipt-verified deployed capability.
5. `StegVerse-Labs/Site#116` must complete admitted production PII detection, redaction, model-leakage, and substantive document execution evidence.
6. TVC operational credentialing and post-credential identity linkage remain incomplete.
7. Site must admit an official current `VA-CRISIS-LINE` source or keep urgent safety fail-closed.
8. Filing remains blocked until veteran-approved transport, revocation, duplicate prevention, confirmation, and custody are admitted.

## Authority boundary

```text
generator implementation != deployment
TVC admission != provider execution
provider execution != claim authority
answer record != adjudication
source guidance != legal or medical opinion
sanitized context != raw-document access
custody != execution
reconstruction != filing authority
draft package != signature or submission
```

## Session consolidation

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
MERGED INTO: StegVerse-Labs/TVC#9
MERGED INTO: master-records/orchestration#15
MERGED INTO: StegVerse-Labs/Site#113
MERGED INTO: StegVerse-Labs/Site#116
```

## Metrics

```yaml
developed_files_percent: 100
route_generator_implementation_percent: 100
route_generator_validation_percent: 100
execution_observer_implementation_percent: 100
real_provider_execution_percent: 0
cross_repository_operational_integration_percent: 48
deployed_activation_percent: 15
session_consolidation_percent: 100
```

## Archive condition

The route-generator and execution-observer implementation lanes are complete, released, and durably transferred. The broader VA Claims Chat goal remains active until real provider execution, observer `COMPLETE`, Master Records custody/reconstruction, deployed Site projection, production document privacy evidence, operational credential linkage, and veteran-approved filing transport are verified.
