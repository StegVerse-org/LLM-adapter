# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: chore/retire-github-image-publication-20260817
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: LLMA-WORKFLOW-RETIRE-GITHUB-IMAGE-PUBLICATION-054
active_claim_state: CLAIMED_FOR_IMPLEMENTATION
role: ACTIVE_DISTINCT_SUPPORT
credential_authority: TV/TVC
github_token_runtime_authority: NONE
github_actions_activation_role: NONE
github_actions_publication_authority: NONE
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
GitHub token as image-publication authority: prohibited
GitHub Actions activation role: NONE
GitHub Actions publication role: NONE
GitHub OIDC as runtime/control-plane authority: prohibited
repository secrets for provider/Master Records production path: prohibited
TV/TVC protected values exported into GitHub Actions: prohibited
GitHub-hosted runtime secret generation: prohibited
non-TV/TVC test-token substitution: prohibited
third-party production/runtime dependency: prohibited
StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
```

## Retired activation provenance

These historical workflow names remain recorded because their absence from the live workflow tree plus explicit transfer of continuity is a validation invariant, not a request to restore them.

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
```

## Released tranches 1-30

Latest released tranche:

```text
30 PR #176
final head: e6ec55dd6de7969af892437529020e465c6ea376
merge: f85b74b5cc1e5b5219a5382ccd6a0cc1d93c33b1
Architecture Guard: 31997014471 SUCCESS
validate: 31997014472 SUCCESS
validate job: 95290357412 SUCCESS
67/67 substantive validation steps: SUCCESS
canonical Goal 4: SUCCESS
workflow parity: SUCCESS
claim 053: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 6
classified/remediated: 46/49 = 93.88%
```

## Active tranche 31 — retire GitHub image-publication authority

Authoritative handoffs read before mutation:

```text
docs/STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md
StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md
```

The Healer handoff already records GitHub API workflow dispatch and GitHub production credentials as superseded, and binds StegDeploy continuation to the resident sovereign heartbeat plus `healer-sovereign-scheduler-worker`. Its relay consumes materialized local state; core-node intake requires the exact image digest to already exist in the local Docker store and does not log in to or pull from GHCR.

Claim `tasks/LLMA-WORKFLOW-RETIRE-GITHUB-IMAGE-PUBLICATION-054.json` therefore removes the two remaining GitHub publication surfaces rather than injecting TV/TVC credentials into them:

```text
.github/workflows/publish-portable-node-image.yml -> removed / TRANSFER_TO_STEGVERSE_WORKER
.github/workflows/stegdeploy-image.yml -> removed / TRANSFER_TO_STEGVERSE_WORKER
```

Source/runtime corrections installed in the same bounded tranche:

```text
compose.stegdeploy.yaml
  default image: stegverse/llm-adapter:local
  local Dockerfile build
  pull_policy: never
scripts/stegdeploy_bootstrap.py
  local compose build, no registry pull
  no locally generated provider/Master Records/review credentials
  credential_authority: TV/TVC
  generated_credentials: false
scripts/verify_stegdeploy_runtime.py
  proves local-build/no-registry/no-generated-secret boundary
scripts/check_stegdeploy_image_receipt_retention.py
  validates last GHCR receipt as immutable historical evidence only
scripts/check_stegdeploy_image_publication_readiness.py
  projects LOCAL_CONTINUATION_READY only when hosted workflows are absent and sovereign handoff markers are present
docs/STEGDEPLOY_PUBLICATION_MIRROR_HANDOFF.md
  github_actions_publication_authority: NONE
  historical_ghcr_receipt_retained: true
```

The last successful GHCR receipt remains historical evidence. This tranche does not claim a fresh publication, persistent deployment, provider execution, custody, Site activation, release, or wallet/trade action.

Release requires exact-head Architecture Guard and global validate PASS, canonical Goal 4 success, both hosted publication workflows absent, post-merge workflow census, and released claim 054.

## Global validation carrier

`.github/workflows/validate.yml` remains deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 6
classified_and_remediated_released: 46/49 = 93.88%
remaining_unclassified_or_unconsolidated_released: 3/49
active_branch_expected_workflow_files: 4
expected_if_tranche_31_releases_without_concurrent_change: 48/49 = 97.96%, 1/49 remaining
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: LLMA-WORKFLOW-RETIRE-GITHUB-IMAGE-PUBLICATION-054
```

Released-main workflow census:

```text
architecture-guard.yml
capability-runtime.yml
publish-portable-node-image.yml
stegdeploy-image.yml
steggate-portable-consumer.yml
validate.yml
```

Expected active-branch census after this tranche's removals:

```text
architecture-guard.yml
capability-runtime.yml
steggate-portable-consumer.yml
validate.yml
```

## Canonical ownership / convergence

```text
organization authority: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
sovereign local model/runtime: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
formal local model development: COMPLETE_RELEASED
local runtime discovery/launch/inference/proof: COMPLETE_RELEASED
live local-model activation: StegVerse-Labs/.github#60 + resident sovereign heartbeat
credential/route authority: TV/TVC / StegVerse-Labs/TVC
StegDeploy scheduler: StegVerse-Labs/.github/handoffs/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json
StegDeploy Healer continuation: StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md
StegDeploy local relay: StegVerse-Labs/StegVerse-Healer/app/relay_stegdeploy_publication.py
StegDeploy local intake: StegVerse-org/core-node-runtime-demo/tools/stegdeploy_runtime_intake_local.py
Ecosystem Chat runtime binding: StegVerse-org/LLM-adapter#18
HIL private review: StegVerse-Labs/TVC#8
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The original local-model/runtime discovery/launch/inference/proof and formal local-model development are complete/released and are not duplicated. Live activation remains machine-owned and requires direct runtime evidence.

## Remaining workflow disposition after claim 054 releases

One audit-start workflow surface remains unclassified:

```text
steggate-portable-consumer.yml
```

`capability-runtime.yml` remains a candidate standalone portability test but its hosted action/token mechanics still require explicit reconciliation with the no-non-TV/TVC-token rule. `architecture-guard.yml` still contains checkout/setup/artifact mechanics plus a schedule and likewise is not yet acceptable under the stronger rule. `validate.yml` is already credential-refusing, anonymous-fetch, permissions-empty validation-only.

Next safe bounded task after claim 054: classify and consolidate `steggate-portable-consumer.yml`, then reconcile `architecture-guard.yml` and `capability-runtime.yml` so final retained workflow count and token mechanics satisfy the technical-minimum and TV/TVC-only credential boundary.

## Collision boundaries

- Do not compete with machine-owned Healer scheduler execution.
- Do not restore GitHub package/OIDC publication authority.
- Do not inject TV/TVC protected values into GitHub Actions.
- Do not duplicate TVC #8 authenticated private-review work.
- Do not manufacture activation, publication, Site, or Master Records evidence.
- Do not touch wallet signing, broadcast, settlement, or trade authority.

## Archive condition

This support session remains active while claim 054 and final workflow/token reconciliation are incomplete. Released main has 6 workflow files against the <=2 preference; the active branch has removed two publication workflows but that result is not released until exact-head validation and merge complete.
