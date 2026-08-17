# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: main
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: NONE
active_claim_state: UNCLAIMED
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

## Released tranches 1-31

Latest release:

```text
31 PR #177
final head: 604deca0faba6363f8200b34d0c9b93e1d41bd9f
merge: 3faf12ac43a62d3acd83aa5eca624119074c0ee2
Architecture Guard: 31997772865 SUCCESS
validate: 31997772867 SUCCESS
validate job: 95292426394 SUCCESS
67/67 substantive validation steps: SUCCESS
canonical Goal 4: SUCCESS
workflow parity: SUCCESS
claim 054: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 4
classified/remediated: 48/49 = 97.96%
```

Tranche 31 retired both GitHub package/OIDC image-publication workflows and corrected a stronger credential-boundary defect discovered during implementation: `scripts/stegdeploy_bootstrap.py` had generated provider, Master Records, review, and receipt credentials locally. It now generates none. Protected values are TV/TVC-injected only, optional privileged capabilities remain disabled/fail-closed when values are absent, and the runtime defaults to a local image build with `pull_policy: never` rather than GHCR continuity. The last GHCR receipt remains immutable historical evidence only.

Canonical StegDeploy continuation:

```text
StegVerse-Labs/.github/handoffs/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json
StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md
StegVerse-Labs/StegVerse-Healer/app/relay_stegdeploy_publication.py
StegVerse-org/core-node-runtime-demo/tools/stegdeploy_runtime_intake_local.py
StegVerse-org/LLM-adapter#18
```

No fresh image publication, persistent deployment, provider execution, custody, Site activation, release, or wallet/trade action is claimed by this release.

## Global validation carrier

`.github/workflows/validate.yml` remains deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting — released work only

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 4
workflow_files_removed_or_consolidated_released: 45
classified_and_remediated_released: 48/49 = 97.96%
remaining_unclassified_or_unconsolidated_released: 1/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

Current default-branch workflow census:

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
Ecosystem Chat runtime binding: StegVerse-org/LLM-adapter#18
HIL private review: StegVerse-Labs/TVC#8
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The original local-model/runtime discovery/launch/inference/proof and formal local-model development are complete/released and are not duplicated. Live activation remains machine-owned and requires direct runtime evidence.

## Remaining workflow disposition

One audit-start workflow surface remains unclassified:

```text
steggate-portable-consumer.yml
```

`capability-runtime.yml` remains a candidate standalone portability test but its hosted action/token mechanics still require explicit reconciliation with the no-non-TV/TVC-token rule. `architecture-guard.yml` still contains checkout/setup/artifact mechanics plus a schedule and likewise is not yet acceptable under the stronger rule. `validate.yml` is already credential-refusing, anonymous-fetch, permissions-empty validation-only.

Next safe bounded task: classify and consolidate `steggate-portable-consumer.yml`; then reconcile `architecture-guard.yml` and `capability-runtime.yml` so the final retained workflow count and mechanics satisfy the technical-minimum and TV/TVC-only credential boundary.

## Collision boundaries

- Do not compete with machine-owned Healer scheduler execution.
- Do not restore GitHub package/OIDC publication authority.
- Do not inject TV/TVC protected values into GitHub Actions.
- Do not duplicate TVC #8 authenticated private-review work.
- Do not manufacture activation, publication, Site, or Master Records evidence.
- Do not touch wallet signing, broadcast, settlement, or trade authority.

## Archive condition

This support session remains active while the final workflow/token reconciliation is incomplete. Released main has 4 workflow files against the <=2 preference, 1/49 audit-start workflow remains unclassified, and two retained hosted validation surfaces still require explicit no-non-TV/TVC-token reconciliation.
