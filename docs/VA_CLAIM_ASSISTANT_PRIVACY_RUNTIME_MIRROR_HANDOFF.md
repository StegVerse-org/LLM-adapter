# VA Claim Assistant Privacy Runtime Mirror Handoff

This handoff is subordinate to `docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md` and `docs/LLM_ADAPTER_MIRROR_HANDOFF.md`. It governs only `PII-RDY-06` and does not replace provider execution, Site document processing, TVC route authority, Master Records custody, filing, or Ecosystem Chat activation lanes.

## Goal identity

```text
Goal ID: VACP-ADAPTER-PII-RUNTIME-006
Originating session goal: reject raw PII before VA route classification or generation, admit only sanitized derived context, and retain privacy-minimized runtime evidence suitable for later Master Records custody
Repository: StegVerse-org/LLM-adapter
Canonical issue: StegVerse-org/LLM-adapter#90
Current sovereign provider correction: StegVerse-org/LLM-adapter#142
Current provider task: tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
Site readiness requirement: PII-RDY-06
Site document owner: StegVerse-Labs/Site#116
Master Records dependency: master-records/orchestration#15
Provider execution: NOT AUTHORIZED BY THIS PRIVACY SLICE
Public activation: NOT AUTHORIZED
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

## Claim state

```text
Original implementation claim: RELEASED_COMPLETE
Original validation claim: RELEASED_COMPLETE
Original task record: tasks/VACP-ADAPTER-PII-RUNTIME-006.json
Workflow cleanup claim: LLMA-WORKFLOW-CONSOLIDATE-VA-PRIVACY-RUNTIME-049
```

The original release covers the privacy gate, privacy-first dispatcher binding, strict receipt schema, negative fixtures, independent validation, historical hosted evidence, and durable transfer. It does not cover provider execution, operational custody, reconstruction, Site production document processing, filing, or activation.

## Authoritative implementation

```text
va_claim_assistant/privacy_runtime.py
va_claim_assistant/privacy_guarded_dispatch.py
contracts/va-claim-assistant-privacy-runtime.schema.json
tests/test_va_claim_assistant_privacy_runtime.py
scripts/validate_va_claim_assistant_privacy_runtime.py
receipts/va-claim-assistant-privacy-runtime-validation.json
tasks/VACP-ADAPTER-PII-RUNTIME-006.json
docs/VA_CLAIM_ASSISTANT_PRIVACY_RUNTIME_MIRROR_HANDOFF.md
```

## Privacy behavior

The privacy gate executes before route classification, governed generation, authority consumption, provider permission, or model input.

Accepted input contains no detected SSN, email, telephone, IP address, prohibited raw-document, prompt, model-content, trace, log, credential, identity, name, birth-date, address, or token fields. Document context is admitted only when `privacy_state` is `PII_REDACTED_VERIFIED` or `SANITIZED_DERIVED_CONTEXT`.

Rejected input becomes `REVIEW_REQUIRED` before classifier invocation, never reaches governed dispatch, retains only safe category codes/lengths, retains neither rejected values nor hashes of rejected PII, and retains no raw document, credential, prompt, model content, trace, log, or medical narrative.

## Historical hosted evidence

Historical release evidence is preserved as provenance, not a current provider-release predicate:

```text
Validation PR: #99
PR head: eb77deeac77598a81c3d80b5f07c8cc987ef0e44
Privacy workflow run: 30874416525 SUCCESS
Privacy job: 91882865431 SUCCESS
Artifact: 8879004626
Artifact digest: sha256:c6078147307ef853887a3618394c4758b6ed422b7ec815b1f22e92a554960961
Historical observation source: GITHUB_ACTIONS_WORKFLOW
Historical receipt hash: bcd39b3689ba0fbe7f18b99e114984543d784c80d3fd8ad5842cc551926df34c
```

The historical artifact verified the release at that time. It does not grant current provider, custody, filing, Site, or activation authority.

## Current deterministic validation transport

Before cleanup, `.github/workflows/va-claim-assistant-privacy-runtime.yml` ran every six hours and on owned pushes/PRs, used `contents: write`, `actions/checkout@v4`, `actions/setup-python@v5`, rewrote the receipt observation source to `GITHUB_ACTIONS_WORKFLOW`, committed/pulled/pushed receipt changes, and uploaded a 90-day artifact.

Under cleanup claim `LLMA-WORKFLOW-CONSOLIDATE-VA-PRIVACY-RUNTIME-049` that standalone hosted workflow is removed. Deterministic validation is preserved through the credential-clean canonical Goal 4 path:

```text
.github/workflows/validate.yml
  -> permissions: {}
  -> anonymous exact-SHA acquisition
  -> explicit credential refusal
  -> no schedule/writeback/artifact transport
  -> scripts/verify_goal4_full.py
