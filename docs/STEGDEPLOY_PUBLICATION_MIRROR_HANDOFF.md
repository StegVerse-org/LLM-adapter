# StegDeploy Publication Mirror Handoff

## Source of truth

This is the authoritative scoped continuation record for canonical StegDeploy image publication readiness in `StegVerse-org/LLM-adapter`.

Live workflow contents, retained receipts, workflow runs, artifacts, issue #18, task records, and default-branch history are authoritative over earlier handoff claims.

## Active goal and claim

```text
task_id: LLMA-PUBLICATION-ACTIVATION-013
originating_goal: complete tasks while active and activate finished Ecosystem Chat tasks
canonical_issue: StegVerse-org/LLM-adapter#18
branch: fix/activate-stegdeploy-publication-observer
claim_state: CLAIMED_FOR_IMPLEMENTATION_AND_INTEGRATION
claimed_at: 2026-08-04T19:33:00-05:00
release_condition: merge, inspect hosted validation and the main publication run, retain exact v2 evidence, and release the claim
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

## Activation defect and correction

The prior handoff stated that the workflow retried hourly, but the live workflow contained only `push` and `workflow_dispatch` triggers. Therefore the recurring machine observer was described but not activated.

This claim installs the missing repository-native trigger:

```yaml
schedule:
  - cron: "17 * * * *"
```

The workflow path itself is an owned-path trigger, so merging the correction causes an immediate main-branch evidence attempt and leaves the hourly observer active afterward.

## Canonical workflow behavior

```text
owned-path push, hourly schedule, or workflow dispatch
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
exclusive live-provider task: remains queued and blocked
```

The publication observer is parallel-safe. Activating it does not satisfy the idle barrier for provider execution and does not bypass authorized provider, persistent endpoint, or Master Records configuration requirements.

## PR #84 disposition

PR #84 requested a one-shot handoff refresh against an older main state. Main subsequently received the v2 receipt writer, fresh pull check, readiness validator, evidence retention, and hardened workflow commits. The remaining defect is the absent live schedule, now owned by `LLMA-PUBLICATION-ACTIVATION-013`.

After this activation merges and validates, PR #84 is superseded and should be closed without merging its stale handoff replacement.

## Validation commands and evidence path

```text
python scripts/check_stegdeploy_image_publication_readiness.py
python scripts/check_session_provider_layer_consolidation.py
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
3. If `PUBLISHED`, verify the retained digest and fresh pull evidence, release this task, and transfer continuation to the existing Healer/core-node intake.
4. If `BLOCKED`, retain the exact first stage blocker, repair only that blocker, and leave provider execution queued.
5. Keep the hourly observer active until a current v2 result is retained.

## Collision boundaries

```text
do not dispatch provider execution
do not access or introduce provider or Master Records credentials
do not modify PR #56 HIL implementation paths
do not create a competing image, gateway, host, or deployment runtime
do not claim persistent deployment, custody, Site activation, release, or sovereign completion
```

## Session consolidation

The stale task-owner correction, missing schedule defect, activation task, release condition, and exact continuation path are durably preserved in this handoff, the orchestration state, the provider-layer inventory, task `LLMA-PUBLICATION-ACTIVATION-013`, and issue #18. This session remains active only until the activation is merged and the resulting publication evidence is inspected and assigned.
