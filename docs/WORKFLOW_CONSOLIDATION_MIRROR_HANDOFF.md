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

These names are retained only for deterministic reconstruction and boundary tests. They are not active production or activation owners and must not be recreated as such.

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns live activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
platform-agnostic-runtime.yml: RETIRED/TRANSFERRED — sovereign runtime proof belongs to StegVerse runtime owners
hil-process-restart-controlled-cycle.yml: RETIRED/TRANSFERRED_TO_TVC
legacy third-party deployment manifests: RETIRED_AS_PRODUCTION_DEPENDENCY
```

## Released tranches 1-23

Latest releases:

```text
22 PR #168
final head: 9c64c385e80b2bf9f44dd44996f5feb3b41b2f4d
merge: 2068b11061f08d5b6e602dd46b66dc35b34620ca
Architecture Guard: 31979872823 SUCCESS
validate: 31979872814 SUCCESS
claim 045: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 15
classified/remediated: 37/49 = 75.51%

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

Tranche 23 removed `.github/workflows/validate-tv-tvc-service-return.yml`, which was only a `workflow_call`/`workflow_dispatch` GitHub wrapper using `contents: read`, `actions/checkout@v4`, and `actions/setup-python@v5`. Repository search found no callers. The actual fail-closed capability remains `scripts/validate_tv_tvc_service_return.py`, which independently validates bundle/request/receipt hashes, invoice/receipt and ledger/bundle binding, requester-return binding, and rejects service returns that imply Master Record authority. No TV/TVC bundle semantics or authority boundary changed.

## Global validation carrier

`.github/workflows/validate.yml` and its exact iOS mirror remain deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit refusal of GitHub/provider/Master-Records/HIL/public-provider credential-shaped environment values, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current_on_main: 14
workflow_files_removed_or_consolidated_released: 35
classified_and_remediated_released: 38/49 = 77.55%
remaining_unclassified_or_unconsolidated_released: 11/49
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
Ecosystem Chat runtime binding: StegVerse-org/LLM-adapter#18
VACC sovereign execution continuation: StegVerse-org/LLM-adapter#142 + tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
VA custody: master-records/orchestration#15
VA Site projection/privacy: StegVerse-Labs/Site#113/#116
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

## Collision boundaries

- Do not recreate sovereign local-model/runtime source work.
- Do not reactivate GitHub Models/GITHUB_TOKEN VACC inference.
- Do not alter TV/TVC service-return bundle or ledger semantics.
- Do not restore hosted schedules, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Next safe task

Under a fresh noncolliding claim, read the applicable specialized handoff and classify the next remaining default-branch workflow surface against canonical StegVerse owners and the `<=2` target. Prefer pure deterministic validation surfaces before workflows that perform publication, image creation, package publication, HIL lifecycle effects, or other stateful outputs.

## Archive condition

This support session remains active while workflow/token remediation is incomplete. Released main has 14 workflow files against the <=2 target and 11/49 audit-start surfaces remain unclassified/unconsolidated. The original local-model/runtime implementation is already complete/released and is not reopened by this maintenance lane.
