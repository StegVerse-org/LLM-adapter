# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, and ensure no non-TV/TVC token becomes runtime/control-plane authority
repository: StegVerse-org/LLM-adapter
branch: main
credential_authority: TV/TVC
github_token_runtime_authority: NONE
session_role: ACTIVE_DISTINCT_SUPPORT
```

Production continuity remains:

```text
StegVerse task -> StegVerse worker -> TV/TVC authority -> StegVerse runtime -> StegVerse evidence/continuity
```

GitHub Actions may validate or mirror but may not substitute for the resident sovereign carrier, TV/TVC authority, or StegVerse runtime. Hosted activation/monitor ownership transfer is exact: **resident carrier owns continuity**; TV/TVC owns protected credential/route authority.

## Completed tranche 1 — StegVerse-only runtime reconciliation

Baseline audit recorded 49 workflow files. PR #145 merged at `c9f561254ec5671c2329c3deb7ce0bfb511331ab` after all ten final-head workflow groups passed. It retired four hosted workflow surfaces:

```text
ecosystem-chat-github-models-execution.yml -> OBSOLETE_OR_SUPERSEDED
ecosystem-chat-live-activation.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
ecosystem-chat-live-activation-monitor.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
hil-process-restart-controlled-cycle.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
```

It also retired `render-production.yaml`, `scripts/write_live_activation_monitor_status.py`, and `scripts/run_hil_process_restart_cycle.py`. No third-party hosted service is a required production/runtime release condition.

## Completed tranche 2 — resident-carrier transfer

Five additional hosted workflow entry surfaces are now removed from `main` at commit:

`b5ec49b78c58c0cf9592b19b2e1b02825c96ec3f`

```text
local-runtime-model-proof.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  owner: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md

sovereign-local-model-binding.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  owners: StegVerse-002/micro-node-runtime + resident sovereign carrier + .github#60

observe-math-solver-public-runtime.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  owners: resident sovereign carrier + LLM-adapter#132 + Site#240

heartbeat-response-node.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  owner: StegVerse-Labs/.github resident sovereign heartbeat

autonomy-completion-projection.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  owner: resident sovereign heartbeat + destination handoff/task projection
```

All associated implementation/proof/observer scripts, tests, receipts, and model/runtime source assets remain available; only the duplicate GitHub-hosted entry surfaces were removed.

### Why tranche 2 was applied directly to current main

The scheduled/write-capable workflows being removed repeatedly advanced `main` while their own cleanup PRs were validating. Direct evidence includes Math Solver observer commit `49e64482de2006469f6cb270bb6748ac1ce9ebff`, which only advanced the BLOCKED receipt timestamp, followed by repeated `github-actions[bot]` autonomy-projection commits. PRs #146 and #147 were superseded by current-main replacements; PR #148 received equivalent final-head validation, but `main` advanced again from the very autonomy workflow being removed.

The exact validated seven-file tranche was therefore applied atomically as a fast-forward commit on the then-current `main`, preserving the newest projection evidence while stopping the writer. No force update was used.

## Validation evidence for tranche 2

Equivalent final-head branch validation:

```text
Architecture Guard: 31925598366 SUCCESS
Validate Provider-Owned Usage Event: 31925598385 SUCCESS
validate: 31925598428 SUCCESS
```

Post-application `main` validation for exact commit `b5ec49b78c58c0cf9592b19b2e1b02825c96ec3f`:

```text
Architecture Guard: 31925681061 SUCCESS
Validate Provider-Owned Usage Event: 31925681054 SUCCESS
validate: 31925681058 SUCCESS
```

The post-application Git tree `.github/workflows` tree is `728579c395699f1497031fbe200db5245a0ddb83` and contains **40 workflow files**. The Actions API may retain historical workflow records and is not used as the file-count denominator.

Exact released claim:
`tasks/LLMA-WORKFLOW-CONSOLIDATION-RESIDENT-CARRIER-025.json`

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current: 40
workflow_files_removed_or_transferred: 9
classified_and_remediated: 9/49 = 18.37%
remaining_unclassified_or_unconsolidated: 40/49
restoration_target: <=2 unless a standalone surface has explicit evidence-backed technical necessity
current_active_tranche_claim: NONE
```

## Remaining classification rule

Every remaining workflow must be placed into exactly one class:

- TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
- FOLD_INTO_STABLE_VALIDATION_DISPATCHER
- OPTIONAL_PUBLICATION_OR_MIRROR
- OBSOLETE_OR_SUPERSEDED
- TEMPORARY_REVIEW_REQUIRED

Unique tests, receipt generation, release gates, and propagation behavior must be preserved in scripts/tasks/contracts before a workflow file is removed.

## Next safe workflow families

```text
HIL dedicated workflow family
  canonical production owner: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md + TVC#8
  next action: read current HIL claims, preserve compatibility tests, then retire/fold duplicate hosted lifecycle/probe workflows

VACC workflow family
  next action: read canonical VACC handoffs/claims before any mutation; transfer unique validation to the canonical VACC worker lane

publication/image/service-gateway workflows
  next action: classify separately; package/publication permissions do not grant production runtime authority
```

## Credential rule

```text
non_tv_tvc_production_secret_or_token_allowed: false
GitHub token as provider credential: prohibited
GitHub token as runtime/control-plane authority: prohibited
repository secrets for provider/Master Records production path: prohibited
TV/TVC protected values exported into GitHub Actions: prohibited
```

Remaining hosted validation mechanics that receive a GitHub repository token are still consolidation debt under the stronger no-non-TV/TVC-token goal even when they grant no production authority.

## Cross-repository continuation

```text
StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
StegVerse-Labs/Site#240
StegVerse-org/LLM-adapter#139
```

StegFin wallet/trade execution is not owned by this workflow-reconciliation lane; it remains with the canonical StegFin/TV-TVC/USER_ONLY continuation.

## Archive condition

This session remains a distinct support lane while the 40 remaining workflow files have not been classified/transferred/consolidated and while backend support integration work remains. The completed local-model/runtime implementation and wallet/trade continuation require no unique chat-local state from this session.
