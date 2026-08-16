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
StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
```

## Retired hosted continuity provenance

These names are retained only for deterministic reconstruction and boundary tests. They are not active execution owners.

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns live activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
platform-agnostic-runtime.yml: RETIRED/TRANSFERRED — sovereign runtime proof belongs to StegVerse runtime owners
hil-process-restart-controlled-cycle.yml: RETIRED/TRANSFERRED_TO_TVC
legacy third-party deployment manifests: RETIRED_AS_PRODUCTION_DEPENDENCY
```

## Completed tranches 1-15

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
15 #161 c0ea3bd5c3c300cce3be7e8442f30def1c41b07b
```

Claims 025-038 are released.

### Tranche 12 — global validate credential and activation cleanup

Global `.github/workflows/validate.yml` and its iOS mirror are deterministic-validation-only: `permissions: {}`, anonymous exact-SHA fetch, explicit credential refusal, no schedule, no checkout/setup/upload actions, no hosted activation probe, no repository writeback, no GitHub token runtime/control-plane authority. Final validation run `31937093538` succeeded.

### Tranche 13 — provider-owned usage validation consolidated

PR #159 consolidated `verify_provider_usage_event.py` and its adversarial tests into global validate and removed the standalone provider-usage workflow. Final validate run `31937348003` succeeded.

### Tranche 14 — Ecosystem Chat sovereignty validation consolidated

PR #160 removed `.github/workflows/ecosystem-chat-service-adoption.yml` after preserving `scripts/check_ecosystem_chat_service_adoption.py` in global validate and the iOS mirror. Architecture Guard `31964932357` and validate `31964932396` succeeded. `StegVerse-org/LLM-adapter#18` remains the sovereignty/runtime continuation owner; TV/TVC remains runtime credential authority.

### Tranche 15 — outcome-level objective-contract validation consolidated

PR #161 merged at `c0ea3bd5c3c300cce3be7e8442f30def1c41b07b`; final implementation head `29d9df7b8710a8f11318208b80914caf4af6a5d4`.

The scheduled standalone `.github/workflows/validate-objective-contract.yml` was removed after its unique fail-closed capability was moved into the existing credential-clean global dispatcher and exact iOS mirror:

```text
$PYTHON_BIN scripts/validate_objective_contract.py
```

The validator continues to enforce the required outcome-level contract, downstream destinations, false-completion substitutes, false authority flags, evidence paths, and `manual_user_action_required=false` without granting provider, activation, custody, publication, deployment, wallet, or credential authority.

Initial run `31965351547` directly proved the objective-contract step but exposed that an active handoff rewrite had compressed away historical retired-workflow/invariant strings consumed by activation-boundary tests. Those provenance strings were restored instead of weakening tests. Fresh exact-head evidence then passed completely:

```text
Architecture Guard 31965418939 SUCCESS
validate 31965418919 SUCCESS
Validate outcome-level objective contract SUCCESS
Test live activation automation contract without executing activation SUCCESS
workflow parity SUCCESS
Confirm validation-only authority boundary SUCCESS
all 61 substantive validate steps SUCCESS
PR #161 merge c0ea3bd5c3c300cce3be7e8442f30def1c41b07b
```

Claim `tasks/LLMA-WORKFLOW-CONSOLIDATE-OBJECTIVE-CONTRACT-038.json` is released as `MERGED_INTO_CANONICAL_WORKSTREAM`.

## Current accounting

Post-tranche-14 direct default-branch enumeration showed 23 workflow files. Tranche 15 removed exactly one additional default-branch workflow file and added no workflow file, yielding 22 current files on main. Four GitHub Actions registry-only historical paths remain absent from main: `internal-governed-reference.yml`, `stack-conformance.yml`, `portable-node-process-restart-proof.yml`, and `authorized-provider-execution-boundary.yml`.

```text
workflow_files_baseline: 49
workflow_files_current_on_main: 22
workflow_files_removed_or_consolidated: 27
classified_and_remediated: 30/49 = 61.22%
remaining_unclassified_or_unconsolidated: 19/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

## Canonical ownership / convergence

```text
organization authority: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
sovereign local model/runtime: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
formal local model development: COMPLETE_RELEASED
local runtime discovery/launch/inference/proof: COMPLETE_RELEASED
live local-model activation: StegVerse-Labs/.github#60 + resident sovereign heartbeat
credential/route authority: TV/TVC / StegVerse-Labs/TVC
HIL runtime/lifecycle: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
LLM transport and Ecosystem Chat sovereignty: StegVerse-org/LLM-adapter#18
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The released local-model/runtime implementation is not duplicated in this workflow lane.

## Collision boundaries

- Do not recreate sovereign runtime source work.
- Do not compete with resident heartbeat, TVC route authority, or TVC HIL lifecycle.
- Do not infer live activation from workflow cleanup.
- Do not create non-TV/TVC runtime/test tokens.
- Do not restore GitHub-hosted activation, artifact transport, or repository writeback.
- Do not recreate retired standalone validation surfaces.
- Do not touch wallet/trade signing, broadcast, settlement, or StegFin provider execution.

## Next safe task

Under a fresh noncolliding claim, read the applicable specialized handoff and classify the next remaining default-branch workflow file against canonical StegVerse owners and the `<=2` target. Necessary deterministic checks should be consolidated into an existing credential-clean dispatcher where technically compatible; recurring operational capability must transfer to a named StegVerse worker before standalone workflow removal.

## Archive condition

This session remains a distinct support lane while workflow/token remediation remains incomplete. Twenty-two actual workflow files remain on main versus the adopted <=2 target, and 19/49 canonical audit-start surfaces remain unclassified/unconsolidated. No archive claim is permitted until all session-specific requirements are complete, superseded, or durably transferred and no distinct support role remains.
