# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: chore/retire-superseded-va-hosted-preflight-20260816
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: LLMA-WORKFLOW-RETIRE-SUPERSEDED-VA-PREFLIGHT-047
active_claim_state: CLAIMED_FOR_IMPLEMENTATION
role: ACTIVE_DISTINCT_SUPPORT
credential_authority: TV/TVC
github_token_runtime_authority: NONE
github_actions_activation_role: NONE
github_oidc_runtime_authority: NONE
third_party_runtime_authority: NONE
```

Production continuity remains `StegVerse task -> StegVerse worker -> TV/TVC authority -> StegVerse runtime -> StegVerse evidence/continuity`. GitHub Actions may validate source only.

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

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns live activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
platform-agnostic-runtime.yml: RETIRED/TRANSFERRED — sovereign runtime proof belongs to StegVerse runtime owners
hil-process-restart-controlled-cycle.yml: RETIRED/TRANSFERRED_TO_TVC
legacy third-party deployment manifests: RETIRED_AS_PRODUCTION_DEPENDENCY
```

## Released tranches 1-23

Latest release:

```text
23 PR #169
final head: 3c28f830d1b4384f3371a670a68d92b65caa33af
merge: 567aaeeae149f43c3ca4fc9ab973b5b08d195e55
Architecture Guard: 31980391501 SUCCESS
validate: 31980391463 SUCCESS
validate job: 95246068046 SUCCESS
67/67 substantive validation steps: SUCCESS
workflow parity: SUCCESS
canonical Goal 4: SUCCESS
validation-only authority boundary: SUCCESS
claim 046: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 14
classified/remediated: 38/49 = 77.55%
```

## Active tranche 24 — superseded VA hosted-preflight family retirement

Claim: `tasks/LLMA-WORKFLOW-RETIRE-SUPERSEDED-VA-PREFLIGHT-047.json`.

The specialized source of truth `docs/VA_CLAIM_ASSISTANT_PROVIDER_PREFLIGHT_MIRROR_HANDOFF.md` was read before mutation. It marks the historical GitHub-Models preflight `COMPLETE/SUPERSEDED` as an activation route. Current continuation is issue #142 + `tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json` under resident sovereign heartbeat -> TVC -> LLM-adapter -> Master Records with TV/TVC credential authority, credential requirement NONE, GitHub token requirement false, GitHub-token runtime authority NONE, third-party inference false, and hosted fallback DISALLOWED.

Initial retirement removed the stale validation wrapper and its obsolete validator:

```text
.github/workflows/validate-va-provider-preflight-hosted-path.yml
  -> ELIMINATE_SUPERSEDED_HOSTED_VALIDATION_WRAPPER
  -> removed
scripts/check_va_provider_preflight_hosted_path.py
  -> ELIMINATE_OBSOLETE_VALIDATOR_BOUND_TO_REMOVED_GITHUB_MODELS_PREFLIGHT
  -> removed
```

That mutation caused the separate `VA Provider Preflight Ubuntu 22.04 Proof` run `31986578857`, job `95262528654`, to fail closed in `Verify hosted-path contract` because it tried to execute the removed validator. Direct logs additionally proved that coupled workflow still used:

```text
GITHUB_TOKEN Contents: read / Metadata: read
actions/checkout@v4 with token
actions/setup-python@v5 with token
secrets.STEGVERSE_MASTER_RECORDS_TOKEN
actions/upload-artifact@v4
historical vendored TVC GitHub-hosted admission proof mechanics
```

That workflow is therefore part of the same superseded GitHub-hosted preflight experiment and violates the current no-non-TV/TVC-token boundary. It is now also removed on the active branch:

```text
.github/workflows/va-provider-preflight-ubuntu2204-proof.yml
  -> ELIMINATE_SUPERSEDED_HOSTED_PROOF_WORKFLOW
  -> removed
```

The specialized handoff preserves historical PR #120/run evidence while explicitly retaining only issue #142/task 023 as current continuation. No current sovereign activation predicate is removed and no replacement hosted workflow is created.

No provider execution, custody, filing, Site mutation, wallet effect, GitHub/OIDC authority, Render authority, repository writeback, artifact transport, or non-TV/TVC secret/token is introduced. Tranche 24 remains incomplete until fresh exact-head Architecture Guard/global validate pass after the coupled proof removal, PR #170 merges, post-merge workflow census is observed, claim 047 is released, and this handoff is finalized on main.

## Global validation carrier

`.github/workflows/validate.yml` and its exact iOS mirror remain deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting — released work only

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 14
workflow_files_removed_or_consolidated_released: 35
classified_and_remediated_released: 38/49 = 77.55%
remaining_unclassified_or_unconsolidated_released: 11/49
expected_if_tranche_24_releases_without_concurrent_change: 12 workflow files, 37 removed/consolidated, 40/49 = 81.63%, 9/49 remaining
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: LLMA-WORKFLOW-RETIRE-SUPERSEDED-VA-PREFLIGHT-047
```

## Canonical ownership / convergence

```text
organization authority: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
sovereign local model/runtime: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
formal local model development: COMPLETE_RELEASED
local runtime discovery/launch/inference/proof: COMPLETE_RELEASED
live local-model activation: StegVerse-Labs/.github#60 + resident sovereign heartbeat
credential/route authority: TV/TVC / StegVerse-Labs/TVC
Ecosystem Chat runtime binding: StegVerse-org/LLM-adapter#18
VACC sovereign execution continuation: StegVerse-org/LLM-adapter#142 + tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
VA custody: master-records/orchestration#15
VA Site projection/privacy: StegVerse-Labs/Site#113/#116
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

## Collision boundaries

- Do not recreate sovereign local-model/runtime source work.
- Do not reactivate GitHub Models/GITHUB_TOKEN VACC inference.
- Preserve historical PR/run evidence while retiring obsolete execution surfaces.
- Do not restore hosted schedules, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Archive condition

This support session remains active while claim 047 and remaining workflow/token remediation are incomplete. Released main has 14 workflow files against the <=2 target and 11/49 audit-start surfaces remain unclassified/unconsolidated.
