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

## Released tranches 1-24

Latest releases:

```text
23 PR #169
final head: 3c28f830d1b4384f3371a670a68d92b65caa33af
merge: 567aaeeae149f43c3ca4fc9ab973b5b08d195e55
Architecture Guard: 31980391501 SUCCESS
validate: 31980391463 SUCCESS
validate job: 95246068046 SUCCESS
67/67 substantive validation steps: SUCCESS
claim 046: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 14
classified/remediated: 38/49 = 77.55%

24 PR #170
final head: 2cfc47455737278607ae7588ce53ce7fff39fcdd
merge: d32b97517cad5933f26639a63156b928559661b2
Architecture Guard: 31986711716 SUCCESS
validate: 31986711718 SUCCESS
validate job: 95262878966 SUCCESS
67/67 substantive validation steps: SUCCESS
workflow parity: SUCCESS
canonical Goal 4: SUCCESS
validation-only authority boundary: SUCCESS
claim 047: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 12
classified/remediated: 40/49 = 81.63%
```

Tranche 24 retired the complete superseded GitHub-hosted VACC preflight validation/proof family. The first bounded deletion caused `VA Provider Preflight Ubuntu 22.04 Proof` run `31986578857`, job `95262528654`, to fail closed because it still called the removed hosted validator. Direct logs exposed that coupled proof surface still received GitHub token read authority, used token-backed `actions/checkout@v4` and `actions/setup-python@v5`, sourced `secrets.STEGVERSE_MASTER_RECORDS_TOKEN`, and used `actions/upload-artifact@v4`. That evidence caused the claim to expand rather than hiding the coupling.

The released retirement removed:

```text
.github/workflows/validate-va-provider-preflight-hosted-path.yml
.github/workflows/va-provider-preflight-ubuntu2204-proof.yml
scripts/check_va_provider_preflight_hosted_path.py
```

Historical PR #120/run evidence remains preserved in `docs/VA_CLAIM_ASSISTANT_PROVIDER_PREFLIGHT_MIRROR_HANDOFF.md`. Current VACC continuation remains issue #142 + `tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json` under resident sovereign heartbeat -> TVC -> LLM-adapter -> Master Records with TV/TVC credential authority, credential requirement NONE, GitHub token requirement false, GitHub-token runtime authority NONE, third-party inference false, and hosted fallback DISALLOWED. No current sovereign activation predicate was removed and no replacement hosted workflow was created.

## Global validation carrier

`.github/workflows/validate.yml` and its exact iOS mirror remain deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current_on_main: 12
workflow_files_removed_or_consolidated_released: 37
classified_and_remediated_released: 40/49 = 81.63%
remaining_unclassified_or_unconsolidated_released: 9/49
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
va-claims-chat-runtime-contract.yml
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
VACC sovereign execution continuation: StegVerse-org/LLM-adapter#142 + tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
VA custody: master-records/orchestration#15
VA Site projection/privacy: StegVerse-Labs/Site#113/#116
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The original local-model/runtime implementation is complete/released and is not reopened by this workflow-maintenance lane.

## Collision boundaries

- Do not recreate sovereign local-model/runtime source work.
- Do not reactivate GitHub Models/GITHUB_TOKEN VACC inference.
- Preserve historical provenance while retiring obsolete execution surfaces.
- Do not restore hosted schedules, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Next safe task

Under a fresh noncolliding claim, read the applicable specialized handoff and classify the next remaining default-branch workflow surface against canonical StegVerse owners and the `<=2` target. Prefer deterministic validation/contract surfaces before publication, package/image creation, HIL lifecycle, or other stateful outputs.

## Archive condition

This support session remains active while workflow/token remediation is incomplete. Released main has 12 workflow files against the <=2 target and 9/49 audit-start surfaces remain unclassified/unconsolidated. The original local-model/runtime implementation is already complete/released and live activation remains machine-owned.
