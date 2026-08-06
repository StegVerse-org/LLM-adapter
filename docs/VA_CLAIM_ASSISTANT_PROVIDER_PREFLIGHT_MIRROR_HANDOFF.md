# VA Claim Assistant Provider Preflight Mirror Handoff

This handoff is subordinate to `docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md` and `docs/LLM_ADAPTER_MIRROR_HANDOFF.md`. It does not replace either parent and does not modify the Ecosystem Chat execution lane owned by issue `#18`.

## Goal identity

```text
Parent goal ID: VACP-ADAPTER-EXECUTION-PREFLIGHT-004
Active repair ID: VACP-PREFLIGHT-HOSTED-EXECUTION-008
Originating goal: activate the finished non-executing provider preflight through a real hosted workflow without granting provider authority
Repository: StegVerse-org/LLM-adapter
Branch: fix/va-provider-preflight-private-workflow
Canonical issue: StegVerse-org/LLM-adapter#90
Parent handoff: docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md
TVC dependency: StegVerse-Labs/TVC#9
Master Records dependency: master-records/orchestration#15
Site projection owner: StegVerse-Labs/Site#113
Provider execution: NOT AUTHORIZED AND NOT EXECUTED
```

## Current claim

```text
Task: tasks/VACP-PREFLIGHT-HOSTED-EXECUTION-008.json
State: CLAIMED
Claimant: connected-repository-va-preflight-repair-lane
Role: CLAIMED_FOR_IMPLEMENTATION_AND_VALIDATION
Claim created: 2026-08-06T10:43:00-05:00
Claim expires: 2026-08-07T10:43:00-05:00
Pull request: StegVerse-org/LLM-adapter#120
Claim release condition: merge the repair, inspect created hosted jobs, retain hash-valid admission and preflight artifacts, record exact evidence here, and release the claim; otherwise retain the first exact blocker
```

The parent implementation task `VACP-ADAPTER-EXECUTION-PREFLIGHT-004` remains `RELEASED_COMPLETE` for local deterministic implementation. This repair owns only the previously unproven hosted execution path.

## Verified hosted failure

```text
Failed run: 31113730396
Event: schedule
Conclusion: failure
Jobs created: 0
Caller: public StegVerse-org/LLM-adapter
Called reusable workflow repository: private StegVerse-Labs/TVC
Called workflow: .github/workflows/va-route-ephemeral-admission.yml@d68318fc67ddb5ebf305a7fd1c6809d44dd6041e
First boundary: public callers can use only public reusable workflows
```

The failure occurred before the admission or preflight Python code ran. It was not a provider, Master Records, receipt, or authority failure.

## Selected repair

The repository already uses an exact, pinned, public-safe TVC mirror for Service Gateway proof. The same bounded pattern is now applied to the VA admission issuer:

```text
Canonical source repository: StegVerse-Labs/TVC
Canonical source commit: e3865e79662529e07d27199235431056d127ea63
Canonical source path: scripts/issue_va_ephemeral_route_admission.py
Canonical Git blob: e9bb981fbd4afea934c8b800a0f70f6b6ddaf61c
Caller mirror: vendor/tvc/e3865e79662529e07d27199235431056d127ea63/issue_va_ephemeral_route_admission.py
```

The caller workflow verifies the exact Git blob before execution. The generated admission retains the canonical TVC issuer identity and semantics. A separate hash-bound provenance sidecar records the actual execution repository, workflow, commit, run, attempt, source commit, source blob, admission receipt hash, and false authority effects.

This avoids misrepresenting a private cross-organization reusable-workflow call while preserving canonical source identity and exact receipt semantics.

## Authoritative files

