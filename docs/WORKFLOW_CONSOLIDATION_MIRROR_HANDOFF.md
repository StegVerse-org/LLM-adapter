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

Historical workflow names remain only as proof that hosted activation/persistence stays retired.

## Released tranches 1-27

Latest release:

```text
27 PR #173
final head: e6f100b2dd4c3c024239a50248a71e379f42d5ce
merge: cf51da459b0317f12c58fa3c365630a104439706
Architecture Guard: 31989374647 SUCCESS
validate: 31989374615 SUCCESS
validate job: 95270003644 SUCCESS
67/67 substantive validation steps: SUCCESS
canonical Goal 4: SUCCESS including governed VACC classifier/generator/retrieval/dispatch, fail-closed service-connection observer, and extracted receipt validator
workflow parity: SUCCESS
capability-runtime: 31989374599 SUCCESS
claim 050: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 9
classified/remediated: 43/49 = 87.76%
```

Tranche 27 removed `.github/workflows/va-claim-assistant-governed-retrieval.yml`, retiring its six-hour schedule, `contents: write`, token-backed checkout/setup, receipt commit/pull/push writeback, and artifact upload. The deterministic capability is retained in canonical Goal 4 through the route classifier/generator/retrieval/dispatch fixtures, `scripts/observe_va_service_connection_execution.py`, and new `scripts/validate_va_claim_assistant_governed_retrieval_receipts.py`. Canonical StegCore is pinned in the dev dependency set for credential-clean validation. Live VACC execution/observation is transferred to resident sovereign heartbeat -> TVC -> issue #142/task `VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023` -> Master Records -> Site projection. Missing execution evidence remains `BLOCKED` and no execution evidence was manufactured.

## Global validation carrier

`.github/workflows/validate.yml` and its exact iOS mirror remain deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current_on_main: 9
workflow_files_removed_or_consolidated_released: 40
classified_and_remediated_released: 43/49 = 87.76%
remaining_unclassified_or_unconsolidated_released: 6/49
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
VA Site projection/privacy: StegVerse-Labs/Site#113/#116/#241
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The original local-model/runtime discovery/launch/inference/proof and formal local-model development are complete/released and are not duplicated by this maintenance lane. Live activation remains machine-owned and requires direct runtime evidence.

## Collision boundaries

- Do not recreate sovereign local-model/runtime source work.
- Do not manufacture VACC provider execution evidence.
- Preserve route, urgent-safety, privacy, filing, custody, veteran-authority, StegGate, and Master Records boundaries.
- Do not restore hosted schedules, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Next safe task

Under a fresh noncolliding claim, read the applicable specialized handoff and classify one of the remaining stateful surfaces: `capability-runtime.yml`, `hil-deployment-profile.yml`, `math-solver-governed-runtime.yml`, `steggate-portable-consumer.yml`, `publish-portable-node-image.yml`, `stegdeploy-image.yml`, or `llm-adapter-open-pr-consolidation.yml`. Preserve `architecture-guard.yml` and `validate.yml` unless evidence proves they can be combined without weakening deterministic validation.

## Archive condition

This support session remains active while workflow/token remediation is incomplete. Main has 9 workflow files against the <=2 target and 6/49 audit-start surfaces remain unclassified/unconsolidated. The original local-model/runtime implementation is already complete/released and live activation remains machine-owned.
