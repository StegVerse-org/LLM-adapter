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
four_app_issue: StegVerse-Labs/Site#241
four_app_parent: StegVerse-Labs/Site#239
common_steggate_binding_issue: StegVerse-Labs/StegCore#70
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

TVC service-connection admission:
  StegVerse-Labs/TVC/docs/VA_CLAIM_ASSISTANT_TVC_MIRROR_HANDOFF.md
  receipt hash aec5c2fa8c2c6b73e6dd9dddbafa39314a30bd0ccf19bb881349be2d3e9724f8

Canonical StegGate identity:
  StegVerse-Labs/StegCore/docs/STEGGATE_RUNTIME_IDENTITY_CONTRACT.md
  StegVerse-Labs/StegCore/management/steggate-four-app-runtime-binding.json
```

The adapter consumes these authority/capability records and does not silently fork them.

## Claim history

```yaml
VACP-ADAPTER-DISPATCH-001:
  state: EXPIRED

VACP-ADAPTER-ROUTES-002:
  state: RELEASED_COMPLETE
  task_record: tasks/VACP-ADAPTER-ROUTES-002.json

VACP-ADAPTER-SERVICE-CONNECTION-EXEC-003:
  state: RELEASED_COMPLETE
  task_record: tasks/VACP-ADAPTER-SERVICE-CONNECTION-EXEC-003.json
  execution evidence observer: COMPLETE
  real provider/model execution: BLOCKED

StegCore#70 VACC common-runtime-binding lane:
  state: IMPLEMENTED_CI_VALIDATED_PUBLIC_EXECUTION_PENDING
  owner: current four-app integration workstream
```

No duplicate VACC evaluator is authorized.

## Current route implementation

`va_claim_assistant/route_classifier.py` deterministically classifies thirteen governed routes, prioritizes urgent safety, and routes ambiguous/unsupported input to `REVIEW_REQUIRED`.

`va_claim_assistant/route_generators.py` implements eleven public-source generators plus document organization from sanitized derived context; raw documents/direct identifiers are rejected. Urgent safety remains fail-closed until an admitted official source is available.

`va_claim_assistant/governed_retrieval.py` remains classifier-first and returns only bounded states such as `ANSWER_READY_PENDING_TVC_AND_CUSTODY`, `DOCUMENT_CONTEXT_REQUIRED`, `AUTHORITY_RESOLUTION_REQUIRED`, and `REVIEW_REQUIRED`.

The current bounded public/source-grounded product remains intact while the real provider-backed path is activated.

## Canonical StegGate runtime identity binding — IMPLEMENTED + HOSTED CI VALIDATED

The VACC service-connection execution evidence path now consumes the same transport-independent identity used by Ecosystem Chat and Math Solver:

```text
contract_version: stegverse.steggate.runtime-identity.v1
runtime_identity: stegverse:steggate:canonical:three-layer:v1
canonical_owner: StegVerse-Labs/StegCore
canonical_admissibility_runtime: stegcore.three_layer.evaluate_three_layer
transport_identity_authoritative: false
application_specific_policy_authority: false
```

Installed changes:

```text
scripts/observe_va_service_connection_execution.py
  commit 9212f6cda2c98eea7de072badbbc1252a0755278
  import-path repair df1d5b0d42938e7cbb696a06f321661515955cf1

contracts/va-service-connection-execution-evidence.schema.json
  commit e0c95a0b3e036a46a81be066f5695f27878a0f71

.github/workflows/va-claim-assistant-governed-retrieval.yml
  commit f617aba650128ca5635701f8dcafce434a337a16
