# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: main
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove Render/third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: NONE
role: ACTIVE_DISTINCT_SUPPORT
credential_authority: TV/TVC
github_token_runtime_authority: NONE
github_oidc_runtime_authority: NONE
render_runtime_authority: NONE
```

Production continuity remains `StegVerse task -> StegVerse worker -> TV/TVC authority -> StegVerse runtime -> StegVerse evidence/continuity`. GitHub Actions may validate or mirror only. Render and other third-party runtimes are not production continuity dependencies.

## Sovereign authority invariants

```text
resident carrier owns continuity
resident StegVerse carrier + TV/TVC
resident sovereign carrier
GitHub token as provider credential: prohibited
GitHub token as runtime/control-plane authority: prohibited
GitHub OIDC as runtime/control-plane authority: prohibited
repository secrets for provider/Master Records production path: prohibited
TV/TVC protected values exported into GitHub Actions: prohibited
GitHub-hosted runtime secret generation: prohibited
GitHub-hosted review/publication credential minting: prohibited
third-party host generated review/publication credential: prohibited
Render production/runtime dependency: prohibited
StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
```

## Completed tranches 1-8

```text
tranche 1: PR #145 -> c9f561254ec5671c2329c3deb7ce0bfb511331ab
tranche 2: transfer commit -> b5ec49b78c58c0cf9592b19b2e1b02825c96ec3f
tranche 3: PR #149 -> 0bd06fcdda1ba7fe736fde1d131b702e57080e3a
tranche 4: PR #150 -> ec16f9f681ebbac4b34e1e3af1607145153ff14c
tranche 5: PR #151 -> 6b5db6e9415fc76da2979943ca6cb9281626ffdb
tranche 6: PR #152 -> 91bb8578662fe2ef0e6276516efb98fce78827b0
tranche 7: PR #153 -> a314dbc3e82a0155b59067d59381995bb74b300f
tranche 8: PR #154 -> 85fe10fe40da948596662daba16f13c7f3eb531c
```

Historical continuity names retained for validation and handoff reconstruction:

```text
ecosystem-chat-github-models-execution.yml
ecosystem-chat-live-activation.yml
ecosystem-chat-live-activation-monitor.yml
hil-process-restart-controlled-cycle.yml
render-production.yaml
hil-live-activation.yml
observe-hil-layer.yml
hil-automated-full-cycle.yml
hil-automated-deployment-proof.yml
hil-controlled-cycle.yml
hil-deployed-cycle-evidence-contract.yml
hil-full-cycle-artifact-contract.yml
hil-managed-receiver-validation.yml
render.yaml
hil-rtg-notification-contract.yml
service-gateway-deploy.yml
```

All completed tranche claims 025-031 are released into the canonical workstream.

## Completed tranche 8 — service-gateway activation proof transfer

PR #154 merged at `85fe10fe40da948596662daba16f13c7f3eb531c`.

Direct inspection established that `.github/workflows/service-gateway-deploy.yml` requested GitHub OIDC `id-token: write`, created a GitHub OIDC issuer policy, labeled its TVC receipt source `github_actions_runtime`, generated `STEGVERSE_HIL_RECEIPT_KEY` on the runner with Python `secrets.token_hex(48)`, and launched the service gateway under those runner-local values. That execution path was incompatible with StegVerse-only production continuity and TV/TVC-only credential authority.

Disposition:

```text
.github/workflows/service-gateway-deploy.yml
  -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  removed by e62d4bb31a90aee7a444de2e0f52bd54ecf21bf5

.github/workflows/hil-deployment-profile.yml
  -> KEEP_STANDALONE_EXCEPTION_TEMPORARY_STABLE_DISPATCHER
  updated by 4a967ba10cca8d64b34382da3f77ad97fde2520b
```

Deterministic service-gateway validation is preserved in the token-refusing anonymous-fetch HIL compatibility dispatcher via `tests/test_service_gateway.py`. Those tests cover TVC-bound readiness, durable PDF intake, idempotent duplicate recovery, Site-format receipt integrity, and rejection of provider keys in the intake role. No service-gateway source or test was deleted, no replacement hosted runtime/OIDC authority/credential source was created, and no persistent activation was inferred.

Final-head validation on `98cb86bd5c4a1580abf1f3850c880c3a683ef9a5` passed:

```text
HIL Compatibility Validation 31932538673 SUCCESS
Architecture Guard 31932538652 SUCCESS
Validate Provider-Owned Usage Event 31932538647 SUCCESS
validate 31932538648 SUCCESS
```

Exact PR changed-file set:

```text
.github/workflows/hil-deployment-profile.yml
.github/workflows/service-gateway-deploy.yml
docs/WORKFLOW_CONSOLIDATION_MIRROR_HANDOFF.md
tasks/LLMA-WORKFLOW-CONSOLIDATION-SERVICE-GATEWAY-031.json
```

Claim `tasks/LLMA-WORKFLOW-CONSOLIDATION-SERVICE-GATEWAY-031.json` is released as `MERGED_INTO_CANONICAL_WORKSTREAM` by commit `381e8f5045ab402d239e85460ccbe43e2a13e0dc`.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current: 27
workflow_files_removed_or_consolidated: 22
classified_and_remediated: 23/49 = 46.94%
remaining_unclassified_or_unconsolidated: 26/49 audit-start surfaces
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

The 27-file count is reconciled from the verified 28-file post-tranche-7 state minus the exact one workflow-file deletion in PR #154; PR #154 added no workflow file.

## Canonical ownership / convergence

```text
organization authority handoff: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
service-gateway runtime/activation: resident sovereign carrier + StegVerse-Labs/.github#59/#65
credential authority: TV/TVC
HIL runtime/lifecycle: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
HIL authenticated private review: StegVerse-Labs/TVC#8
Site projection: StegVerse-Labs/Site#67
Master Records: master-records/orchestration#13
sovereign local model/runtime: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
StegFin continuation: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

Formal local-model development and local discovery/launch/inference/proof remain `COMPLETE_RELEASED` and must not be duplicated here. This workflow lane grants no HIL activation, publication, release, Master Record, provider, wallet or trade authority.

## Collision boundaries

- Do not duplicate resident carrier activation work or TVC credential resolution.
- Do not duplicate TVC #8 authenticated private-review implementation.
- Do not create/export review, publication, provider or Master Records credentials.
- Do not infer persistent service-gateway or HIL activation from repository validation.
- Do not make GitHub OIDC, Render, or another third-party host a production dependency.
- Do not recreate released local-model/runtime work.
- Do not touch wallet/trade signing, broadcast, settlement, or StegFin provider execution.

## Next safe families

```text
remaining HIL / service-gateway validation workflows
  inspect individually; preserve deterministic validation while transferring production execution to StegVerse/TV-TVC

VACC workflow family
  read current VACC handoffs and active claims before mutation

publication/image workflows
  classify separately; publication permission does not grant runtime authority

global validate.yml
  redistribute unique validation, eliminate repository-token writeback and hosted token mechanics, then retire or reduce to a token-clean validation surface
```

## Archive condition

This session remains a distinct support lane while workflow/token remediation remains incomplete. Twenty-seven workflow files remain versus the adopted <=2 target, 26/49 audit-start surfaces remain unclassified/unconsolidated, and `validate.yml` still carries repository-token checkout/artifact/writeback mechanics that must be redistributed or redesigned. No archive claim is permitted until all session-specific requirements are complete, superseded, or durably transferred and no distinct validation/integration/reconciliation role remains.
