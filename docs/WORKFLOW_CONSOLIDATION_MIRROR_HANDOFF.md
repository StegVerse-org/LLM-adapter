# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: chore/consolidate-va-governed-retrieval-20260816
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: LLMA-WORKFLOW-CONSOLIDATE-VA-GOVERNED-RETRIEVAL-050
active_claim_state: CLAIMED_FOR_IMPLEMENTATION
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

These historical workflow names remain in this handoff only so tests and future operators can verify that hosted activation/persistence remain retired; they are not runnable production surfaces.

## Released tranches 1-26

Latest release:

```text
26 PR #172
final head: def5bda508e34d364ed089599fe023d0f45163cf
merge: 99c2460d71fa421754f90c4d30503e2581631c6e
Architecture Guard: 31987457768 SUCCESS
validate: 31987457767 SUCCESS
validate job: 95264802323 SUCCESS
67/67 substantive validation steps: SUCCESS
canonical Goal 4: SUCCESS including privacy fixture + independent validator
workflow parity: SUCCESS
validation-only authority boundary: SUCCESS
claim 049: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 10
classified/remediated: 42/49 = 85.71%
```

## Active tranche 27 — governed VACC validation/observation consolidation

Claim: `tasks/LLMA-WORKFLOW-CONSOLIDATE-VA-GOVERNED-RETRIEVAL-050.json`.

The specialized handoff `docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md` was read before mutation. It shows the thirteen-route source implementation and canonical StegGate identity binding are released, while real provider execution remains blocked and belongs to the sovereign VACC execution path. The old standalone workflow still ran every six hours with `contents: write`, token-backed checkout/setup, receipt commit/pull/push writeback, and artifact upload. Those hosted lifecycle mechanics are not current provider authority.

Installed on the active branch:

```text
.github/workflows/va-claim-assistant-governed-retrieval.yml
  -> CONSOLIDATE_DETERMINISTIC_VALIDATION_INTO_CANONICAL_GOAL4_AND_TRANSFER_LIVE_OBSERVATION_TO_STEGVERSE_WORKER
  -> removed
scripts/verify_goal4_full.py
  -> executes route classifier fixture
  -> executes route generator fixture
  -> executes governed retrieval fixture
  -> executes governed dispatch fixture
  -> executes scripts/observe_va_service_connection_execution.py
  -> executes scripts/validate_va_claim_assistant_governed_retrieval_receipts.py
scripts/validate_va_claim_assistant_governed_retrieval_receipts.py
  -> new durable validator containing the former inline receipt/hash/runtime-identity/readiness assertions
pyproject.toml dev dependencies
  -> canonical StegCore pinned at 8c484e584d60a3bd2763d6948d0eb3f4afd67e0c so canonical Goal 4 can validate the identity without a credential-bearing setup path
```

The global `validate.yml` and exact iOS mirror remain `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, and no hosted activation. They already execute canonical Goal 4.

Live VACC observation/continuation is transferred to:

```text
StegVerse-Labs/.github resident sovereign heartbeat
-> StegVerse-Labs/TVC
-> StegVerse-org/LLM-adapter#142
-> tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
-> scripts/observe_va_service_connection_execution.py
-> master-records/orchestration#15
-> StegVerse-Labs/Site#113/#241 after immutable evidence
```

No provider execution evidence is manufactured by this cleanup. If the execution receipt is absent, the retained observer must continue to emit `BLOCKED`. No provider execution, custody, filing, Site mutation, wallet effect, GitHub/OIDC runtime authority, Render authority, repository writeback, artifact transport, or non-TV/TVC secret/token is introduced.

Tranche 27 remains incomplete until exact-head Architecture Guard/global validate pass, PR merge, post-merge workflow census, claim 050 release, and main handoff finalization.

## Global validation carrier

`.github/workflows/validate.yml` and its exact iOS mirror remain deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting — released work only

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 10
workflow_files_removed_or_consolidated_released: 39
classified_and_remediated_released: 42/49 = 85.71%
remaining_unclassified_or_unconsolidated_released: 7/49
expected_if_tranche_27_releases_without_concurrent_change: 9 workflow files, 40 removed/consolidated, 43/49 = 87.76%, 6/49 remaining
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: LLMA-WORKFLOW-CONSOLIDATE-VA-GOVERNED-RETRIEVAL-050
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
- Preserve all route, urgent-safety, privacy, filing, custody and veteran-authority boundaries.
- Do not restore hosted schedules, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Archive condition

This support session remains active while claim 050 and remaining workflow/token remediation are incomplete. Released main has 10 workflow files against the <=2 target and 7/49 audit-start surfaces remain unclassified/unconsolidated.
