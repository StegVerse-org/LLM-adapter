# VA Claim Assistant Provider Preflight Mirror Handoff

This scoped handoff is subordinate to `docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md`, `docs/VACC_PUBLIC_INFORMATION_PROFILE_MIRROR_HANDOFF.md`, and `docs/LLM_ADAPTER_MIRROR_HANDOFF.md`. It grants no provider, custody, filing, deployment, publication, release, Site, wallet, or activation authority.

## Goal and canonical continuation

```text
historical_goal_id: VACP-ADAPTER-EXECUTION-PREFLIGHT-004
historical_task_id: VACP-PREFLIGHT-HOSTED-EXECUTION-008
historical_pull_request: StegVerse-org/LLM-adapter#120
parent_runtime_issue: StegVerse-org/LLM-adapter#90
current_correction_issue: StegVerse-org/LLM-adapter#142
canonical_current_task: tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
historical_execution_task: tasks/VACP-ADAPTER-AUTHORIZED-EXECUTION-005.json SUPERSEDED
credential_authority: TV/TVC
credential_requirement: NONE
github_token_runtime_authority: NONE
github_token_required: false
non_tv_tvc_secret_or_token_required: false
third_party_inference_required: false
hosted_provider_fallback: DISALLOWED
```

## Historical preflight result

The GitHub-Models-specific preflight was previously implemented and validated as a non-executing/fail-closed experiment. Its evidence remains immutable historical provenance only:

```text
PR #120 merge: 8fb86f92f70f23c1042d4f2eb782e1a3a6797b65
focused hosted-path run: 31135075848 SUCCESS
main preflight run: 31136792639 SUCCESS
historical release commit: acaed090dab900541d65289c8e0daa7e62b645b8
provider permission requested: false
provider execution observed: false
authority effect: false
activation effect: false
```

Those runs do not grant runtime authority and are not current VACC activation predicates.

## Supersession — current authority

The GitHub-Models activation path is no longer admissible because it depended on GitHub Actions runtime permission/credential semantics (`models: read` / ephemeral `GITHUB_TOKEN`). Current governing requirements are:

```text
credential_authority: TV/TVC
non-TV/TVC secrets or tokens: PROHIBITED
github_token_runtime_authority: NONE
github_token_required: false
third_party_inference_required: false
hosted_provider_fallback: DISALLOWED
model_output_authority: NONE
```

Canonical replacement:

```text
StegVerse-002/micro-node-runtime
-> StegVerse-Labs/.github resident sovereign heartbeat
-> StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
-> StegVerse-org/LLM-adapter
-> master-records/orchestration
-> StegVerse-Labs/Site#113 after immutable activation evidence
```

Durable correction records:

```text
issue: StegVerse-org/LLM-adapter#142
task: tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
old execution task: tasks/VACP-ADAPTER-AUTHORIZED-EXECUTION-005.json state=SUPERSEDED
old scheduled workflow: .github/workflows/va-claim-assistant-provider-preflight.yml REMOVED
workflow removal commit: ffdb7874d6b62c494d38461cca55137547d5ad02
task supersession commit: 044968419f00b7d19ae25f4fd2686b5e96e4e4dc
realignment task install commit: 38478376d814e44f4de91846423d16c3800a509e
```

Historical request/receipt files whose names contain `github-models` remain provenance only.

## Hosted-preflight validation/proof surface retirement

Cleanup claim: `tasks/LLMA-WORKFLOW-RETIRE-SUPERSEDED-VA-PREFLIGHT-047.json`.

Before this cleanup, `.github/workflows/validate-va-provider-preflight-hosted-path.yml` still used `actions/checkout@v4` and `actions/setup-python@v5` to execute `scripts/check_va_provider_preflight_hosted_path.py`. That validator was itself bound to the already-removed `.github/workflows/va-claim-assistant-provider-preflight.yml` and superseded `VACP-PREFLIGHT-HOSTED-EXECUTION-008` experiment.

