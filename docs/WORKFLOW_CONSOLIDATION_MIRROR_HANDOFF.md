# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: chore/remove-render-managed-hil-20260816
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove Render/third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: tasks/LLMA-WORKFLOW-CONSOLIDATION-RENDER-HIL-029.json
role: CLAIMED_FOR_IMPLEMENTATION
credential_authority: TV/TVC
github_token_runtime_authority: NONE
render_runtime_authority: NONE
```

Production continuity remains `StegVerse task -> StegVerse worker -> TV/TVC authority -> StegVerse runtime -> StegVerse evidence/continuity`. GitHub Actions may validate or mirror only. Render and other third-party runtimes are not production continuity dependencies.

## Sovereign authority invariants

```text
resident carrier owns continuity
resident StegVerse carrier + TV/TVC
GitHub token as provider credential: prohibited
GitHub token as runtime/control-plane authority: prohibited
repository secrets for provider/Master Records production path: prohibited
TV/TVC protected values exported into GitHub Actions: prohibited
GitHub-hosted review/publication credential minting: prohibited
third-party host generated review/publication credential: prohibited
Render production/runtime dependency: prohibited
```

## Completed tranches

### Tranche 1 — StegVerse-only runtime reconciliation

PR #145 merged at `c9f561254ec5671c2329c3deb7ce0bfb511331ab` after 10/10 final-head workflow groups passed.

```text
ecosystem-chat-github-models-execution.yml -> OBSOLETE_OR_SUPERSEDED
ecosystem-chat-live-activation.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
ecosystem-chat-live-activation-monitor.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
hil-process-restart-controlled-cycle.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
render-production.yaml -> RETIRED REQUIRED HOSTED DEPENDENCY
```

### Tranche 2 — resident-carrier transfer

Commit `b5ec49b78c58c0cf9592b19b2e1b02825c96ec3f` removed five hosted workflow surfaces while retaining source/tests/receipts:

```text
local-runtime-model-proof.yml -> StegVerse-002/micro-node-runtime
sovereign-local-model-binding.yml -> micro-node-runtime + resident carrier + .github#60
observe-math-solver-public-runtime.yml -> resident carrier + LLM-adapter#132 + Site#240
heartbeat-response-node.yml -> resident sovereign heartbeat
autonomy-completion-projection.yml -> resident heartbeat + destination handoff projection
```

Validation passed Architecture Guard `31925681061`, provider usage `31925681054`, and validate `31925681058`. Claim 025 is released.

### Tranche 3 — HIL static compatibility consolidation

PR #149 merged at `0bd06fcdda1ba7fe736fde1d131b702e57080e3a` after HIL Compatibility Validation `31926015337`, Architecture Guard `31926015326`, provider usage `31926015343`, and validate `31926015314` passed.

```text
hil-deployment-profile.yml -> FOLD_INTO_STABLE_VALIDATION_DISPATCHER
hil-storage-consistency.yml -> FOLD_INTO_STABLE_VALIDATION_DISPATCHER
hil-https-receiver-probe-contract.yml -> FOLD_INTO_STABLE_VALIDATION_DISPATCHER
hil-https-receiver-probe.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
```

The retained dispatcher is token-refusing, `permissions: {}`, and uses anonymous exact-source acquisition. Claim 026 is released.

### Tranche 4 — HIL lifecycle/observer transfer

PR #150 merged at `ec16f9f681ebbac4b34e1e3af1607145153ff14c`. Final-head validation passed Architecture Guard `31927674982`, provider usage `31927675001`, and validate `31927674976`.

```text
hil-live-activation.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
observe-hil-layer.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
```

The first scheduled GitHub-hosted polling against a hardcoded Render runtime. The second exported `secrets.GITHUB_TOKEN` and mutated issue state. Claim 027 is released.

### Tranche 5 — HIL cycle validation / credential-minting retirement

PR #151 merged at `6b5db6e9415fc76da2979943ca6cb9281626ffdb`.

```text
hil-automated-full-cycle.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
hil-automated-deployment-proof.yml -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
hil-controlled-cycle.yml -> CONSOLIDATE_INTO_STABLE_DISPATCHER
hil-deployed-cycle-evidence-contract.yml -> CONSOLIDATE_INTO_STABLE_DISPATCHER
hil-full-cycle-artifact-contract.yml -> CONSOLIDATE_INTO_STABLE_DISPATCHER
```

The first two GitHub-hosted workflows minted review/publication bearer values with Python `secrets.token_urlsafe(...)`; those surfaces are retired. Deterministic controlled-cycle, artifact and deployed-evidence validation remains in the token-refusing dispatcher. Final-head validation passed HIL Compatibility `31927907026`, Architecture Guard `31927907100`, Provider Usage `31927907117`, and validate `31927907146`. Claim 028 is released.

## Current tranche 6 — eliminate remaining Render HIL managed-host surface

Exact claim: `tasks/LLMA-WORKFLOW-CONSOLIDATION-RENDER-HIL-029.json`.

Direct inspection found the remaining `.github/workflows/hil-managed-receiver-validation.yml` validates `render.yaml`, uses GitHub-hosted execution, injects non-TV/TVC review/publication token values into a container, and records GitHub Actions as its execution venue. Direct inspection of `render.yaml` found a Render-managed HIL receiver service with `generateValue: true` for `STEGVERSE_HIL_REVIEW_TOKEN` and `STEGVERSE_HIL_PUBLICATION_TOKEN`.

Disposition on this branch:

```text
.github/workflows/hil-managed-receiver-validation.yml -> ELIMINATE
  removed by efe5ec30e4c86b440f0f5531bf2b0e9aab5e8d99
  reason: validates a prohibited third-party managed runtime and injects review/publication credentials outside TV/TVC authority

