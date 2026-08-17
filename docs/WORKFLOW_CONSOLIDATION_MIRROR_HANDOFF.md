# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: chore/consolidate-va-privacy-runtime-validation-20260816
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: LLMA-WORKFLOW-CONSOLIDATE-VA-PRIVACY-RUNTIME-049
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

## Released tranches 1-25

Latest release:

```text
25 PR #171
final head: 6da12cb2562a76540fdb5d39faa0fc70e082bd60
merge: b3a17c81d89d2cc8a69497d4d0a277788389bc8b
Architecture Guard: 31987117708 SUCCESS
validate: 31987118201 SUCCESS
validate job: 95263934427 SUCCESS
67/67 substantive validation steps: SUCCESS
claim 048: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 11
classified/remediated: 41/49 = 83.67%
```

## Active tranche 26 — VA Claim Assistant privacy-runtime validation consolidation

Claim: `tasks/LLMA-WORKFLOW-CONSOLIDATE-VA-PRIVACY-RUNTIME-049.json`.

The specialized privacy handoff was read before mutation. `PII-RDY-06` implementation remains `RELEASED_COMPLETE`; the privacy gate must execute before classification/governed dispatch/model input, raw PII must fail closed without value/hash retention, only sanitized derived context is admitted, and privacy validation grants no provider/custody/filing/Site/wallet/activation authority.

Direct inspection of `.github/workflows/va-claim-assistant-privacy-runtime.yml` showed a six-hour scheduled GitHub-hosted surface using `contents: write`, `actions/checkout@v4`, `actions/setup-python@v5`, GitHub-hosted observation-source rewriting, repository commit/pull/push writeback, and `actions/upload-artifact@v4` with 90-day retention.

Installed on the active branch:

```text
.github/workflows/va-claim-assistant-privacy-runtime.yml
  -> CONSOLIDATE_INTO_CANONICAL_GOAL4
  -> removed
tests/test_va_claim_assistant_privacy_runtime.py
  -> retained local deterministic fixture/receipt generator
scripts/validate_va_claim_assistant_privacy_runtime.py
  -> retained fail-closed independent receipt/source-order validator
scripts/verify_goal4_full.py
  -> now executes both privacy fixture and validator in order
.github/workflows/validate.yml + exact iOS mirror
  -> already execute canonical Goal 4 using permissions: {}, anonymous exact-SHA fetch, and credential refusal
```

The specialized privacy handoff is also reconciled away from superseded provider task `VACP-ADAPTER-AUTHORIZED-EXECUTION-005`; current provider continuation is issue #142 + `tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json` under resident sovereign heartbeat -> TVC -> LLM-adapter -> Master Records with TV/TVC authority, credential requirement NONE, GitHub token requirement false, and GitHub-token runtime authority NONE.

Historical PR #99/run/artifact evidence remains provenance only. Current hosted validation regenerates a `LOCAL_DETERMINISTIC_VALIDATION` receipt only in the workspace and does not write it back or upload it.

No provider execution, custody, filing, Site mutation, wallet effect, GitHub/OIDC runtime authority, Render authority, repository writeback, artifact transport, or non-TV/TVC secret/token is introduced. Tranche 26 remains incomplete until exact-head Architecture Guard/global validate pass, PR merge, post-merge workflow census, claim 049 release, and main handoff finalization.

## Global validation carrier

`.github/workflows/validate.yml` and its exact iOS mirror remain deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting — released work only

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 11
workflow_files_removed_or_consolidated_released: 38
classified_and_remediated_released: 41/49 = 83.67%
remaining_unclassified_or_unconsolidated_released: 8/49
expected_if_tranche_26_releases_without_concurrent_change: 10 workflow files, 39 removed/consolidated, 42/49 = 85.71%, 7/49 remaining
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: LLMA-WORKFLOW-CONSOLIDATE-VA-PRIVACY-RUNTIME-049
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
VACC runtime/route implementation: StegVerse-org/LLM-adapter#90/#142
VA custody: master-records/orchestration#15
VA Site projection/privacy: StegVerse-Labs/Site#113/#116
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

## Collision boundaries

- Do not recreate sovereign local-model/runtime source work.
- Preserve privacy-before-classification/model-input ordering and no-retention guarantees.
- Do not reactivate GitHub Models/GITHUB_TOKEN VACC inference or superseded task 005.
- Do not restore hosted schedules, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Archive condition

This support session remains active while claim 049 and remaining workflow/token remediation are incomplete. Released main has 11 workflow files against the <=2 target and 8/49 audit-start surfaces remain unclassified/unconsolidated.