Repository search found no caller/reference to that wrapper or validator. Removing them caused the separate `.github/workflows/va-provider-preflight-ubuntu2204-proof.yml` to fail closed on PR #170 at run `31986578857`, job `95262528654`, because its first substantive step tried to execute the now-removed hosted-path validator.

Direct inspection of that coupled Ubuntu proof showed it also belonged to the obsolete GitHub-hosted experiment and violated the current credential boundary:

```text
runs-on: ubuntu-22.04
actions/checkout@v4 with GitHub token
actions/setup-python@v5 with token
scripts/check_va_provider_preflight_hosted_path.py
secrets.STEGVERSE_MASTER_RECORDS_TOKEN
actions/upload-artifact@v4
historical TVC vendored admission source
historical GitHub-run-derived admission/proof manifest
```

The failed run directly logged `GITHUB_TOKEN` read permissions, token-backed checkout/setup actions, and the attempted call to the removed hosted validator. Because the current sovereign route requires `credential_requirement: NONE`, `github_token_required: false`, no third-party inference, and TV/TVC-only authority, the coupled proof workflow is also superseded rather than a current activation predicate.

Under claim 047 the complete obsolete hosted validation family is therefore retired:

```text
.github/workflows/validate-va-provider-preflight-hosted-path.yml
  -> ELIMINATE_SUPERSEDED_HOSTED_VALIDATION_WRAPPER
  -> removed
.github/workflows/va-provider-preflight-ubuntu2204-proof.yml
  -> ELIMINATE_SUPERSEDED_HOSTED_PROOF_WORKFLOW
  -> removed
scripts/check_va_provider_preflight_hosted_path.py
  -> ELIMINATE_OBSOLETE_VALIDATOR_BOUND_TO_REMOVED_GITHUB_MODELS_PREFLIGHT
  -> removed
```

The removals do not erase historical PR/run evidence above and do not remove any current sovereign activation predicate. No replacement GitHub workflow is created because the current route is machine-owned by StegVerse + TV/TVC and the historical hosted path is explicitly superseded.

## Preserved VACC safety gates

Real VACC inference still requires:

```text
privacy_guarded_dispatch PASS before model input
admitted VA/federal grounding and provenance
fresh TVC route admission
bounded response generation
Master Records custody RECORDED
same-execution reconstruction PASS
Site projection only after immutable execution evidence
```

## Current machine-owned continuation

```text
current task: VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023
execution owner: resident sovereign heartbeat -> TVC -> LLM-adapter -> Master Records
claim state: MACHINE_OWNED
manual runtime execution allowed: false
```

Machine-observable release condition:

```text
resident heartbeat advances beyond HB29 under a fresh authorized fence
canonical private local-model runtime proof exists
TVC emits ROUTE_ADMITTED with credential_requirement NONE
TVC records github_token_required=false
VACC executes against that exact admitted private endpoint
privacy guard PASS precedes model input
Master Records custody RECORDED
same-execution reconstruction PASS
Site projection consumes immutable activation evidence
```

No chat session may substitute a GitHub credential, provider token, second heartbeat, second local model, or second custody path.

## Session consolidation

```text
MERGED INTO: StegVerse-org/LLM-adapter#142
MERGED INTO: StegVerse-org/LLM-adapter/tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
MERGED INTO: StegVerse-Labs/.github#60 resident sovereign heartbeat
MERGED INTO: StegVerse-Labs/TVC/tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json
MERGED INTO: master-records/orchestration
MERGED INTO: StegVerse-Labs/Site#113
```

The historical hosted-preflight implementation is COMPLETE/SUPERSEDED as an activation route. Product activation remains machine-owned and incomplete.

## Completion measures

```text
historical preflight task completion: 8/8
historical preflight validation: 8/8
historical activation authority: 0; intentionally non-authorizing
sovereign source/control records: 4/4
source-policy validation: COMPLETE
live route validation: PENDING MACHINE OWNED
integration predicates complete: 4/8
goal activation: 4/8
```

Claim 047 is not complete until fresh exact-head Architecture Guard/global validate pass after the coupled proof retirement, its PR merges, the post-merge workflow census is observed, the claim is released, and the canonical workflow-consolidation handoff is finalized on main.
