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
github_actions_activation_role: NONE
github_oidc_runtime_authority: NONE
render_runtime_authority: NONE
```

Production continuity remains `StegVerse task -> StegVerse worker -> TV/TVC authority -> StegVerse runtime -> StegVerse evidence/continuity`. GitHub Actions may validate source only. Render and other third-party runtimes are not production continuity dependencies.

## Sovereign authority invariants

```text
resident carrier owns continuity
resident StegVerse carrier + TV/TVC
resident sovereign carrier
GitHub token as provider credential: prohibited
GitHub token as runtime/control-plane authority: prohibited
GitHub Actions activation role: NONE
GitHub OIDC as runtime/control-plane authority: prohibited
repository secrets for provider/Master Records production path: prohibited
TV/TVC protected values exported into GitHub Actions: prohibited
GitHub-hosted runtime secret generation: prohibited
non-TV/TVC test-token substitution: prohibited
Render production/runtime dependency: prohibited
```

## Retired hosted continuity provenance

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns live activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
platform-agnostic-runtime.yml: RETIRED/TRANSFERRED
hil-process-restart-controlled-cycle.yml: RETIRED/TRANSFERRED_TO_TVC
render-production.yaml: RETIRED_AS_PRODUCTION_DEPENDENCY
render.yaml: RETIRED_AS_PRODUCTION_DEPENDENCY
```

## Completed tranches 1-13

```text
1 #145 c9f561254ec5671c2329c3deb7ce0bfb511331ab
2 transfer b5ec49b78c58c0cf9592b19b2e1b02825c96ec3f
3 #149 0bd06fcdda1ba7fe736fde1d131b702e57080e3a
4 #150 ec16f9f681ebbac4b34e1e3af1607145153ff14c
5 #151 6b5db6e9415fc76da2979943ca6cb9281626ffdb
6 #152 91bb8578662fe2ef0e6276516efb98fce78827b0
7 #153 a314dbc3e82a0155b59067d59381995bb74b300f
8 #154 85fe10fe40da948596662daba16f13c7f3eb531c
9 #155 ec4d668038da9ad6a439007c71c9b2b2df091fbb
10 #156 837799aa5c4e6ee64ffc86902216eb36e53ebd36
11 #157 310f0225d3700fda735d3f2d70943a12e9bda0cc
12 #158 695ad0723d303b140c19c6c15abbb8f0653b05ee
13 #159 ee193f96c1d3b6fca2f0d1d009536fec83c6a884
```

All completed tranche claims 025-036 are released.

### Tranche 10

Hosted `platform-agnostic-runtime.yml` was retired because it created non-TV/TVC credential-shaped HIL values. Sovereign local runtime discovery/launch/inference/proof remains `COMPLETE_RELEASED` in `StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md`.

### Tranche 11

`capability-runtime.yml` remains a temporary cross-platform validation exception but is credential-clean: `permissions: {}`, anonymous exact-SHA source acquisition, no checkout/setup actions, explicit credential refusal, no writeback, 3-OS × Python 3.11/3.12 matrix, and cancel-in-progress. Validation run `31936410223` passed 6/6 matrix jobs.

### Tranche 12

PR #158 made global `validate.yml` and its iOS mirror deterministic-validation-only and credential-clean. Schedule, checkout/setup actions, artifact upload, hosted live activation probe, and GitHub writeback were removed. Final validation: Architecture Guard `31937093509` SUCCESS; Provider-Owned Usage `31937093522` SUCCESS; validate `31937093538` SUCCESS with 57/57 validation steps successful.

### Tranche 13 — provider-owned usage validation consolidated

PR #159 merged at `ee193f96c1d3b6fca2f0d1d009536fec83c6a884`; final implementation head `24b1205eddd5a7768fb1804fe142afda9a2782fa`.

`.github/workflows/validate-provider-usage-event.yml` was classified `CONSOLIDATE_INTO_STABLE_DISPATCHER` and removed. Its unique deterministic checks are now in the token-clean global `validate.yml` and exact iOS mirror:

```text
$PYTHON_BIN scripts/verify_provider_usage_event.py
$PYTHON_BIN -m pytest -q tests/test_provider_usage_event.py
```

This removed an `actions/checkout` + `actions/setup-python` workflow without dropping the provider-owned usage-event validator or adversarial test capability. No live provider request, custody operation, activation, publication, repository writeback, or credential authority was added.

Final validation:

```text
Architecture Guard 31937348046 SUCCESS
validate 31937348003 SUCCESS — 59/59 validation steps SUCCESS
provider-owned usage-event validator SUCCESS
provider-owned usage-event adversarial tests SUCCESS
workflow parity SUCCESS
```

Claim `tasks/LLMA-WORKFLOW-CONSOLIDATE-PROVIDER-USAGE-036.json` is released as `MERGED_INTO_CANONICAL_WORKSTREAM`.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current: 24
workflow_files_removed_or_consolidated: 25
classified_and_remediated: 28/49 = 57.14%
remaining_unclassified_or_unconsolidated: 21/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

## Canonical ownership / convergence

```text
organization authority: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
sovereign local model/runtime: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
live local-model activation: StegVerse-Labs/.github#60 + resident sovereign heartbeat
credential authority: TV/TVC
route authority: StegVerse-Labs/TVC
HIL runtime/lifecycle: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
LLM transport: StegVerse-org/LLM-adapter#18
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

Formal local-model development and actual discovery/launch/inference/proof are `COMPLETE_RELEASED`; do not duplicate them.

## Collision boundaries

- Do not recreate sovereign runtime source work.
- Do not compete with resident heartbeat, TVC route authority, or TVC HIL lifecycle.
- Do not infer live activation from workflow cleanup.
- Do not create non-TV/TVC runtime/test tokens.
- Do not restore GitHub-hosted activation, artifact transport, or repository writeback.
- Do not recreate provider-owned usage-event standalone validation.
- Do not touch wallet/trade signing, broadcast, settlement, or StegFin provider execution.

## Next safe task

Classify the next remaining GitHub workflow surface against canonical StegVerse owners and the `<=2` target. Any necessary deterministic validation should be consolidated into an existing token-clean dispatcher where technically compatible; any recurring operational capability belongs to a named StegVerse worker before standalone workflow removal.

## Archive condition

This session remains a distinct support lane while workflow/token remediation remains incomplete. Twenty-four workflow files remain versus the adopted <=2 target and 21/49 audit-start surfaces remain unclassified/unconsolidated. No archive claim is permitted until all session-specific requirements are complete, superseded, or durably transferred and no distinct support role remains.