```

The execution schema is now v1.1.0 and requires the canonical StegGate identity in every future real provider-execution receipt. The observer writes the same identity into BLOCKED/REVIEW_REQUIRED/COMPLETE readiness evidence and fails closed if the installed StegCore identity does not match.

Initial identity-binding workflow run `31339637616` failed at observer import because the standalone script did not include the repository root on `sys.path`. That failure was inspected and repaired rather than ignored.

Strongest current validation:

```text
workflow: VA Claim Assistant Governed Retrieval
run: 31339681257
job: 93311292315
conclusion: SUCCESS
artifact: 9045428133
artifact digest: sha256:5127b21f40554f9f6894c550ad54bb496d2bbbb0af374c927ebf0bc871309813
```

All deterministic route/classifier/generator/dispatch steps passed; the canonical runtime identity was validated; the observer executed successfully; receipts were persisted; and evidence was uploaded.

This proves VACC's execution-evidence lane is bound to canonical StegGate semantics in CI. It does **not** prove a real provider-backed VACC execution or public end-to-end activation.

## Current execution readiness receipt

```text
path: receipts/va-claim-assistant-service-connection-execution-readiness.json
schema_version: 1.1.0
observer: va_claim_assistant.service_connection_execution_observer.v2
state: BLOCKED
blocker: provider_execution_evidence_missing
provider_execution_observed: false
custody: PENDING_REAL_ADAPTER_EXECUTION
reconstruction: PENDING_REAL_ADAPTER_EXECUTION
receipt_hash: e787e3bc1e2f4e4eabe6bda89f1baf946410474ca35ca7494f8bf07dc1d56ae1
canonical runtime identity: VERIFIED
activation effect: false
```

A future real execution receipt at `receipts/va-claim-assistant-service-connection-execution.json` must use schema v1.1.0 and prove:

- exact canonical StegGate runtime identity;
- actual provider use;
- model class `retrieval_grounded_text_generation`;
- TVC-controlled credential source without a credential value;
- exact TVC/answer/dispatch hash binding;
- only admitted source domains;
- bounded cost no greater than USD 1.00;
- valid execution time order;
- no secrets, PII, raw documents, identity artifacts, prompts, traces, prohibited logs, or medical narrative;
- all authority/activation flags false;
- valid canonical receipt hash.

The observer returns `COMPLETE` only when all checks pass. Invalid evidence becomes `REVIEW_REQUIRED`; absent evidence remains `BLOCKED`.

## Machine-owned continuation

```text
workflow: .github/workflows/va-claim-assistant-governed-retrieval.yml
triggers: owned-path push, pull request, every six hours, workflow dispatch
receipt: receipts/va-claim-assistant-service-connection-execution-readiness.json
provider execution owner: StegVerse-org/LLM-adapter#90
custody owner after valid execution: master-records/orchestration#15
Site projection owner: StegVerse-Labs/Site#113 / #241
privacy/document owner: StegVerse-Labs/Site#116
```

Missing provider execution stays machine-visible and cannot be converted into success by CI or documentation.

## Exact remaining tasks

1. `StegVerse-org/LLM-adapter#90` must perform one real `service_connection` provider/model execution through the admitted TVC capability and canonical StegGate identity and write the schema-valid execution receipt.
2. The machine observer must transition from `BLOCKED` to `COMPLETE`.
3. `master-records/orchestration#15` must record the execution and TVC receipts, return custody `RECORDED`, and prove reconstruction `PASS`.
4. `StegVerse-Labs/Site#113/#241` must project only the resulting receipt-verified deployed capability and prove public end-to-end governed execution.
5. `StegVerse-Labs/Site#116` must complete admitted production PII detection/redaction/model-leakage and substantive document execution evidence.
6. Site must admit an official current `VA-CRISIS-LINE` source or retain urgent-safety fail-closed posture.
7. Filing remains blocked until veteran-approved transport, revocation, duplicate prevention, confirmation, and custody are admitted.

## Authority boundary

```text
generator implementation != deployment
canonical runtime identity binding != provider execution
TVC admission != provider execution
provider execution != claim authority
answer record != adjudication
sanitized context != raw-document access
custody != execution
reconstruction != filing authority
receipt verification != signature or submission
```

## Session consolidation and metrics

```yaml
developed_files_percent: 100
route_generator_implementation_percent: 100
execution_observer_implementation_percent: 100
canonical_steggate_identity_binding_percent: 100_in_ci
real_provider_execution_percent: 0
public_direct_four_app_binding_percent: 0
cross_repository_operational_integration_percent: 55
deployed_activation_percent: 15
```

Canonical continuation:

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
MERGED INTO: StegVerse-Labs/StegCore#70
MERGED INTO: master-records/orchestration#15
MERGED INTO: StegVerse-Labs/Site#113/#241
MERGED INTO: StegVerse-Labs/Site#116
PARENT: StegVerse-Labs/Site#239
```

The VACC identity-binding implementation is durable and validated. The parent four-app conversation remains active until all four public applications satisfy their direct runtime gates or this active #70 integration claim is fully transferred/released under the parent archive rule.
