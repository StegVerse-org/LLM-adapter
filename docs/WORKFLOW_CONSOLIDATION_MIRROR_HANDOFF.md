# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, and ensure no non-TV/TVC token becomes runtime/control-plane authority
repository: StegVerse-org/LLM-adapter
branch: chore/workflow-consolidation-resident-carriers-20260815
active_claim: tasks/LLMA-WORKFLOW-CONSOLIDATION-RESIDENT-CARRIER-025.json
role: CLAIMED_FOR_INTEGRATION_AND_RECONCILIATION
claim_created_at: 2026-08-15T22:49:00-05:00
claim_release_condition: merge the bounded resident-carrier transfer tranche after final-head repository validation; then release the claim and start a fresh nonoverlapping census tranche
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

## Source of truth / policy relationship

The restoration target follows the Core-Lite stable dispatcher pattern: a bounded bootstrap/setup doorway plus a stable intake/validation dispatcher; ordinary feature expansion belongs in task registries, tools, scripts, schemas, and StegVerse workers rather than new workflow files. Historical organization-wide enforcement of `<=2` is not asserted here; this handoff records the current restoration target.

Production continuity remains:

```text
StegVerse task -> StegVerse worker -> TV/TVC authority -> StegVerse runtime -> StegVerse evidence/continuity
```

Hosted activation/monitor ownership transfer is exact: **resident carrier owns continuity**; TV/TVC owns protected credential/route authority.

GitHub Actions may validate or mirror but may not substitute for the resident sovereign carrier, TV/TVC authority, or StegVerse runtime.

## Completed tranche 1 — PR #145

The workflow directory contained **49 workflow files** before reconciliation. PR #145 merged at `c9f561254ec5671c2329c3deb7ce0bfb511331ab` after all ten final-head workflow groups passed and removed four workflow files:

```text
.github/workflows/ecosystem-chat-github-models-execution.yml
  OBSOLETE_OR_SUPERSEDED
  reason: used GitHub token as provider credential; superseded by TV/TVC + sovereign local-model route

.github/workflows/ecosystem-chat-live-activation.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  owner: resident StegVerse carrier + TV/TVC

.github/workflows/ecosystem-chat-live-activation-monitor.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  owner: resident carrier owns continuity

.github/workflows/hil-process-restart-controlled-cycle.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  owner: StegVerse-Labs/TVC + TVC#8
```

That reduced the repository from 49 to **45 workflow files**.

Non-workflow artifacts retired in tranche 1:

```text
render-production.yaml
scripts/write_live_activation_monitor_status.py
scripts/run_hil_process_restart_cycle.py
```

No third-party hosted service is a required production/runtime release condition.

## Current tranche 2 — resident-carrier transfer

This branch removes five additional GitHub-hosted workflow entry surfaces while retaining their scripts/tests/receipts and assigning their execution semantics to existing StegVerse owners:

```text
.github/workflows/local-runtime-model-proof.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  canonical owner: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
  retained assets: local_model_runtime.py, build/proof scripts, local reference model, tests, receipts
  reason: formal local model and discovery/launch/inference/proof are already COMPLETE_RELEASED; hosted write-capable proof is duplicate cost/authority surface

.github/workflows/sovereign-local-model-binding.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  canonical owners: StegVerse-002/micro-node-runtime + StegVerse-Labs/.github resident sovereign carrier + .github#60
  retained assets: sovereign binding code/tests/proof script
  reason: live same-carrier activation is machine-owned and hosted CI cannot substitute

.github/workflows/observe-math-solver-public-runtime.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  canonical owners: resident sovereign carrier + LLM-adapter#132 + Site#240
  retained assets: scripts/observe_math_solver_public_runtime.py + receipts/math-solver-public-runtime.latest.json
  reason: hourly GitHub polling/writeback was observed directly committing only BLOCKED timestamps while the eligible StegVerse carrier was absent; it is not the runtime owner

.github/workflows/heartbeat-response-node.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  canonical owner: StegVerse-Labs/.github resident sovereign heartbeat
  retained assets: scripts/process_heartbeat_response.py + heartbeat receipt schema/data
  reason: an hourly GitHub-hosted heartbeat is not the sovereign resident heartbeat and cannot own persistence/authority

.github/workflows/autonomy-completion-projection.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  canonical owner: resident sovereign heartbeat + destination handoff/task projection
  retained assets: scripts/project_autonomy_completion_evidence.py + data/autonomy/completion-evidence.json
  reason: scheduled/workflow-run GitHub writeback caused autonomous main-branch churn and is not completion authority
```

