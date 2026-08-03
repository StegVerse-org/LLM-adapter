# VA Claim Assistant Provider Preflight Mirror Handoff

This handoff is subordinate to `docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md` and `docs/LLM_ADAPTER_MIRROR_HANDOFF.md`. It does not replace either parent and does not modify the Ecosystem Chat execution lane owned by issue `#18`.

## Goal identity

```text
Goal ID: VACP-ADAPTER-EXECUTION-PREFLIGHT-004
Originating session goal: bind fresh TVC route admission to explicit provider authority and Master Records configuration checks before any VA provider call
Repository: StegVerse-org/LLM-adapter
Branch: main
Canonical issue: StegVerse-org/LLM-adapter#90
Parent handoff: docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md
TVC dependency: StegVerse-Labs/TVC#9
Master Records dependency: master-records/orchestration#15
Site projection owner: StegVerse-Labs/Site#113
Provider execution: NOT AUTHORIZED AND NOT EXECUTED
```

## Claim state

```text
Implementation claim: RELEASED_COMPLETE
Validation claim: RELEASED_COMPLETE_FOR_LOCAL_DETERMINISTIC_PREFLIGHT
Claim created: 2026-08-03T23:31:00Z
Claim released: 2026-08-03T23:45:00Z
Task record: tasks/VACP-ADAPTER-EXECUTION-PREFLIGHT-004.json
Active claim on these definition paths: NONE
```

Release is limited to the request contract, authority validator, TVC same-run call, preflight observer, recurring workflow, committed readiness receipt, and durable transfer. It does not release provider execution, custody, deployment, or activation.

## Authoritative files

```text
requests/va-claim-assistant-provider-execution-authority-request.github-models.v1.json
scripts/validate_va_provider_execution_authority.py
scripts/observe_va_provider_execution_preflight.py
.github/workflows/va-claim-assistant-provider-preflight.yml
receipts/va-claim-assistant-provider-execution-preflight.json
tasks/VACP-ADAPTER-EXECUTION-PREFLIGHT-004.json
docs/VA_CLAIM_ASSISTANT_PROVIDER_PREFLIGHT_MIRROR_HANDOFF.md
```

## Installed evidence

```text
task claim: 7f41144f06daf8ab97ea0bc8dad47bb8df16980c
authority request: c2c3516e5f45eab9e24fd76b9f2730b3f610b85b
authority validator: fbeee7b4a84ad88ed5c99b3933543c285c65da02
preflight observer: c24ff859768fd0e287561bfa0c891410adc5613a
preflight workflow: 02cb8c357cccb9e27567e905c435c048d8916ec1
preflight receipt: 16aed3f1ed0ae3004e8643c43d518dd8bd290a23
task release: 1f226edcf3ca539e3e558770b38217be5947bf22
preflight state: CONFIGURATION_REQUIRED
observation source: LOCAL_DETERMINISTIC_VALIDATION
result SHA-256: db9ca3a04c0794197907e1a5b81a2fb433d17c5a47607e6e548d7a54e0b3cf4d
```

No complete hosted preflight workflow run, job log, or artifact was independently inspected. A future GitHub Actions execution will write `observation_source: GITHUB_ACTIONS_WORKFLOW` and supersede the local validation level without changing the state vocabulary.

## Fresh TVC admission dependency

The workflow calls:

```text
StegVerse-Labs/TVC/.github/workflows/va-route-ephemeral-admission.yml@d68318fc67ddb5ebf305a7fd1c6809d44dd6041e
```

It binds the current adapter commit, `service_connection`, the Site source-registry commit/blob, answer-schema commit, answer receipt hash, dispatch receipt hash, purpose, and scope. The admission expires after exactly 900 seconds, is single-use, and includes a revocation reference.

The earlier committed TVC admission expired and is historical evidence only. It may not be reused.

## Provider-authority boundary

The committed request remains:

```text
state: REQUESTED_NOT_APPROVED
provider: github-models
permission required: models: read
maximum requests: 1
maximum request cost: USD 0.10
request is authority: false
credential presence is authority: false
```

A future approval receipt must be separately supplied at:

```text
receipts/va-claim-assistant-provider-execution-authority.github-models.v1.json
```

The validator requires exact provider, protocol, endpoint, host, route, purpose, scope, caller repository/commit, model, issue/expiry window, single-use request count, cost ceiling, canonical hash, and false authority fields. Missing, invalid, future, expired, mismatched, or authority-escalating receipts fail closed.

## Current exact preflight

