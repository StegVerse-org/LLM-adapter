# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: chore/consolidate-steggate-consumer-20260817
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: LLMA-WORKFLOW-CONSOLIDATE-STEGGATE-CONSUMER-055
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

Tranche 31 retired both GitHub package/OIDC image-publication workflows. StegDeploy now generates no protected provider/Master Records/review credentials, uses TV/TVC-injected protected values only, and defaults to a local image build with `pull_policy: never`. The last GHCR receipt is immutable historical evidence only.

Canonical StegDeploy continuation:

```text
StegVerse-Labs/.github/handoffs/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json
StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md
StegVerse-Labs/StegVerse-Healer/app/relay_stegdeploy_publication.py
StegVerse-org/core-node-runtime-demo/tools/stegdeploy_runtime_intake_local.py
StegVerse-org/LLM-adapter#18
```

## Active tranche 32 — consolidate StegGate portable consumer validation

Claim:

```text
tasks/LLMA-WORKFLOW-CONSOLIDATE-STEGGATE-CONSUMER-055.json
state: CLAIMED_FOR_IMPLEMENTATION
claimant: chatgpt-session-backend-support-20260817
release_condition: merge only after deterministic consumer checks execute through canonical Goal 4, hosted StegGate consumer workflow is absent, exact-head Architecture Guard and global validate PASS, post-merge workflow census is observed, and no new authority is introduced
```

Implementation installed on this branch:

```text
.github/workflows/steggate-portable-consumer.yml -> removed / CONSOLIDATE_INTO_STABLE_DISPATCHER
scripts/verify_steggate_portable_consumer.py -> deterministic canonical identity/receipt verifier
tests/test_steggate_portable_consumer.py -> retained deterministic consumer tests
scripts/verify_goal4_full.py -> now invokes both StegGate consumer test and deterministic verifier
llm_adapter/steggate_portable_consumer.py -> unchanged authority model; thin consumer delegates to canonical StegCore
```

Canonical StegGate ownership remains:

```text
canonical_owner: StegVerse-Labs/StegCore
canonical_commit: 8c484e584d60a3bd2763d6948d0eb3f4afd67e0c
runtime_binding: StegVerse-Labs/StegCore#70
adapter_runtime: StegVerse-org/LLM-adapter#18
transport_identity_authoritative: false
```

The removed workflow previously used checkout/setup/artifact Actions. The deterministic checks now live in the stable Goal 4 validation path and no GitHub artifact transport is required for this capability. This tranche has no activation, provider, publication, Site, Master Records custody, filing, or wallet/trade authority effect.

## Global validation carrier

`.github/workflows/validate.yml` remains deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 4
classified_and_remediated_released: 48/49 = 97.96%
active_branch_expected_workflow_files: 3
expected_if_tranche_32_releases_without_concurrent_change: 49/49 = 100.00%
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: LLMA-WORKFLOW-CONSOLIDATE-STEGGATE-CONSUMER-055
```

Expected active-branch workflow census:

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
Ecosystem Chat runtime binding: StegVerse-org/LLM-adapter#18
HIL private review: StegVerse-Labs/TVC#8
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The original local-model/runtime discovery/launch/inference/proof and formal local-model development are complete/released and are not duplicated. Live activation remains machine-owned and requires direct runtime evidence.

## Next bounded task after claim 055 releases

Reconcile `architecture-guard.yml` and `capability-runtime.yml` against the strict no-non-TV/TVC-token rule and the `<=2` final workflow target. `validate.yml` is already the credential-refusing stable dispatcher. Do not retain standalone hosted workflows merely because they historically carried validation.

## Collision boundaries

- Do not create another StegGate authority or evaluator.
- Do not change canonical StegCore identity or admit transport identity as authority.
- Do not compete with machine-owned resident carrier execution.
- Do not restore GitHub package/OIDC/runtime authority.
- Do not inject TV/TVC protected values into GitHub Actions.
- Do not duplicate TVC #8 authenticated private-review work.
- Do not manufacture activation, provider, publication, Site, Master Records, or trade evidence.
- Do not touch wallet signing, broadcast, settlement, or trade authority.

## Archive condition

This support session remains active while claim 055 and final workflow/token reconciliation are incomplete. The branch reduces the workflow surface from 4 to 3 and classifies the last audit-start workflow, but release requires exact-head validation and merge; afterward `architecture-guard.yml` and `capability-runtime.yml` still require explicit disposition against the stronger credential boundary and <=2 target.
