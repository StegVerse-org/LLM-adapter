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

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
```

## Released tranches 1-32

Latest release:

```text
32 PR #178
final head: 0b7588b8c80cb3dd5e97a9dcb4c947a5557731d6
merge: 9ff6304f9a84b28ca54db86ae9faeb7814f84651
Architecture Guard: 32002977860 SUCCESS
validate: 32002977858 SUCCESS
validate job: 95306767617 SUCCESS
67/67 substantive validation steps: SUCCESS
canonical Goal 4: SUCCESS
claim 055: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 3
classified/remediated: 49/49 = 100.00%
```

Tranche 32 removed `.github/workflows/steggate-portable-consumer.yml`, retained deterministic consumer tests, added `scripts/verify_steggate_portable_consumer.py`, and folded both checks into `scripts/verify_goal4_full.py`. StegCore remains canonical owner at commit `8c484e584d60a3bd2763d6948d0eb3f4afd67e0c`; transport identity remains non-authoritative. No GitHub artifact transport is required for this capability.

Tranche 31 remains the canonical retirement of GitHub package/OIDC image-publication authority. StegDeploy generates no protected provider/Master Records/review credentials, uses TV/TVC-injected protected values only, and defaults to local image build with `pull_policy: never`.

## Global validation carrier

`.github/workflows/validate.yml` is deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 3
classified_and_remediated_released: 49/49 = 100.00%
remaining_unclassified_audit_start_surfaces: 0
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

Current default-branch workflow census:

```text
architecture-guard.yml
capability-runtime.yml
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

## Next bounded task

Reconcile `architecture-guard.yml` and `capability-runtime.yml` against the strict no-non-TV/TVC-token rule and the `<=2` final workflow target. `validate.yml` is already the credential-refusing stable dispatcher. Do not retain standalone hosted workflows merely because they historically carried validation.

## Collision boundaries

- Do not compete with machine-owned resident carrier or Healer scheduler execution.
- Do not restore GitHub package/OIDC/runtime authority.
- Do not inject TV/TVC protected values into GitHub Actions.
- Do not duplicate TVC #8 private-review work.
- Do not manufacture activation, provider, publication, Site, Master Records, or trade evidence.
- Do not touch wallet signing, broadcast, settlement, or trade authority.

## Archive condition

This support session remains active while the final retained workflow/token reconciliation is incomplete. Audit-start classification is now complete at 49/49 and the released tree has 3 workflows, but `architecture-guard.yml` and `capability-runtime.yml` still require explicit disposition against the stronger credential boundary and <=2 technical-minimum target.