render.yaml -> ELIMINATE_OBSOLETE_THIRD_PARTY_RUNTIME_MANIFEST
  removed by a1e74f1a684e29da87855a09e6ca9dd01c64c0b0
  reason: declares Render as HIL receiver runtime and delegates review/publication credential generation to that host
```

Provider-neutral source implementation, Dockerfile, HIL protocol code, deterministic tests and the token-refusing HIL compatibility dispatcher remain installed. No replacement third-party runtime or credential source is created.

If this exact tranche passes final-head validation and merges:

```text
workflow_files_baseline: 49
workflow_files_current_before_tranche: 30
workflow_files_after_tranche: 29
workflow_files_removed_or_consolidated_after_tranche: 20
classified_and_remediated_after_tranche: 21/49 = 42.86%
remaining_unclassified_or_unconsolidated: 28/49 audit-start surfaces
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
```

## Canonical ownership / convergence

```text
HIL runtime/lifecycle: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
HIL authenticated private review: StegVerse-Labs/TVC#8
Site projection: StegVerse-Labs/Site#67
Master Records: master-records/orchestration#13
sovereign local model/runtime: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
resident activation/control plane: StegVerse-Labs/.github#59/#60/#65
StegFin continuation: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

Formal local-model development and local discovery/launch/inference/proof remain `COMPLETE_RELEASED` and must not be duplicated here. HIL private-review work remains claimed by TVC #8. This workflow lane grants no HIL activation, publication, release, Master Record, provider, wallet or trade authority.

## Collision boundaries

- Do not duplicate TVC #8 authenticated private-review implementation.
- Do not create/export review, publication, provider or Master Records credentials.
- Do not infer HIL product activation from workflow or manifest retirement.
- Do not make Render or another third-party host a production dependency.
- Do not recreate released local-model/runtime work.
- Do not touch wallet/trade signing, broadcast, settlement, or StegFin provider execution.

## Next safe families after claim 029 releases

```text
remaining HIL lifecycle/evidence workflows
  inspect against canonical TVC ownership; preserve only deterministic non-authorizing validation

VACC workflow family
  read current VACC handoffs and active claims before mutation
  preserve unique VA validation while transferring runtime/provider execution to canonical VACC/TV-TVC owners

publication/image/service-gateway workflows
  classify separately; optional publication/mirror permission does not grant runtime authority

global validate.yml
  redistribute unique validation, eliminate repository-token writeback and hosted token mechanics, then retire or reduce to a token-clean validation surface
```

## Validation / release requirements for tranche 6

```text
Architecture Guard: required PASS
Validate Provider-Owned Usage Event: required PASS
validate: required PASS
PR changed-file set: exact bounded surfaces only
post-merge workflow count: direct verification required
claim 029: release to MERGED_INTO_CANONICAL_WORKSTREAM only after merge
handoff: finalize on main after merge
```

## Archive condition

This session remains a distinct support lane while workflow/token remediation remains incomplete. After this tranche, 29 workflow files would remain versus the adopted <=2 target. No archive claim is permitted until all session-specific requirements are complete, superseded, or durably transferred and no distinct validation/integration/reconciliation role remains.