```text
requests/va-claim-assistant-provider-execution-authority-request.github-models.v1.json
scripts/validate_va_provider_execution_authority.py
scripts/observe_va_provider_execution_preflight.py
scripts/check_va_provider_preflight_hosted_path.py
.github/workflows/va-claim-assistant-provider-preflight.yml
.github/workflows/validate-va-provider-preflight-hosted-path.yml
vendor/tvc/e3865e79662529e07d27199235431056d127ea63/issue_va_ephemeral_route_admission.py
receipts/va-claim-assistant-provider-execution-preflight.json
tasks/VACP-ADAPTER-EXECUTION-PREFLIGHT-004.json
tasks/VACP-PREFLIGHT-HOSTED-EXECUTION-008.json
docs/VA_CLAIM_ASSISTANT_PROVIDER_PREFLIGHT_MIRROR_HANDOFF.md
```

## Repair implementation state

Completed on branch:

```text
claim commit: e74ad65c0ea88b1eea5fde7664b315f72f262406
pinned TVC mirror commit: 3bc9424ad0f5a2e1ea7b376566ab804d869b3a28
caller workflow repair commit: d8c48379d286bde79db063822abf90ce0f443eb9
fail-closed validator commit: 3ef664de223c2a166ae4cb9dbe26ff8564562f49
focused validation workflow commit: 9a1dbbbfbc76e5a4f1d8a76c9ec76922948fd8e1
pull request: #120
```

Observed from the PR head:

```text
VA Claim Assistant Provider Preflight run: 31117757807
issue-tvc-admission job created: yes
focused validation run: 31117757866
focused validation job created: yes
hosted conclusions: PENDING RUNNER EXECUTION
artifacts inspected: not yet
```

The original zero-job startup failure is removed. Completion is not claimed until both hosted jobs finish successfully and their artifacts are inspected.

## Pinned-source validator

`scripts/check_va_provider_preflight_hosted_path.py` fails closed unless all of the following remain true:

- the vendored file has exact Git blob `e9bb981fbd4afea934c8b800a0f70f6b6ddaf61c`;
- the private cross-organization reusable-workflow call is absent;
- the exact source commit and source blob are bound in the caller workflow;
- deterministic source execution emits a 900-second, single-use, hash-valid admission;
- provider request and provider execution flags remain false;
- all admission authority and activation flags remain false;
- the execution-provenance sidecar and its SHA-256 are present;
- one-day admission and 30-day preflight artifact retention remain present;
- the repair task remains `CLAIMED`, `BLOCKED`, or `COMPLETE` and authority-neutral.

The focused workflow `.github/workflows/validate-va-provider-preflight-hosted-path.yml` runs that validator on owned pull requests and main pushes.

## Parent implementation evidence

```text
task claim: 7f41144f06daf8ab97ea0bc8dad47bb8df16980c
authority request: c2c3516e5f45eab9e24fd76b9f2730b3f610b85b
authority validator: fbeee7b4a84ad88ed5c99b3933543c285c65da02
preflight observer: c24ff859768fd0e287561bfa0c891410adc5613a
original preflight workflow: 02cb8c357cccb9e27567e905c435c048d8916ec1
local preflight receipt: 16aed3f1ed0ae3004e8643c43d518dd8bd290a23
parent task release: 1f226edcf3ca539e3e558770b38217be5947bf22
local preflight state: CONFIGURATION_REQUIRED
local result SHA-256: db9ca3a04c0794197907e1a5b81a2fb433d17c5a47607e6e548d7a54e0b3cf4d
```

## Provider-authority boundary

The committed request remains:

```text
state: REQUESTED_NOT_APPROVED
provider: github-models
permission required for a later execution lane: models: read
maximum requests: 1
maximum request cost: USD 0.10
request is authority: false
credential presence is authority: false
```

The preflight workflow itself has no provider permission and makes no provider call. A future approval receipt must be separately supplied at:

```text
receipts/va-claim-assistant-provider-execution-authority.github-models.v1.json
```

The validator requires exact provider, protocol, endpoint, host, route, purpose, scope, caller repository and commit, model, issue and expiry window, single-use request count, cost ceiling, canonical hash, and false authority fields. Missing, invalid, future, expired, mismatched, or authority-escalating receipts fail closed.

