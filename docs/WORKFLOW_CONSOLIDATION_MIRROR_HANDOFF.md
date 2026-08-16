# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: chore/transfer-service-gateway-proof-20260816
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove Render/third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: tasks/LLMA-WORKFLOW-CONSOLIDATION-SERVICE-GATEWAY-031.json
role: CLAIMED_FOR_IMPLEMENTATION
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

## Completed tranches 1-7

```text
tranche 1: PR #145 -> c9f561254ec5671c2329c3deb7ce0bfb511331ab
tranche 2: transfer commit -> b5ec49b78c58c0cf9592b19b2e1b02825c96ec3f
tranche 3: PR #149 -> 0bd06fcdda1ba7fe736fde1d131b702e57080e3a
tranche 4: PR #150 -> ec16f9f681ebbac4b34e1e3af1607145153ff14c
tranche 5: PR #151 -> 6b5db6e9415fc76da2979943ca6cb9281626ffdb
tranche 6: PR #152 -> 91bb8578662fe2ef0e6276516efb98fce78827b0
tranche 7: PR #153 -> a314dbc3e82a0155b59067d59381995bb74b300f
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
```

All completed tranche claims 025-030 are released into the canonical workstream. Tranche 7 final-head validation passed HIL Compatibility `31932303066`, Architecture Guard `31932303061`, Validate Provider-Owned Usage Event `31932303068`, and validate `31932303074`.

## Current tranche 8 — service-gateway activation proof transfer

Exact claim: `tasks/LLMA-WORKFLOW-CONSOLIDATION-SERVICE-GATEWAY-031.json`.

Direct inspection of `.github/workflows/service-gateway-deploy.yml` found a GitHub-hosted activation proof with:

```text
permissions: contents:read + id-token:write
GitHub OIDC issuer policy bound to service-gateway-deploy.yml
TVC receipt source labelled github_actions_runtime
runner-local STEGVERSE_HIL_RECEIPT_KEY generated with Python secrets.token_hex(48)
runner-local gateway launch using that generated value
ephemeral GitHub-hosted activation proof as execution venue
```

This conflicts with the canonical production path and TV/TVC-only credential authority. The workflow does not provide an admissible persistent runtime and cannot remain a production activation mechanism.

Disposition on this branch:

```text
.github/workflows/service-gateway-deploy.yml
  -> TRANSFER_TO_STEGVERSE_TASK_OR_WORKER
  removed by e62d4bb31a90aee7a444de2e0f52bd54ecf21bf5

.github/workflows/hil-deployment-profile.yml
  -> KEEP_STANDALONE_EXCEPTION_TEMPORARY_STABLE_DISPATCHER
  updated by 4a967ba10cca8d64b34382da3f77ad97fde2520b
```

The deterministic capability is preserved by adding `tests/test_service_gateway.py` to the token-refusing HIL compatibility dispatcher. That test set already validates TVC-bound readiness, durable PDF intake, idempotent duplicate recovery, Site-format submission receipt integrity, and rejection of provider keys in the intake role. No service-gateway source or test is deleted.

Production runtime/activation remains assigned to the resident sovereign carrier + StegVerse-Labs/.github #59/#65 under TV/TVC credential authority. HIL runtime/lifecycle remains owned by `StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md`; TVC #8 private-review work remains untouched.

If this exact tranche passes final-head validation and merges:

```text
workflow_files_baseline: 49
workflow_files_current_before_tranche: 28
workflow_files_after_tranche: 27
workflow_files_removed_or_consolidated_after_tranche: 22
classified_and_remediated_after_tranche: 23/49 = 46.94%
remaining_unclassified_or_unconsolidated: 26/49 audit-start surfaces
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
```

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

## Next safe families after claim 031 releases

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

## Validation / release requirements for tranche 8

```text
HIL Compatibility Validation: required PASS
Architecture Guard: required PASS
Validate Provider-Owned Usage Event: required PASS
validate: required PASS
PR changed-file set: exact bounded surfaces only
post-merge workflow-file count: direct verification required
claim 031: release to MERGED_INTO_CANONICAL_WORKSTREAM only after merge
handoff: finalize on main after merge
```

## Archive condition

This session remains a distinct support lane while workflow/token remediation remains incomplete. If tranche 8 merges, 27 workflow files will remain versus the adopted <=2 target, 26/49 audit-start surfaces will remain unclassified/unconsolidated, and `validate.yml` will still carry repository-token checkout/artifact/writeback mechanics that must be redistributed or redesigned. No archive claim is permitted until all session-specific requirements are complete, superseded, or durably transferred and no distinct validation/integration/reconciliation role remains.
