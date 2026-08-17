# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: main
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: NONE
active_claim_state: NONE
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

## Retired activation provenance

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
```

## Released tranches 1-28

Latest releases:

```text
27 PR #173
final head: e6f100b2dd4c3c024239a50248a71e379f42d5ce
merge: cf51da459b0317f12c58fa3c365630a104439706
Architecture Guard: 31989374647 SUCCESS
validate: 31989374615 SUCCESS
validate job: 95270003644 SUCCESS
67/67 substantive validation steps: SUCCESS
claim 050: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 9
classified/remediated: 43/49 = 87.76%

28 PR #174
final head: e453eee4adf4814810870b18905d333e6d6b6a40
merge: 842b6980f227a2b1e44f6b4431fbdca7fe88d8b0
Architecture Guard: 31989860425 SUCCESS
validate: 31989860454 SUCCESS
validate job: 95271358484 SUCCESS
67/67 substantive validation steps: SUCCESS
canonical Goal 4: SUCCESS
workflow parity: SUCCESS
claim 051: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 8
classified/remediated: 44/49 = 89.80%
```

Tranche 28 retired `.github/workflows/llm-adapter-open-pr-consolidation.yml`, which used token-backed checkout/setup, `GH_TOKEN: ${{ github.token }}`, fixed-list `gh api` polling and artifact upload for an already `COMPLETE`/archive-safe bounded reconciliation task. Historical inventory, validator, task record, receipt and immutable PR/run/artifact evidence remain preserved. `docs/LLM_ADAPTER_MIRROR_HANDOFF.md` now identifies historical Render/provider state as provenance only and points current authority to the resident StegVerse heartbeat, TV/TVC, current adapter owners and Master Records.

The first exact-head validate run `31989735496` failed closed because the historical orchestration validator still required the now-retired workflow. That coupling was corrected by installing `scripts/check_llm_adapter_orchestration_state_current.py` and changing canonical Goal 4 to use the supersession-aware validator while retaining the old orchestration validator as historical provenance. The final exact head then passed Architecture Guard and all 67 global-validation substantive steps. No current PR state was mutated as part of cleanup.

## Global validation carrier

`.github/workflows/validate.yml` and its exact iOS mirror remain deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current_on_main: 8
workflow_files_removed_or_consolidated_released: 41
classified_and_remediated_released: 44/49 = 89.80%
remaining_unclassified_or_unconsolidated_released: 5/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

Current default-branch workflow files are:

```text
architecture-guard.yml
capability-runtime.yml
hil-deployment-profile.yml
math-solver-governed-runtime.yml
publish-portable-node-image.yml
stegdeploy-image.yml
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
Ecosystem Chat runtime binding: StegVerse-org/LLM-adapter#18
VACC sovereign continuation: StegVerse-org/LLM-adapter#142 + tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
Master Records: master-records/orchestration
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The original local-model/runtime discovery/launch/inference/proof and formal local-model development are complete/released and are not duplicated. Live activation remains machine-owned and requires direct runtime evidence.

## Remaining workflow disposition work

`capability-runtime.yml` has been directly inspected: it is credential-clean (`permissions: {}` plus explicit credential refusal), has no schedule/writeback/artifact transport, and uniquely validates the portable capability/bootstrap/service/autostart surface across Ubuntu, Windows, macOS and Python 3.11/3.12. Its latest observed exact-head run during tranche 27 was SUCCESS. It is therefore a strong `KEEP_STANDALONE_EXCEPTION` candidate unless an equally strong cross-platform replacement is installed.

Still requiring fresh bounded disposition:

```text
hil-deployment-profile.yml
math-solver-governed-runtime.yml
publish-portable-node-image.yml
stegdeploy-image.yml
steggate-portable-consumer.yml
```

`architecture-guard.yml` and `validate.yml` are currently retained core deterministic validation surfaces. Any attempt to combine them must prove no loss of boundary coverage.

## Collision boundaries

- Do not recreate sovereign local-model/runtime source work.
- Do not reopen completed task 016 or restore GitHub-token API polling.
- Preserve unique multi-platform capability validation unless a verified replacement exists.
- Do not treat historical PR snapshots or Render evidence as current runtime authority.
- Do not restore hosted schedules, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Archive condition

This support session remains active while workflow/token remediation is incomplete. Main has 8 workflow files against the <=2 preference and 5/49 audit-start surfaces remain unclassified/unconsolidated. The original local-model/runtime implementation is already complete/released and live activation remains machine-owned.