## Current expected preflight

Until protected configuration and explicit authority exist, the hosted result is expected to remain:

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

Expected blockers:

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

valid admission + configuration ready + missing or invalid explicit authority
  -> AUTHORITY_REQUIRED

valid admission + configuration ready + explicit authority valid
  -> READY_FOR_EXPLICIT_AUTHORIZED_EXECUTION
```

None of these states performs a provider call. A distinct workflow-dispatch-only, permission-bearing lane must consume both the admission and explicit authority before requesting `models: read`.

## Machine-owned continuation

```text
workflow: .github/workflows/va-claim-assistant-provider-preflight.yml
triggers: owned-path push, pull request, every six hours, workflow dispatch
admission source: exact pinned TVC mirror
admission artifact retention: 1 day
preflight artifact retention: 30 days
concurrency: newest duplicate for the same ref cancels older run
provider permission: absent
provider call: prohibited
receipt output: receipts/va-claim-assistant-provider-execution-preflight.json
```

## Exact incomplete tasks

1. PR #120 must complete hosted validation and be merged or retain its first exact blocker.
2. The repair task and this handoff must record the final run, jobs, artifacts, admission hash, provenance hash, and preflight result hash.
3. The repair claim must be released after merge and main-branch verification.
4. A protected execution environment must separately configure `STEGVERSE_MASTER_RECORDS_ENDPOINT`, `STEGVERSE_MASTER_RECORDS_ALLOWED_HOSTS`, and `STEGVERSE_MASTER_RECORDS_TOKEN`.
5. A separately authorized owner must commit a valid, unexpired VA-specific provider authority receipt for the exact adapter commit.
6. A workflow-dispatch-only execution lane may then consume fresh admission and explicit authority before requesting `models: read`.
7. One provider call must emit a privacy-minimized execution receipt matching all admitted hashes.
8. `master-records/orchestration#15` must return custody `RECORDED` and reconstruction `PASS`.
9. `StegVerse-Labs/Site#113` may project only the final verified state.
10. Production document privacy, credential linkage, veteran-approved filing transport, and Ecosystem Chat activation remain separate incomplete goals.

## Collision and authority boundaries

- do not modify or dispatch the Ecosystem Chat provider workflow owned by issue `#18`;
- do not infer authority from credentials or configuration;
- do not create an approval receipt on behalf of an authorized human or governance lane;
- do not expose tokens or configuration values;
- do not modify TVC canonical source through the caller mirror;
- preflight is not execution;
- provider output is not authority;
- custody is not execution;
- reconstruction is not filing or publication authority;
- filing, submission, representation, adjudication, rating, medical opinion, deployment, publication, and Site activation remain false.

## Integration and propagation

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
MERGED INTO: StegVerse-Labs/TVC#9
MERGED INTO: master-records/orchestration#15
MERGED INTO: StegVerse-Labs/Site#113
```

No Publisher, admissibility-wiki, or StegGuardian propagation is admissible before real provider execution, custody, reconstruction, and Site projection are verified.

## Session consolidation and archive condition

The original implementation slice remains archive-safe. This active repair claim is archive-safe only after PR #120 is merged or blocked with exact evidence, the claim is released or transferred, and the final hosted state is recorded here and in task `VACP-PREFLIGHT-HOSTED-EXECUTION-008`.

## Current repair measures

```text
task inventory: 6 deliverable groups
claim and collision control: 1/1
pinned source mirror: 1/1
caller workflow repair: 1/1
validator and focused gate: 1/1
hosted validation and artifact inspection: 0/1
merge, main verification, claim release, and handoff finalization: 0/1
developed files: 5/5
scaffolding or stubs: 0
missing implementation files: 0
validation: 2 jobs created; 0 hosted conclusions inspected
integration: PR #120 open; not merged
goal activation: 4/6 = 67 percent for this bounded repair
session consolidation: active claim durably recorded; archive condition not yet satisfied
```
