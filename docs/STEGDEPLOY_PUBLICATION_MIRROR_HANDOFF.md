# StegDeploy Publication Mirror Handoff

## Source of truth

This is the authoritative scoped continuation record for canonical StegDeploy image publication readiness in `StegVerse-org/LLM-adapter`.

Live workflow contents, retained receipts, workflow runs, artifacts, issue #18, task records, default-branch history, and the canonical StegVerse-Healer scheduler handoff are authoritative over earlier chat or handoff claims.

## Active goal and claim

```text
task_id: LLMA-PUBLICATION-ACTIVATION-013
originating_goal: complete tasks while active and activate finished Ecosystem Chat tasks
canonical_issue: StegVerse-org/LLM-adapter#18
branch: fix/activate-stegdeploy-publication-observer
claim_state: CLAIMED_FOR_IMPLEMENTATION_AND_INTEGRATION
claimed_at: 2026-08-04T19:33:00-05:00
release_condition: merge, inspect hosted validation and the main publication run, retain exact v2 evidence, assign recurring observation to Healer, and release the claim
```

Task record:

```text
tasks/LLMA-PUBLICATION-ACTIVATION-013.json
```

## Current retained truth

```text
canonical workflow: .github/workflows/stegdeploy-image.yml
retained receipt: receipts/stegdeploy-image-publication.json
retained pull log: receipts/stegdeploy-image-verification-pull.log
retained readiness: status/stegdeploy-image-publication-readiness.json
observed receipt schema: stegdeploy.image-publication.v1
observed readiness: BLOCKED
observed consumer_pull_verified: false
observed blockers:
  - current retained receipt predates v2 publication contract
  - fresh consumer pull verification not retained
provider execution authority: false
persistent deployment authority: false
custody authority: false
Site activation authority: false
manual user action required: false
```

A structurally valid v2 workflow is not itself proof that an image is published or consumable. The repository remains `BLOCKED` until the same run retains a v2 receipt, fresh pull log, and readiness projection.

## Scheduler-authority correction

The earlier handoff stated that this repository retried publication hourly, but the live workflow contained no schedule. A first attempted correction added a local cron. Canonical validation rejected that change with:

```text
scheduled workflow is not permitted outside StegVerse-Healer
```

The repository-wide policy is stronger than the earlier scoped claim:

```text
StegVerse-Labs/StegVerse-Healer is the sole approved clock for managed repositories.
```

Therefore the correct architecture is:

```text
StegVerse-Labs/StegVerse-Healer/.github/workflows/stegdeploy-publication-relay.yml
  schedule: cron "37 * * * *"
  -> app/relay_stegdeploy_publication.py
  -> bounded workflow-dispatch request to this repository

StegVerse-org/LLM-adapter/.github/workflows/stegdeploy-image.yml
  push on owned paths
  workflow_dispatch
  no schedule trigger
```

The merge of this activation package changes an owned workflow path, producing one immediate main-branch publication attempt without violating scheduler centralization. Recurrence remains machine-owned by StegVerse-Healer.

## Canonical Healer blocker

The Healer handoff and retained relay state already record the exact recurring-dispatch blocker:

```text
owner: StegVerse-Labs/StegVerse-Healer
workflow: .github/workflows/stegdeploy-publication-relay.yml
state: BLOCKED
observed result: HTTP 403
cause boundary: available HEALER_GH_TOKEN cannot create the LLM-adapter workflow-dispatch event
release condition: a controlled relay run creates the bounded dispatch without exposing the token
```

This is not converted into a user evidence-copying task. The one-shot activation in this PR proceeds through the owned-path main push while Healer retains the recurring observer and token-scope release condition.

## Canonical workflow behavior

```text
owned-path push or bounded workflow dispatch
-> authenticate to GHCR using GITHUB_TOKEN
-> build and publish linux/amd64 image
-> attest image provenance
-> remove local main tag and perform a fresh consumer pull
-> write stegdeploy.image-publication.v2 receipt
-> write exact PUBLISHED or BLOCKED state and stage outcomes
-> refresh readiness projection
-> retain receipt, pull log, and readiness together on main
-> upload evidence artifact
-> fail closed when state is not PUBLISHED
```

The workflow grants only bounded image-publication evidence activity. It grants no provider execution, persistent deployment, custody, release, Site activation, or general publication authority.

## Orchestration reconciliation

The durable orchestration state is corrected as follows:

```text
closed PR #44: no longer an active owner
current HIL full-cycle owner: PR #56
provider-layer consolidation PR #95: merged and released
publication evidence owner: issue #18
publication activation task: LLMA-PUBLICATION-ACTIVATION-013
recurring scheduler owner: StegVerse-Labs/StegVerse-Healer
exclusive live-provider task: remains queued and blocked
```

The publication evidence task is parallel-safe. Activating it does not satisfy the idle barrier for provider execution and does not bypass authorized provider, persistent endpoint, package-access, or Master Records configuration requirements.

## PR #84 disposition

PR #84 requested a one-shot handoff refresh against an older main state. Main subsequently received the v2 receipt writer, fresh pull check, readiness validator, evidence retention, and hardened workflow commits. This activation package now supplies the current-main event trigger, task ownership reconciliation, and canonical Healer delegation.

After this activation merges and validates, PR #84 is superseded and should be closed without merging its stale handoff replacement.

## Validation commands and evidence path

```text
python scripts/check_stegdeploy_image_publication_readiness.py
python scripts/check_session_provider_layer_consolidation.py
python scripts/check_llm_adapter_orchestration_state.py
python -m json.tool data/llm-adapter-orchestration-state.json
python -m json.tool data/session-provider-layer-consolidation.json
```

Hosted evidence required before claim release:

```text
pull-request workflow results
main-branch StegDeploy image workflow result
publish job and step outcomes
retained v2 receipt
same-run pull log
refreshed readiness projection
uploaded publication artifact
```

## Next executable action

1. Merge the activation branch after hosted validation passes.
2. Inspect the push-triggered `StegDeploy image` run.
3. If `PUBLISHED`, verify the retained digest and fresh pull evidence, release this task, and transfer image consumption to the existing Healer/core-node intake.
4. If `BLOCKED`, retain the exact first publication-stage blocker, repair only that blocker, and leave provider execution queued.
5. Leave recurring observation with StegVerse-Healer; do not add a local schedule.

## Collision boundaries

```text
do not add a schedule trigger outside StegVerse-Healer
do not dispatch provider execution
do not access or introduce provider or Master Records credentials
do not modify PR #56 HIL implementation paths
do not create a competing image, gateway, host, scheduler, or deployment runtime
do not claim persistent deployment, custody, Site activation, release, or sovereign completion
```

## Session consolidation

The stale task-owner correction, scheduler-authority correction, one-shot activation task, Healer delegation, token-scope blocker, release condition, and exact continuation path are durably preserved in this handoff, the orchestration state, the provider-layer inventory, task `LLMA-PUBLICATION-ACTIVATION-013`, issue #18, and `StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md`. This session remains active only until the activation is merged and the resulting publication evidence is inspected and assigned.
