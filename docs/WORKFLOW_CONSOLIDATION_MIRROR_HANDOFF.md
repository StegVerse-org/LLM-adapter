# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: main
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: NONE
role: ACTIVE_DISTINCT_SUPPORT
credential_authority: TV/TVC
github_token_runtime_authority: NONE
```

Production continuity remains `StegVerse task -> StegVerse worker -> TV/TVC authority -> StegVerse runtime -> StegVerse evidence/continuity`. GitHub Actions may validate or mirror only.

### Sovereign activation ownership invariants

```text
resident carrier owns continuity
resident StegVerse carrier + TV/TVC
resident sovereign carrier
GitHub token as provider credential: prohibited
GitHub token as runtime/control-plane authority: prohibited
repository secrets for provider/Master Records production path: prohibited
StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
```

These describe production ownership, not GitHub-hosted execution authority.

## Completed tranche 1 — StegVerse-only runtime reconciliation

PR #145 merged at `c9f561254ec5671c2329c3deb7ce0bfb511331ab` after 10/10 final-head workflow groups passed. Exact retired/redirected names remain part of the continuity contract:

```text
ecosystem-chat-github-models-execution.yml -> OBSOLETE_OR_SUPERSEDED
ecosystem-chat-live-activation.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
ecosystem-chat-live-activation-monitor.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
hil-process-restart-controlled-cycle.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
render-production.yaml -> RETIRED REQUIRED HOSTED DEPENDENCY
```

The resident carrier owns continuity for the retired activation monitor and persistence path; the resident StegVerse carrier + TV/TVC owns production continuation.

## Completed tranche 2 — resident-carrier transfer

Commit `b5ec49b78c58c0cf9592b19b2e1b02825c96ec3f` removed five hosted workflow surfaces while retaining source/tests/receipts:

```text
local-runtime-model-proof.yml -> StegVerse-002/micro-node-runtime
sovereign-local-model-binding.yml -> micro-node-runtime + resident carrier + .github#60
observe-math-solver-public-runtime.yml -> resident carrier + LLM-adapter#132 + Site#240
heartbeat-response-node.yml -> resident sovereign heartbeat
autonomy-completion-projection.yml -> resident heartbeat + destination handoff projection
```

Validation passed Architecture Guard `31925681061`, provider usage `31925681054`, and validate `31925681058`. Claim 025 is `MERGED_INTO_CANONICAL_WORKSTREAM`.

## Completed tranche 3 — HIL static compatibility consolidation

PR #149 merged at `0bd06fcdda1ba7fe736fde1d131b702e57080e3a` after HIL Compatibility Validation `31926015337`, Architecture Guard `31926015326`, provider usage `31926015343`, and validate `31926015314` all passed.

Disposition:

```text
hil-deployment-profile.yml -> FOLD_INTO_STABLE_VALIDATION_DISPATCHER (retained temporary token-clean compatibility dispatcher)
hil-storage-consistency.yml -> FOLD_INTO_STABLE_VALIDATION_DISPATCHER (standalone removed)
hil-https-receiver-probe-contract.yml -> FOLD_INTO_STABLE_VALIDATION_DISPATCHER (standalone removed)
hil-https-receiver-probe.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER (standalone removed; probe script retained)
```

HIL compatibility identity is v1.1 and canonical TVC ownership is explicit. Claim 026 is released.

## Completed tranche 4 — HIL lifecycle/observer transfer

PR #150 merged at `ec16f9f681ebbac4b34e1e3af1607145153ff14c` after an initial handoff-regression validation failure was repaired without restoring either hosted workflow. Final-head validation passed:

```text
Architecture Guard 31927674982 SUCCESS
Validate Provider-Owned Usage Event 31927675001 SUCCESS
validate 31927674976 SUCCESS
```

Disposition:

```text
.github/workflows/hil-live-activation.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  removed; it scheduled GitHub-hosted polling against a hardcoded third-party Render runtime

.github/workflows/observe-hil-layer.yml
  TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  removed; it scheduled GitHub-hosted coordination, exported secrets.GITHUB_TOKEN, and mutated issue #92
```

Canonical continuation is `StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md`, TVC #8, Site #67, and `master-records/orchestration#13`. `scripts/observe_hil_layer.py` remains available for StegVerse-side reuse. Claim 027 is released in `tasks/LLMA-WORKFLOW-CONSOLIDATION-HIL-LIFECYCLE-027.json`.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current: 35
workflow_files_removed_or_consolidated: 14
classified_and_remediated: 15/49 = 30.61%
remaining_unclassified_or_unconsolidated: 34/49 audit-start surfaces
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

The current 35 count is reconciled from the directly verified 37-file post-PR-149 tree minus the exact two workflow deletions in PR #150, with no workflow addition in that PR.

## Collision boundaries

- Do not duplicate TVC #8 authenticated private-review work.
- Do not create/export review, publication, provider or Master Records credentials.
- Do not infer HIL product activation from compatibility validation or workflow removal.
- Do not make a third-party host a production dependency.
- Do not recreate released local-model/runtime work.
- Do not touch wallet/trade signing, broadcast, settlement, or StegFin trade execution.

## Credential rule

```text
non_tv_tvc_production_secret_or_token_allowed: false
GitHub token as provider credential: prohibited
GitHub token as runtime/control-plane authority: prohibited
repository secrets for provider/Master Records production path: prohibited
TV/TVC protected values exported into GitHub Actions: prohibited
```

The retained HIL compatibility dispatcher refuses credential-bearing environment variables and uses anonymous source acquisition. Broader repository GitHub-hosted validation mechanics remain consolidation debt; `validate.yml` is a later dispatcher-hardening target because its hosted checkout/setup and writeback mechanics still consume repository-token capability even though that token has no production authority.

## Next safe families

```text
remaining HIL lifecycle/evidence workflows
  inspect individually against canonical TVC HIL ownership and preserve only deterministic non-authorizing validation

VACC workflow family
  read current VACC handoffs and active claims before mutation
  preserve unique VA validation while transferring runtime/provider execution to canonical VACC/TV-TVC owners

publication/image/service-gateway workflows
  classify separately; optional publication/mirror permission does not grant runtime authority

global validate.yml
  harden/remove scheduled writeback and hosted token mechanics after its unique validation set is durably redistributed
```

## Canonical continuations

```text
StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
StegVerse-Labs/TVC#8
StegVerse-Labs/Site#67
StegVerse-Labs/Site#240
StegVerse-org/LLM-adapter#139
master-records/orchestration#13
```

StegFin wallet/trade execution is not owned by this workflow-reconciliation lane; it remains with canonical StegFin/TV-TVC/USER_ONLY continuation.

## Archive condition

This session remains a distinct support lane while 35 workflow files remain versus the adopted <=2 target and backend-support surfaces remain to classify, transfer, or consolidate. Released local-model/runtime work and machine-owned StegFin continuation require no chat-local reimplementation.
