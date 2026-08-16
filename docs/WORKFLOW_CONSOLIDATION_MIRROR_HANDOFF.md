# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: chore/consolidate-public-knowledge-vacc-validation-20260816
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: LLMA-WORKFLOW-CONSOLIDATE-PUBLIC-KNOWLEDGE-VACC-041
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

## Retired hosted continuity provenance

```text
ecosystem-chat-live-activation.yml: RETIRED — resident StegVerse carrier + TV/TVC owns live activation
ecosystem-chat-live-activation-monitor.yml: RETIRED — resident carrier owns continuity
platform-agnostic-runtime.yml: RETIRED/TRANSFERRED — sovereign runtime proof belongs to StegVerse runtime owners
hil-process-restart-controlled-cycle.yml: RETIRED/TRANSFERRED_TO_TVC
legacy third-party deployment manifests: RETIRED_AS_PRODUCTION_DEPENDENCY
```

## Completed tranches 1-17

```text
1 #145 c9f561254ec5671c2329c3deb7ce0bfb511331ab
2 transfer b5ec49b78c58c0cf9592b19b2e1b02825c96ec3f
3 #149 0bd06fcdda1ba7fe736fde1d131b702e57080e3a
4 #150 ec16f9f681ebbac4b34e1e3af1607145153ff14c
5 #151 6b5db6e9415fc76da2979943ca6cb9281626ffdb
6 #152 91bb8578662fe2ef0e6276516efb98fce78827b0
7 #153 a314dbc3e82a0155b59067d59381995bb74b300f
8 #154 85fe10fe40da948596662daba16f13c7f3eb531c
9 #155 ec4d668038da9ad6a439007c71c9b2b2df091fbb
10 #156 837799aa5c4e6ee64ffc86902216eb36e53ebd36
11 #157 310f0225d3700fda735d3f2d70943a12e9bda0cc
12 #158 695ad0723d303b140c19c6c15abbb8f0653b05ee
13 #159 ee193f96c1d3b6fca2f0d1d009536fec83c6a884
14 #160 c7bb207042259b11060e8cf8d93019a7cff0ccbe
15 #161 c0ea3bd5c3c300cce3be7e8442f30def1c41b07b
16 #162 c921766daefbb14c48502e51c324883510c004a5
17 #163 1885754f60a1d08a8219e4244e383c3e4ceea0de
```

Claims 025-040 are released. The global dispatcher is credential-clean deterministic validation only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit credential refusal, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation, and no GitHub-token runtime/control-plane authority.

## Active tranche 18 — public-knowledge/VACC source validation consolidation

Claim: `tasks/LLMA-WORKFLOW-CONSOLIDATE-PUBLIC-KNOWLEDGE-VACC-041.json`.

Before mutation, both specialized handoffs were read. `docs/ECOSYSTEM_PUBLIC_KNOWLEDGE_MIRROR_HANDOFF.md` marks public-knowledge source implementation `COMPLETE_VALIDATED_SOURCE` with issue #140 as corpus-expansion owner. `docs/VACC_PUBLIC_INFORMATION_PROFILE_MIRROR_HANDOFF.md` marks the source profile `COMPLETE_VALIDATED_SOURCE_PROFILE`, preserves the claim-specific official-VA-only boundary, assigns issue #141 source-profile history, issue #90 runtime execution, and Site orchestration the canonical source registry/projection.

The standalone `.github/workflows/public-knowledge-vacc-source-validation.yml` was credential-free but still duplicated its own GitHub-hosted source acquisition and focused validation. Its unique deterministic capability is now installed in the stable global dispatcher and exact iOS mirror:

```text
compile:
  llm_adapter/public_knowledge.py
  llm_adapter/ai_entry_backend_service.py
  llm_adapter/vacc_public_information.py
  tests/test_public_knowledge.py
  tests/test_vacc_public_information.py
focused validation:
  $PYTHON_BIN -m unittest -q tests.test_public_knowledge tests.test_vacc_public_information
```

The global credential refusal now explicitly includes `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in addition to GitHub and StegVerse provider/Master-Records/HIL credential-shaped environment values. Both specialized handoffs preserve historical run `31875248198`, job `94989892925`, 11/11 focused tests, compile PASS, anonymous source acquisition, and `PUBLIC_KNOWLEDGE_VACC_SOURCE_VALIDATION_PASS`, while naming `.github/workflows/validate.yml` as current validation.

Disposition on the active branch:

```text
.github/workflows/public-knowledge-vacc-source-validation.yml
  -> CONSOLIDATE_INTO_STABLE_DISPATCHER
  -> removed
.github/workflows/validate.yml
  -> current deterministic source-policy validation
iosnoperiod/github/workflows/validate.yml
  -> exact mirror
```

No public-corpus authority, VACC route execution, provider execution, custody, Site mutation, filing, publication, activation, wallet effect, GitHub-token authority, or non-TV/TVC credential is added. Tranche 18 remains incomplete until exact final-head Architecture Guard and validate pass, the PR merges, claim 041 is released, and this handoff is finalized on main.

## Current accounting — released work only

```text
workflow_files_baseline: 49
workflow_files_current_on_released_main: 20
workflow_files_removed_or_consolidated: 29
classified_and_remediated: 32/49 = 65.31%
remaining_unclassified_or_unconsolidated: 17/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: LLMA-WORKFLOW-CONSOLIDATE-PUBLIC-KNOWLEDGE-VACC-041
```

If tranche 18 releases as installed and no concurrent workflow-file change occurs, main becomes 19 workflow files, 30 removed/consolidated, 33/49 = 67.35% classified/remediated, and 16/49 remaining.

## Canonical ownership / convergence

```text
organization authority: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
sovereign local model/runtime: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
formal local model development: COMPLETE_RELEASED
local runtime discovery/launch/inference/proof: COMPLETE_RELEASED
live local-model activation: StegVerse-Labs/.github#60 + resident sovereign heartbeat
credential/route authority: TV/TVC / StegVerse-Labs/TVC
Ecosystem Chat runtime binding: StegVerse-org/LLM-adapter#18
public corpus expansion: StegVerse-org/LLM-adapter#140
VACC source profile: StegVerse-org/LLM-adapter#141
VACC runtime: StegVerse-org/LLM-adapter#90
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

## Collision boundaries

- Do not recreate sovereign runtime source work.
- Do not weaken claim-specific official-VA-only grounding.
- Do not make VAwatchdog/private material public grounding without separately admitted sanitized projection.
- Do not infer runtime activation from source-policy validation.
- Do not create non-TV/TVC runtime/test tokens.
- Do not restore hosted activation, artifact transport, or repository writeback.
- Do not touch wallet/trade signing, broadcast, settlement, or StegFin provider execution.

## Next task after release

Under a fresh noncolliding claim, read the applicable specialized handoff and classify the next remaining default-branch workflow file against canonical StegVerse owners and the `<=2` target.

## Archive condition

This session remains a distinct support lane while workflow/token remediation remains incomplete. Released main has 20 workflow files versus the adopted <=2 target, 17/49 audit-start surfaces remain unclassified/unconsolidated, and claim 041 is active.
