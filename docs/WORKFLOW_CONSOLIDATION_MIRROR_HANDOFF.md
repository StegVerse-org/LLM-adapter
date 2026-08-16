# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: main
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: NONE
role: ACTIVE_DISTINCT_SUPPORT
credential_authority: TV/TVC
github_token_runtime_authority: NONE
github_actions_activation_role: NONE
github_oidc_runtime_authority: NONE
third_party_runtime_authority: NONE
```

Production continuity remains `StegVerse task -> StegVerse worker -> TV/TVC authority -> StegVerse runtime -> StegVerse evidence/continuity`. GitHub Actions may validate source only. Third-party runtimes are not production continuity dependencies.

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
third-party production/runtime dependency: prohibited
```

## Retired hosted continuity provenance

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns live activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
platform-agnostic-runtime.yml: RETIRED/TRANSFERRED
hil-process-restart-controlled-cycle.yml: RETIRED/TRANSFERRED_TO_TVC
legacy third-party deployment manifests: RETIRED_AS_PRODUCTION_DEPENDENCY
```

## Completed tranches 1-14

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
14 #160 c7bb207042259b11060e8cf8d93019a7cff0ccbe
```

All completed tranche claims 025-037 are released.

### Tranche 10

Hosted `platform-agnostic-runtime.yml` was retired because it created non-TV/TVC credential-shaped HIL values. Sovereign local runtime discovery/launch/inference/proof remains `COMPLETE_RELEASED` in `StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md`.

### Tranche 11

`capability-runtime.yml` remains a temporary cross-platform validation exception but is credential-clean: `permissions: {}`, anonymous exact-SHA source acquisition, no checkout/setup actions, explicit credential refusal, no writeback, 3-OS × Python 3.11/3.12 matrix, and cancel-in-progress. Validation run `31936410223` passed 6/6 matrix jobs.

### Tranche 12

PR #158 made global `validate.yml` and its iOS mirror deterministic-validation-only and credential-clean. Schedule, checkout/setup actions, artifact upload, hosted live activation probe, and GitHub writeback were removed. Final validation: Architecture Guard `31937093509` SUCCESS; Provider-Owned Usage `31937093522` SUCCESS; validate `31937093538` SUCCESS with 57/57 validation steps successful.

### Tranche 13 — provider-owned usage validation consolidated

PR #159 merged at `ee193f96c1d3b6fca2f0d1d009536fec83c6a884`; final implementation head `24b1205eddd5a7768fb1804fe142afda9a2782fa`. `.github/workflows/validate-provider-usage-event.yml` was consolidated into the token-clean global dispatcher. Final validation: Architecture Guard `31937348046` SUCCESS; validate `31937348003` SUCCESS with 59/59 validation steps successful; provider-event validator, adversarial tests, and workflow parity all passed. Claim 036 is released.

### Tranche 14 — Ecosystem Chat sovereignty validation consolidated

PR #160 merged at `c7bb207042259b11060e8cf8d93019a7cff0ccbe`; final implementation head `a7bf10d659fa329654d757644c97b01835ca1ce6`.

`.github/workflows/ecosystem-chat-service-adoption.yml` was classified `CONSOLIDATE_INTO_STABLE_DISPATCHER` and removed. Its unique deterministic sovereignty check is retained in `.github/workflows/validate.yml` and its exact iOS mirror:

```text
$PYTHON_BIN scripts/check_ecosystem_chat_service_adoption.py
```

`docs/ECOSYSTEM_CHAT_SERVICE_ADOPTION_MIRROR_HANDOFF.md` now points validation automation to `.github/workflows/validate.yml` while preserving `StegVerse-org/LLM-adapter#18` as the runtime/sovereignty continuation owner and TV/TVC as runtime credential authority.

Final-head evidence:

```text
Architecture Guard 31964932357 SUCCESS
validate 31964932396 SUCCESS
Validate Ecosystem Chat zero-external-dependency sovereignty contract SUCCESS
workflow parity SUCCESS
all 60 substantive validate steps SUCCESS
PR #160 merge c7bb207042259b11060e8cf8d93019a7cff0ccbe
```

Claim `tasks/LLMA-WORKFLOW-CONSOLIDATE-SERVICE-ADOPTION-037.json` is released as `MERGED_INTO_CANONICAL_WORKSTREAM`.

## Current accounting and live-registry reconciliation

```text
workflow_files_baseline: 49
released_lineage_expected_workflow_files_after_tranche_14: 23
workflow_files_removed_or_consolidated_from_audit_start: 26
classified_and_remediated: 29/49 = 59.18%
remaining_unclassified_or_unconsolidated_from_audit_start: 20/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

A direct post-merge GitHub Actions registry query reported `total_count: 27` registered active workflows. That does not agree with the prior handoff lineage count of 23 expected files after tranche 14. Because live repository state is authoritative, the next task is not allowed to assume 23 as the operational count. A fresh reconciliation must identify the four-workflow delta as concurrent additions, registry-retained entries, or prior accounting omissions before the next consolidation claim. Until reconciled, use:

```text
live_registered_workflow_count: 27
canonical_audit_start_denominator: 49
canonical_classified_remediated: 29/49
operational_file_count: RECONCILIATION_REQUIRED
```

## Canonical ownership / convergence

```text
organization authority: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
sovereign local model/runtime: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
live local-model activation: StegVerse-Labs/.github#60 + resident sovereign heartbeat
credential authority: TV/TVC
route authority: StegVerse-Labs/TVC
HIL runtime/lifecycle: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
LLM transport and Ecosystem Chat sovereignty owner: StegVerse-org/LLM-adapter#18
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

Formal local-model development and actual discovery/launch/inference/proof are `COMPLETE_RELEASED`; do not duplicate them.

## Collision boundaries

- Do not recreate sovereign runtime source work.
- Do not compete with resident heartbeat, TVC route authority, or TVC HIL lifecycle.
- Do not infer live activation from workflow cleanup.
- Do not create non-TV/TVC runtime/test tokens.
- Do not restore GitHub-hosted activation, artifact transport, or repository writeback.
- Do not recreate provider-owned usage-event or Ecosystem Chat service-adoption standalone validation.
- Do not touch wallet/trade signing, broadcast, settlement, or StegFin provider execution.

## Next safe task

First reconcile the live `27` registered workflow count against the canonical 49-surface audit and the released lineage. Then, under a fresh noncolliding claim, classify the next remaining workflow surface against canonical StegVerse owners and the `<=2` target. Any necessary deterministic validation should be consolidated into an existing token-clean dispatcher where technically compatible; any recurring operational capability belongs to a named StegVerse worker before standalone workflow removal.

## Archive condition

This session remains a distinct support lane while workflow/token remediation remains incomplete. The live Actions registry reports 27 active registered workflows versus the adopted <=2 target, 20/49 canonical audit-start surfaces remain unclassified/unconsolidated, and the registry/file-lineage delta requires reconciliation. No archive claim is permitted until all session-specific requirements are complete, superseded, or durably transferred and no distinct support role remains.
