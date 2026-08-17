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

## Retired hosted continuity provenance

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns live activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
platform-agnostic-runtime.yml: RETIRED/TRANSFERRED — sovereign runtime proof belongs to StegVerse runtime owners
hil-process-restart-controlled-cycle.yml: RETIRED/TRANSFERRED_TO_TVC
legacy third-party deployment manifests: RETIRED_AS_PRODUCTION_DEPENDENCY
```

## Released tranches 1-25

Latest releases:

```text
24 PR #170
final head: 2cfc47455737278607ae7588ce53ce7fff39fcdd
merge: d32b97517cad5933f26639a63156b928559661b2
Architecture Guard: 31986711716 SUCCESS
validate: 31986711718 SUCCESS
validate job: 95262878966 SUCCESS
67/67 substantive validation steps: SUCCESS
claim 047: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 12
classified/remediated: 40/49 = 81.63%

25 PR #171
final head: 6da12cb2562a76540fdb5d39faa0fc70e082bd60
merge: b3a17c81d89d2cc8a69497d4d0a277788389bc8b
Architecture Guard: 31987117708 SUCCESS
validate: 31987118201 SUCCESS
validate job: 95263934427 SUCCESS
67/67 substantive validation steps: SUCCESS
canonical Goal 4: SUCCESS including VA runtime-contract validator
workflow parity: SUCCESS
validation-only authority boundary: SUCCESS
claim 048: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 11
classified/remediated: 41/49 = 83.67%
```

Tranche 25 removed `.github/workflows/va-claims-chat-runtime-contract.yml`, retiring its six-hour schedule, `contents: write`, persisted checkout credentials, repository commit/pull/push writeback, and artifact upload. `scripts/validate_va_claims_chat_runtime_contract.py` remains fail-closed and is now invoked by `scripts/verify_goal4_full.py`; both the credential-clean global dispatcher and its exact iOS mirror execute that Goal 4 aggregate. The committed PASS receipt remains release evidence while hosted regeneration is workspace-local only.

## Global validation carrier

`.github/workflows/validate.yml` and its exact iOS mirror remain deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current_on_main: 11
workflow_files_removed_or_consolidated_released: 38
classified_and_remediated_released: 41/49 = 83.67%
remaining_unclassified_or_unconsolidated_released: 8/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

Current default-branch workflow files are:

```text
architecture-guard.yml
capability-runtime.yml
hil-deployment-profile.yml
llm-adapter-open-pr-consolidation.yml
math-solver-governed-runtime.yml
publish-portable-node-image.yml
stegdeploy-image.yml
steggate-portable-consumer.yml
va-claim-assistant-governed-retrieval.yml
va-claim-assistant-privacy-runtime.yml
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
VACC runtime/route implementation: StegVerse-org/LLM-adapter#90/#142
VA custody: master-records/orchestration#15
VA Site projection/privacy: StegVerse-Labs/Site#113/#116
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The original local-model/runtime implementation is complete/released and is not reopened by this workflow-maintenance lane.

## Collision boundaries

- Do not recreate sovereign local-model/runtime source work.
- Do not reactivate GitHub Models/GITHUB_TOKEN VACC inference.
- Preserve VACC route/document/filing/privacy authority boundaries when consolidating validators.
- Do not restore hosted schedules, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Next safe task

Under a fresh noncolliding claim, read the applicable specialized handoff and classify the next remaining default-branch workflow surface against canonical StegVerse owners and the `<=2` target. Prefer deterministic validation/privacy contract surfaces before publication, package/image creation, HIL lifecycle, or other stateful outputs.

## Archive condition

This support session remains active while workflow/token remediation is incomplete. Released main has 11 workflow files against the <=2 target and 8/49 audit-start surfaces remain unclassified/unconsolidated. The original local-model/runtime implementation is already complete/released and live activation remains machine-owned.