The exact claim is `tasks/LLMA-WORKFLOW-CONSOLIDATION-RESIDENT-CARRIER-025.json`.

If this tranche merges, the workflow-file count becomes **40**. No application/runtime capability is deleted; only duplicate hosted workflow entry surfaces are removed.

## Direct observed cost/churn evidence

`Observe Math Solver Public Runtime` schedule run `31924396268` executed on GitHub-hosted Actions and produced main commit `49e64482de2006469f6cb270bb6748ac1ce9ebff`, changing only `observed_at` in `receipts/math-solver-public-runtime.latest.json` while the receipt remained `BLOCKED`.

The main branch subsequently advanced again via a GitHub Actions bot commit for autonomy-completion projection. These are concrete examples of hosted polling/writeback creating cost and branch drift without establishing sovereign activation.

## Required classification before further deletion

Every remaining workflow must be placed into exactly one class:

- TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
- FOLD_INTO_STABLE_VALIDATION_DISPATCHER
- OPTIONAL_PUBLICATION_OR_MIRROR
- OBSOLETE_OR_SUPERSEDED
- TEMPORARY_REVIEW_REQUIRED

Unique test commands, receipt generation, release gates, and propagation behavior must be preserved in scripts/tasks/contracts before the workflow file is removed. File-count reduction alone is not completion.

## High-priority remaining groups

```text
HIL dedicated workflow family
  canonical production owner: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md + TVC#8
  next action: preserve compatibility tests under dispatcher; retire duplicate lifecycle/hosted workflows

VACC workflow family
  next action: read VACC handoffs/claims before consolidation; transfer unique checks to canonical VACC worker lane

publication/image/service-gateway workflows
  next action: classify separately; no GitHub credential or package permission may become production runtime authority
```

## Credential rule

```text
non_tv_tvc_production_secret_or_token_allowed: false
GitHub token as provider credential: prohibited
GitHub token as runtime/control-plane authority: prohibited
repository secrets for provider/Master Records production path: prohibited
TV/TVC protected values exported into GitHub Actions: prohibited
```

Any remaining workflow that relies on GitHub's repository token for hosted validation mechanics is not production authority, but remains consolidation debt under the stronger no-non-TV/TVC-token requirement.

## Cross-repository continuation

```text
StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
StegVerse-Labs/Site#240
StegVerse-org/LLM-adapter#139
```

StegFin wallet/trade execution is not owned by this workflow-reconciliation lane; it remains with its canonical StegFin/TV-TVC/USER_ONLY continuation.

## Completion and archive conditions

```text
workflow_files_baseline: 49
workflow_files_after_pr145: 45
workflow_files_after_current_tranche_if_merged: 40
restoration_target: <=2
classified_and_remediated_so_far_if_merged: 9/49
remaining_unclassified_or_unconsolidated_if_merged: 40/49
current_tranche_validation: RETRY_AFTER_CONTRACT_WORDING_ALIGNMENT
session_consolidation_state: ACTIVE_DISTINCT_SUPPORT
```

This handoff must be updated after each consolidation tranche. The session is not archive-safe while unclassified workflow surfaces, explicit non-TV/TVC token paths, or unique untransferred behavior remain.
