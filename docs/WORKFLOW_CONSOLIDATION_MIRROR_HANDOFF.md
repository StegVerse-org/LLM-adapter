# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, and ensure no non-TV/TVC token becomes runtime/control-plane authority
repository: StegVerse-org/LLM-adapter
branch: chore/workflow-consolidation-local-runtime-20260815
role: CLAIMED_FOR_INTEGRATION_AND_RECONCILIATION
claim_created_at: 2026-08-15T22:49:00-05:00
claim_release_condition: merge this bounded local-runtime workflow-transfer tranche after repository validation, then continue the remaining workflow census under a new nonoverlapping tranche
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

## Source of truth / policy relationship

The restoration target follows the Core-Lite stable dispatcher pattern: a bounded bootstrap/setup doorway plus a stable intake/validation dispatcher; ordinary feature expansion belongs in task registries, tools, scripts, schemas, and StegVerse workers rather than new workflow files. Historical organization-wide enforcement of `<=2` is not asserted here; this handoff records the current restoration target.

Production continuity remains:

```text
StegVerse task -> StegVerse worker -> TV/TVC authority -> StegVerse runtime -> StegVerse evidence/continuity
```

GitHub Actions may validate or mirror but may not substitute for the resident sovereign carrier, TV/TVC authority, or StegVerse runtime.

## Verified baseline and completed tranche 1

The workflow directory contained **49 workflow files** before reconciliation.

PR #145 merged at `c9f561254ec5671c2329c3deb7ce0bfb511331ab` after all ten final-head workflow groups passed. It removed four workflow files whose behavior was prohibited or superseded:

```text
.github/workflows/ecosystem-chat-github-models-execution.yml
  OBSOLETE_OR_SUPERSEDED
  reason: used GitHub token as provider credential; superseded by TV/TVC + sovereign local-model route

.github/workflows/ecosystem-chat-live-activation.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  reason: resident sovereign carrier + TV/TVC own activation continuity

.github/workflows/ecosystem-chat-live-activation-monitor.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  reason: resident carrier owns continuity/observation

.github/workflows/hil-process-restart-controlled-cycle.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  reason: HIL lifecycle/restart/private-review work is owned by TVC/TVC#8
```

That reduced the repository from 49 to **45 workflow files**.

Non-workflow artifacts retired in that tranche:

```text
render-production.yaml
scripts/write_live_activation_monitor_status.py
scripts/run_hil_process_restart_cycle.py
```

No third-party hosted service is a required production/runtime release condition.

## Bounded tranche 2 — sovereign/local-runtime workflows

This branch classifies and removes two additional standalone GitHub workflows:

```text
.github/workflows/local-runtime-model-proof.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  canonical owner: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
  retained capability: llm_adapter/local_model_runtime.py, committed local reference model, build/proof scripts, tests and receipts remain in repository history/source
  reason: formal local model plus discovery/launch/inference/proof are already COMPLETE_RELEASED under the canonical sovereign runtime owner; this GitHub-hosted write-capable proof is duplicate authority/cost surface

.github/workflows/sovereign-local-model-binding.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  canonical live owner: StegVerse-Labs/.github resident sovereign carrier + .github#60
  canonical model/runtime owner: StegVerse-002/micro-node-runtime
  retained capability: binding/provider tests and `scripts/prove_sovereign_local_model_binding.py` remain source-level validation assets
  reason: live same-carrier binding/activation is machine-owned and this hosted workflow is not allowed to substitute for it
```

After this tranche the workflow-file target state is **43**, pending merge validation. No local-model implementation is deleted; only duplicate hosted workflow entry surfaces are removed.

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
  action: preserve compatibility tests under dispatcher; retire duplicate lifecycle/hosted workflows

VACC workflow family
  action: read VACC handoffs/claims before consolidation; transfer unique checks to canonical VACC worker lane

Math Solver observer family
  canonical runtime: StegVerse portable node + canonical StegGate
  public activation: StegVerse-Labs/Site#240
  action: eliminate hosted polling/writeback after preserving machine-observable receipt semantics in the resident carrier/Site lane

publication/image/service-gateway workflows
  action: classify separately; no GitHub credential or package permission may become production runtime authority
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
workflow_files_after_current_branch_if_merged: 43
restoration_target: <=2
classified_and_remediated_so_far: 6/49
remaining_unclassified_or_unconsolidated: 43/49
current_tranche_validation: PENDING
session_consolidation_state: ACTIVE_DISTINCT_SUPPORT
```

This handoff must be updated after each consolidation tranche. The session is not archive-safe while unclassified workflow surfaces, explicit non-TV/TVC token paths, or unique untransferred behavior remain.
