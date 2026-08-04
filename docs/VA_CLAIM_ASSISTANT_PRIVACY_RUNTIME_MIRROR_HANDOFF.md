# VA Claim Assistant Privacy Runtime Mirror Handoff

This handoff is subordinate to `docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md` and `docs/LLM_ADAPTER_MIRROR_HANDOFF.md`. It governs only `PII-RDY-06` and does not replace the provider-execution, Site document-processing, TVC credentialing, Master Records custody, or Ecosystem Chat lanes.

## Goal identity

```text
Goal ID: VACP-ADAPTER-PII-RUNTIME-006
Originating session goal: reject raw PII before VA route classification or generation, admit only sanitized derived context, and retain privacy-minimized runtime evidence suitable for later Master Records custody
Repository: StegVerse-org/LLM-adapter
Branch: main
Validation branch: validation/va-pii-runtime-006
Canonical issue: StegVerse-org/LLM-adapter#90
Site readiness requirement: PII-RDY-06
Site document owner: StegVerse-Labs/Site#116
Master Records dependency: master-records/orchestration#15
Provider execution: NOT AUTHORIZED
Public activation: NOT AUTHORIZED
```

## Authoritative files

```text
va_claim_assistant/privacy_runtime.py
va_claim_assistant/privacy_guarded_dispatch.py
contracts/va-claim-assistant-privacy-runtime.schema.json
tests/test_va_claim_assistant_privacy_runtime.py
scripts/validate_va_claim_assistant_privacy_runtime.py
.github/workflows/va-claim-assistant-privacy-runtime.yml
receipts/va-claim-assistant-privacy-runtime-validation.json
tasks/VACP-ADAPTER-PII-RUNTIME-006.json
docs/VA_CLAIM_ASSISTANT_PRIVACY_RUNTIME_MIRROR_HANDOFF.md
```

## Claim state

```text
Implementation claim: CLAIMED_FOR_IMPLEMENTATION
Validation claim: CLAIMED_FOR_VALIDATION
Claim created: 2026-08-04T03:07:00Z
Claim expires: 2026-08-05T03:07:00Z
Task record: tasks/VACP-ADAPTER-PII-RUNTIME-006.json
Release condition: production gate, wrapper, schema, negative fixtures, validator, recurring workflow, PASS receipt, hosted PR run inspection, artifact inspection, provider-executor dependency binding, issue transfer, and final task release
```

## Installed implementation

```text
task claim: 0574695ec089a3d708a2817b6ed5d8f9f8ee21ad
privacy runtime: e14e70be89f24d418d28a2a44c091d3349414ebc
privacy-guarded dispatcher: e007689277cc2f3961bbcd9361b7b2373e1340ce
receipt schema: c5352d8f3da069e392e2cf52cb88cd84dda3dd15
negative fixtures: ea1c8829e3acff4102c739adbd18ba398467f445
independent validator: cc1b13031f4837460112f5c97224a1c15e2e29c7
recurring workflow: 1065e58e5fc30b1e5831be329a8f20f6df55bad3
```

## Runtime behavior

The privacy gate executes before route classification and answer generation.

Accepted input:

- has no detected SSN, email, telephone, IP-address, prohibited raw-document, prompt, model-content, trace, log, credential, identity, name, birth-date, address, or token fields;
- may include document context only when `privacy_state` is `PII_REDACTED_VERIFIED` or `SANITIZED_DERIVED_CONTEXT`;
- receives a hash-bound privacy event;
- may continue to the existing governed dispatcher;
- retains no raw question outside the existing governed answer record.

Rejected input:

- becomes `REVIEW_REQUIRED` before classifier invocation;
- never reaches the governed dispatcher;
- retains only safe category codes and lengths;
- retains no rejected value and no hash of rejected PII;
- retains no raw document, credential, prompt, model input/output, trace, log, or medical narrative.

## Negative fixtures

```text
SSN
email address
telephone number
IP address
raw_document field
prompt field
credentials field
identity_proofing_artifact field
veteran_name field
email field inside document context
```

