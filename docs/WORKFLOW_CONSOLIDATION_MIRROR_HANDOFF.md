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

## Released tranches 1-30

Latest release:

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

Tranche 30 removed the standalone `hil-deployment-profile.yml` hosted compatibility surface and preserved its deterministic source validation through `scripts/verify_hil_compatibility_full.py` inside canonical Goal 4. The first exact-head run correctly exposed an undeclared `jsonschema` test dependency; `jsonschema>=4.23` is now explicitly declared in the repository dev dependency set, and the corrected exact head passed all required validation. This does not alter HIL runtime authority.

Canonical HIL continuation remains:

```text
StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
TVC #8 authenticated private review: CLAIMED_FOR_IMPLEMENTATION
HIL product activation: 2/7 gates complete
StegVerse-Labs/Site#67 projection
master-records/orchestration#13
resident StegVerse carrier
```

No HIL activation, authenticated private-review decision, publication, Site mutation, Master Record release, wallet action, provider execution, Render dependency, GitHub/OIDC runtime authority, or non-TV/TVC secret/token is introduced.

## Global validation carrier

`.github/workflows/validate.yml` remains deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting — released work only

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 6
workflow_files_removed_or_consolidated_released: 43
classified_and_remediated_released: 46/49 = 93.88%
remaining_unclassified_or_unconsolidated_released: 3/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

Current default-branch workflow census:

```text
architecture-guard.yml
capability-runtime.yml
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
HIL runtime/backend: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
HIL private review: StegVerse-Labs/TVC#8
HIL Site projection: StegVerse-Labs/Site#67
HIL Master Records: master-records/orchestration#13
Ecosystem Chat runtime binding: StegVerse-org/LLM-adapter#18
VACC sovereign continuation: StegVerse-org/LLM-adapter#142 + tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
Math Solver machine continuation: StegVerse-org/LLM-adapter#72/#132 + Site#240 + StegCore#70
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The original local-model/runtime discovery/launch/inference/proof and formal local-model development are complete/released and are not duplicated. Live activation remains machine-owned and requires direct runtime evidence.

## Remaining workflow disposition work

`capability-runtime.yml` remains a strong `KEEP_STANDALONE_EXCEPTION` candidate because it uniquely validates Ubuntu, Windows and macOS portable capability/bootstrap/service/autostart behavior across Python 3.11/3.12. Its actual token/action mechanics still require explicit classification against the user's no-non-TV/TVC-token rule before final retention.

Still requiring fresh bounded disposition:

```text
publish-portable-node-image.yml
stegdeploy-image.yml
steggate-portable-consumer.yml
```

`architecture-guard.yml` and `validate.yml` remain core validation surfaces for now. `architecture-guard.yml` still contains hosted checkout/setup/artifact mechanics and a schedule; it is therefore not yet proven compatible with the stronger no-non-TV/TVC-token requirement and must be reconciled before this workstream can close.

Next safe bounded task: inspect the remaining portable-image publication pair (`publish-portable-node-image.yml`, `stegdeploy-image.yml`) against their canonical publication/runtime handoffs, determine whether publication belongs to a governed StegVerse worker rather than GitHub package authority, preserve repository-local deterministic image-contract validation in Goal 4, and eliminate duplicate hosted publication surfaces without granting GitHub token authority.

## Collision boundaries

- Do not duplicate TVC #8 authenticated private-review work.
- Do not manufacture HIL activation, publication, Site, or Master Records evidence.
- Do not create another Math Solver evaluator, provider route, or runtime carrier.
- Do not restore hosted schedules, token-backed setup, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Archive condition

This support session remains active while remaining workflow/token remediation is incomplete. Released main has 6 workflow files against the <=2 preference, 3/49 audit-start surfaces remain unclassified/unconsolidated, and retained hosted validation/publication surfaces still require explicit no-non-TV/TVC-token reconciliation.
