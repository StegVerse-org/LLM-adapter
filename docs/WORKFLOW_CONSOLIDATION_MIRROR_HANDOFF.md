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

## Released tranches 1-29

Latest release:

```text
29 PR #175
final head: b13aaf2c96a60053909d937c6e0365e8ee85dcd0
merge: 4d961856533d2e5cda79d093a2be0d943beaa7f1
Architecture Guard: 31990344714 SUCCESS
validate: 31990344530 SUCCESS
validate job: 95272608077 SUCCESS
67/67 substantive validation steps: SUCCESS
canonical Goal 4: SUCCESS
workflow parity: SUCCESS
claim 052: MERGED_INTO_CANONICAL_WORKSTREAM
post-merge workflow files: 7
classified/remediated: 45/49 = 91.84%
```

Tranche 29 removed the standalone `math-solver-governed-runtime.yml` GitHub-token/artifact surface and preserved its deterministic capability in `scripts/verify_math_solver_governed_runtime.py`, `tests/test_math_solver_gateway.py`, and canonical `scripts/verify_goal4_full.py`. Hosted validation does not prove sovereign carrier execution.

Live Math Solver continuation remains machine/Site owned:

```text
StegVerse-Labs/.github resident sovereign carrier
-> StegVerse-org/LLM-adapter#72 service gateway
-> StegVerse-org/LLM-adapter#132 Math Solver runtime
-> scripts/observe_math_solver_public_runtime.py
-> StegVerse-Labs/Site#240 activation consumer
-> StegVerse-Labs/StegCore#70 canonical runtime binding
```

## Global validation carrier

`.github/workflows/validate.yml` and its exact iOS mirror remain deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Current accounting — released work only

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 7
workflow_files_removed_or_consolidated_released: 42
classified_and_remediated_released: 45/49 = 91.84%
remaining_unclassified_or_unconsolidated_released: 4/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

Current default-branch workflow census:

```text
architecture-guard.yml
capability-runtime.yml
hil-deployment-profile.yml
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
Math Solver machine continuation: StegVerse-org/LLM-adapter#72/#132 + Site#240 + StegCore#70
Master Records: master-records/orchestration
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The original local-model/runtime discovery/launch/inference/proof and formal local-model development are complete/released and are not duplicated. Live activation remains machine-owned and requires direct runtime evidence.

## Remaining workflow disposition work

`capability-runtime.yml` remains a strong `KEEP_STANDALONE_EXCEPTION` candidate because it is credential-clean and uniquely validates Ubuntu, Windows and macOS portable capability/bootstrap/service/autostart behavior across Python 3.11/3.12.

Still requiring fresh bounded disposition:

```text
hil-deployment-profile.yml
publish-portable-node-image.yml
stegdeploy-image.yml
steggate-portable-consumer.yml
```

`architecture-guard.yml` and `validate.yml` remain core deterministic validation surfaces unless a verified combined replacement preserves all coverage.

Next safe bounded task: inspect `hil-deployment-profile.yml` against the canonical TVC HIL handoff and determine whether its deterministic compatibility checks can be folded into `validate.yml` while transferring all live HIL execution/observation to TVC/resident StegVerse workers. Do not duplicate TVC private-review ownership.

## Collision boundaries

- Do not create another Math Solver evaluator, provider route, or runtime carrier.
- Do not manufacture carrier/public activation evidence.
- Preserve canonical StegGate pre-execution/replay semantics.
- Do not restore hosted schedules, token-backed setup, repository writeback, artifact transport, or activation.
- Do not touch wallet signing, broadcast, settlement, or Master Record authorization.

## Archive condition

This support session remains active while remaining workflow/token remediation is incomplete. Released main has 7 workflow files against the <=2 preference and 4/49 audit-start surfaces remain unclassified/unconsolidated.