scripts/verify_goal4_full.py
  -> tests/test_va_claim_assistant_privacy_runtime.py
  -> scripts/validate_va_claim_assistant_privacy_runtime.py
```

The fixture script regenerates a `LOCAL_DETERMINISTIC_VALIDATION` receipt in the workspace and exercises accepted public/document routes plus ten negative fixtures. The independent validator then verifies the strict receipt schema, source ordering, privacy-before-governed-dispatch ordering, no provider permission marker, receipt hash, and retained-source markers. GitHub-hosted validation does not write the generated receipt back to the repository or upload it as an artifact.

## Current provider continuation

The older task `tasks/VACP-ADAPTER-AUTHORIZED-EXECUTION-005.json` is superseded and is not a current privacy release consumer. Current provider continuation is:

```text
issue: StegVerse-org/LLM-adapter#142
task: tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
execution owner: resident sovereign heartbeat -> TVC -> LLM-adapter -> Master Records
credential_authority: TV/TVC
credential_requirement: NONE
github_token_required: false
github_token_runtime_authority: NONE
third_party_inference_required: false
hosted_provider_fallback: DISALLOWED
```

The sovereign executor must still invoke `va_claim_assistant/privacy_guarded_dispatch.py` before any model input. Privacy `PASS` alone does not release provider execution.

## Cross-repository continuation

```text
StegVerse-org/LLM-adapter#90/#142
  privacy gate remains required before sovereign VACC inference

master-records/orchestration#15
  genuine operational privacy-event custody and reconstruction owner
  PII-RDY-07 remains incomplete until custody RECORDED and reconstruction PASS

StegVerse-Labs/Site#113
  Site projection owner after immutable execution evidence

StegVerse-Labs/Site#116
  production document detection/redaction/model-leakage owner
  adapter PII-RDY-06 does not complete Site PII-RDY-01 through PII-RDY-03
```

## Authority boundary

```text
privacy fixture PASS != Site production detector certification
privacy validation != provider authority
privacy validation != custody
custody != execution
reconstruction != filing or publication authority
provider output != claim authority
adapter PASS != Site activation
```

No provider, credential, custody, filing, submission, representation, adjudication, rating, medical, publication, deployment, release, wallet, or Site activation authority is granted.

## Integration and consolidation

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
MERGED INTO: StegVerse-org/LLM-adapter#142
MERGED INTO: StegVerse-org/LLM-adapter/tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
MERGED INTO: master-records/orchestration#15
MERGED INTO: StegVerse-Labs/Site#113
MERGED INTO: StegVerse-Labs/Site#116
```

## Metrics

```text
privacy implementation: RELEASED_COMPLETE
negative fixtures: 10
scaffolding or stubs: 0
missing required implementation files: 0
historical hosted release evidence: PRESERVED
current deterministic validation carrier: canonical Goal 4
operational privacy custody: incomplete under named owner
```

## Archive condition

The bounded PII-RDY-06 implementation remains archive-safe. Workflow cleanup claim 049 remains incomplete until exact-head Architecture Guard/global validate pass, PR merge, post-merge workflow census, claim release, and canonical workflow handoff finalization. Broader project execution continues through the named sovereign provider, Master Records, and Site owners.
