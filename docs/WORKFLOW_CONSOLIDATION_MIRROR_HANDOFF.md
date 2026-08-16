# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, and ensure no non-TV/TVC token becomes runtime/control-plane authority
repository: StegVerse-org/LLM-adapter
branch: fix/stegverse-runtime-reconcile-20260815
role: CLAIMED_FOR_INTEGRATION_AND_RECONCILIATION
claim_created_at: 2026-08-15T19:55:00-05:00
claim_release_condition: classify and transfer unique behavior, then reduce GitHub workflow entry surfaces to the adopted <=2 target without deleting unique capability evidence
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

## Source of truth / policy relationship

The restoration target follows the Core-Lite stable dispatcher pattern: a bounded bootstrap/setup doorway plus a stable intake/validation dispatcher; ordinary feature expansion belongs in task registries, tools, scripts, schemas, and StegVerse workers rather than new workflow files. Historical organization-wide enforcement of `<=2` is not asserted here; this handoff records the current restoration target.

The organization runtime handoff remains authoritative for production continuity: GitHub Actions may validate or mirror but may not substitute for the resident sovereign carrier, TV/TVC authority, or StegVerse runtime.

## Verified baseline

The `main` workflow directory was directly enumerated before this reconciliation and contained **49 workflow files**.

The current reconciliation removes four workflow files whose behavior is either prohibited or superseded:

```text
.github/workflows/ecosystem-chat-github-models-execution.yml
  reason: used GitHub token as provider credential; superseded by TV/TVC + sovereign local-model route

.github/workflows/ecosystem-chat-live-activation.yml
  reason: scheduled hosted activation, repository secrets, third-party gateway fallback; superseded by resident StegVerse carrier + TV/TVC

.github/workflows/ecosystem-chat-live-activation-monitor.yml
  reason: scheduled hosted observer of the superseded live-activation workflow; resident carrier owns continuity

.github/workflows/hil-process-restart-controlled-cycle.yml
  reason: GitHub-hosted duplicate of HIL lifecycle/restart/private-review work already owned by TVC/TVC#8
```

Therefore the branch moves from 49 to **45 workflow files**. This is containment, not completion. The restoration denominator is `45 -> <=2`, after unique behaviors are transferred.

## Non-workflow artifacts retired in the same reconciliation

```text
render-production.yaml
scripts/write_live_activation_monitor_status.py
scripts/run_hil_process_restart_cycle.py
```

No third-party hosted service is a required production/runtime release condition.

## Required classification before further deletion

Every remaining workflow must be placed into exactly one class:

- TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
- FOLD_INTO_STABLE_VALIDATION_DISPATCHER
- OPTIONAL_PUBLICATION_OR_MIRROR
- OBSOLETE_OR_SUPERSEDED
- TEMPORARY_REVIEW_REQUIRED

Unique test commands, receipt generation, release gates, and propagation behavior must be preserved in scripts/tasks/contracts before the workflow file is removed. File-count reduction alone is not completion.

## High-priority groups already identified

```text
HIL dedicated workflow family
  canonical production owner: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md + TVC#8
  expected action: preserve compatibility tests under dispatcher; retire duplicate lifecycle/hosted workflows

sovereign/local-runtime workflow family
  canonical model/runtime owner: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
  live execution owner: StegVerse-Labs/.github resident sovereign carrier + .github#60
  expected action: retain only non-authorizing validation needed by dispatcher; do not recreate execution authority

VACC workflow family
  expected action: read VACC handoffs/claims before consolidation; transfer unique checks to scripts/tasks and canonical VACC worker lane

Math Solver workflow family
  canonical runtime: StegVerse portable node + canonical StegGate
  public activation: StegVerse-Labs/Site#240
  expected action: retain deterministic tests/receipts while eliminating hosted observer duplication

publication/image/service-gateway workflows
  expected action: classify separately; no GitHub credential or package permission may become production runtime authority
```

## Credential rule

```text
non_tv_tvc_production_secret_or_token_allowed: false
GitHub token as provider credential: prohibited
GitHub token as runtime/control-plane authority: prohibited
repository secrets for provider/Master Records production path: prohibited
TV/TVC protected values exported into GitHub Actions: prohibited
```

Any remaining workflow that relies on GitHub's repository token for hosted validation mechanics is not production authority, but still remains consolidation debt under the user's stronger no-non-TV/TVC-token requirement. The target architecture minimizes/removes those hosted mechanics by moving execution to StegVerse workers and retaining at most the adopted bounded doorway/dispatcher surface.

## Validation / evidence

Current reconciliation evidence is PR #145. Final-head repository checks must be inspected before merge. Earlier functional Math Solver head passed canonical `validate`, Platform-Agnostic Runtime, capability-runtime, Architecture Guard, provider-usage validation, and the retained HIL compatibility checks.

## Cross-repository continuation

```text
StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md
StegVerse-Labs/Site#240
StegVerse-org/LLM-adapter#139
```

## Completion and archive conditions

```text
workflow_files_baseline: 49
workflow_files_after_current_reconciliation: 45
restoration_target: <=2
classified_remaining: 0/45 as a complete census
production Render dependency: removed in PR #145
GitHub Models provider-token workflow: removed in PR #145
HIL duplicate restart workflow: removed in PR #145
session_consolidation_state: ACTIVE_DISTINCT_SUPPORT
```

This handoff must be updated after each consolidation tranche. The session is not archive-safe while unclassified workflow surfaces, explicit non-TV/TVC token paths, or unique untransferred behavior remain.