Each fixture requires `governed_dispatch = null`, `state = REVIEW_REQUIRED`, no rejected value in serialized output, and no rejected input hash.

## Validation state

```text
Source syntax and isolated privacy-event validation: PASS
Production wrapper installation: COMPLETE
Negative fixture suite: INSTALLED
Independent receipt validator: INSTALLED
Recurring hosted workflow: INSTALLED
Push-run receipt: NOT OBSERVED
PR validation run: PENDING
Job logs: PENDING
Artifact inspection: PENDING
Provider execution: NOT EXECUTED
Custody: NOT SUBMITTED
Reconstruction: NOT SUBMITTED
Authority effect: false
Activation effect: false
```

No hosted workflow success is claimed until the pull-request run, job steps, decoded logs, and artifact are inspected directly.

## Machine-owned continuation

```text
workflow: .github/workflows/va-claim-assistant-privacy-runtime.yml
triggers: owned-path push, pull request, every six hours, workflow dispatch
output: receipts/va-claim-assistant-privacy-runtime-validation.json
artifact retention: 90 days
concurrency: newest duplicate run for the same ref cancels older run
provider permission: absent
provider call: prohibited
```

## Cross-repository obligations

```text
StegVerse-org/LLM-adapter#90
  owns runtime privacy implementation and execution binding

master-records/orchestration#15
  may ingest only the privacy-minimized event after operational execution
  must return custody RECORDED and reconstruction PASS for PII-RDY-07

StegVerse-Labs/Site#113
  may import the adapter PASS receipt for PII-RDY-06 projection

StegVerse-Labs/Site#116
  remains owner of production document detection, redaction, and leakage evidence
  adapter PASS does not complete PII-RDY-01, PII-RDY-02, or PII-RDY-03
```

## Collision and authority boundaries

- do not modify or dispatch `VACP-ADAPTER-AUTHORIZED-EXECUTION-005` except to add this privacy runtime as a release dependency;
- do not modify Site document processors, TVC credentialing, or Master Records implementation;
- regex fixture coverage is not Site production-detector certification;
- privacy validation is not custody or reconstruction;
- privacy validation is not provider, filing, submission, representation, adjudication, rating, medical, publication, deployment, or activation authority.

## Exact incomplete tasks

1. Inspect the PR-triggered privacy workflow run, all job steps, decoded logs, and artifact.
2. Persist the hosted `GITHUB_ACTIONS_WORKFLOW` receipt on `main` or preserve the exact failed blocker.
3. Bind `VACP-ADAPTER-AUTHORIZED-EXECUTION-005` to call `privacy_guarded_dispatch` before provider permission or model input.
4. Release task `VACP-ADAPTER-PII-RUNTIME-006` only after the evidence above is complete.
5. Transfer the final receipt to adapter issue `#90`, Master Records issue `#15`, and Site issues `#113` and `#116`.
6. Keep PII-RDY-07 blocked until a genuine operational event is custodied and reconstructed.

## Session consolidation

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
MERGED INTO: master-records/orchestration#15
MERGED INTO: StegVerse-Labs/Site#113
MERGED INTO: StegVerse-Labs/Site#116
```

All unique design requirements for this privacy-runtime slice are now durable. The implementation claim remains active only for hosted validation, execution-task binding, final receipt retention, issue transfer, and claim release.

## Metrics

```text
developed files: 8/9
scaffolding or stubs: 0
missing required files: 1 hosted receipt
validation: 3/7
integration: 2/5
goal activation: 55 percent to PII-RDY-06 completion
session consolidation: 1/1
```

## Archive condition

This privacy-runtime slice becomes archive-safe when the hosted PR workflow, job logs, and artifact pass; the receipt is committed; the blocked provider executor depends on the privacy gate; the task claim is released; and all continuation owners receive the exact evidence. Broader VA Claim Session archival still requires the remaining provider, custody, Site privacy, identity-linkage, filing, and activation lanes.