```text
state: CONFIGURATION_REQUIRED
fresh TVC admission shape: PASS
provider permission requested by preflight: false
provider execution observed: false
custody: NOT_SUBMITTED
reconstruction: NOT_SUBMITTED
authority effect: false
activation effect: false
```

Blockers:

```text
authorized_configuration_missing:STEGVERSE_MASTER_RECORDS_ALLOWED_HOSTS
authorized_configuration_missing:STEGVERSE_MASTER_RECORDS_ENDPOINT
authorized_configuration_missing:STEGVERSE_MASTER_RECORDS_TOKEN
provider_execution_authority_missing_or_invalid
```

The observer checks only whether protected configuration values are present. It never emits their values into source, logs, receipts, or artifacts.

## State machine

```text
invalid fresh TVC admission
  -> REVIEW_REQUIRED

valid admission + missing Master Records configuration
  -> CONFIGURATION_REQUIRED

valid admission + configuration ready + missing/invalid explicit authority
  -> AUTHORITY_REQUIRED

valid admission + configuration ready + explicit authority valid
  -> READY_FOR_EXPLICIT_AUTHORIZED_EXECUTION
```

None of these states performs a provider call. A distinct workflow-dispatch-only, permission-bearing lane must consume both the admission and explicit authority before requesting `models: read`.

## Machine-owned continuation

```text
workflow: .github/workflows/va-claim-assistant-provider-preflight.yml
triggers: owned-path push, pull request, every six hours, workflow dispatch
TVC artifact retention: 1 day
preflight artifact retention: 30 days
concurrency: newest duplicate for the same ref cancels older run
provider permission: absent
provider call: prohibited
receipt output: receipts/va-claim-assistant-provider-execution-preflight.json
```

The workflow distinguishes local deterministic validation from hosted execution through `observation_source`, `workflow_run_id`, and `workflow_run_attempt`.

## Exact incomplete tasks

1. A protected execution environment must configure `STEGVERSE_MASTER_RECORDS_ENDPOINT`, `STEGVERSE_MASTER_RECORDS_ALLOWED_HOSTS`, and `STEGVERSE_MASTER_RECORDS_TOKEN`.
2. A separately authorized owner must commit a valid, unexpired VA-specific provider authority receipt for the exact adapter commit.
3. A workflow-dispatch-only execution lane must consume a fresh TVC admission and the explicit authority before requesting `models: read`.
4. That lane may execute one `service_connection` request and must persist a privacy-minimized execution receipt matching all admitted hashes.
5. The installed execution observer must change from `BLOCKED` to `COMPLETE`.
6. `master-records/orchestration#15` must return custody `RECORDED` and reconstruction `PASS`.
7. `StegVerse-Labs/Site#113` may project only the final verified state.
8. Production document privacy, credential linkage, veteran-approved filing transport, and Ecosystem Chat activation remain separate incomplete goals.

## Collision and authority boundaries

- do not modify or dispatch the Ecosystem Chat provider workflow owned by issue `#18`;
- do not infer authority from credentials or configuration;
- do not create an approval receipt on behalf of an authorized human or governance lane;
- do not expose tokens or configuration values;
- preflight is not execution;
- provider output is not authority;
- custody is not execution;
- reconstruction is not filing or publication authority;
- filing, submission, representation, adjudication, rating, medical opinion, deployment, publication, and Site activation remain false.

## Validation

```text
Static request contract: PASS
Explicit-authority validator fixtures: PASS
Fresh admission validator: PASS
Deterministic local preflight: PASS
Current preflight state: CONFIGURATION_REQUIRED
Hosted cross-repository workflow inspection: NOT OBSERVED
Provider execution: NOT EXECUTED
Custody: NOT SUBMITTED
Reconstruction: NOT SUBMITTED
```

## Integration and propagation

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
MERGED INTO: StegVerse-Labs/TVC#9
MERGED INTO: master-records/orchestration#15
MERGED INTO: StegVerse-Labs/Site#113
```

No Publisher, admissibility-wiki, or StegGuardian propagation is admissible before real provider execution, custody, reconstruction, and Site projection are verified.

## Session consolidation and archive condition

All unique information from this preflight implementation slice is preserved in code, workflow, receipts, task state, this handoff, and canonical issues. The bounded preflight slice is archive-safe. The broader governed VA Claim Session remains active in the named execution, custody, privacy, filing, and projection lanes.

## Metrics

```text
developed files: 7/7
scaffolding or stubs: 0
missing required files: 0
validation: 3/4
integration: 3/6
goal activation: 52 percent to real expanded-route execution
session consolidation: 1/1
```
