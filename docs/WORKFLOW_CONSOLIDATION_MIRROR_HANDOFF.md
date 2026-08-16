# Workflow Consolidation Mirror Handoff

## Active goal

```text
goal_id: LLM-ADAPTER-WORKFLOW-CONSOLIDATION-001
repository: StegVerse-org/LLM-adapter
branch: main
originating_goal: restore the StegVerse/Core-Lite dispatcher architecture, contain hosted Actions cost, remove third-party runtime dependence, and ensure no non-TV/TVC token becomes runtime/control-plane authority
active_claim: NONE
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

## Completed tranches 1-18

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
18 #164 2452d23531bafdbd9a20de0ba0dd28aa127991a4
```

Claims 025-041 are released.

## Global validation authority cleanup

`.github/workflows/validate.yml` and its exact iOS mirror are deterministic-validation-only: `permissions: {}`, anonymous exact-SHA source acquisition, explicit refusal of GitHub/provider/Master-Records/HIL and public-provider credential-shaped environment values, no checkout/setup/upload actions, no schedule, no repository writeback, no hosted activation probe, and no GitHub-token runtime/control-plane authority.

## Tranche 18 — public-knowledge/VACC source validation consolidated

PR #164 merged at `2452d23531bafdbd9a20de0ba0dd28aa127991a4`; final implementation head `e95786a8210ea8eb78666e6f545cb62a7a7c832e`.

The standalone `.github/workflows/public-knowledge-vacc-source-validation.yml` was removed. Its deterministic capability now runs from the shared credential-clean dispatcher and exact iOS mirror:

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

`docs/ECOSYSTEM_PUBLIC_KNOWLEDGE_MIRROR_HANDOFF.md` and `docs/VACC_PUBLIC_INFORMATION_PROFILE_MIRROR_HANDOFF.md` preserve historical run `31875248198`, job `94989892925`, 11/11 focused tests, anonymous exact-SHA acquisition, compile PASS, and the original `PUBLIC_KNOWLEDGE_VACC_SOURCE_VALIDATION_PASS` marker while naming `.github/workflows/validate.yml` as the current validation carrier.

The current global credential-refusal gate now explicitly includes `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in addition to GitHub and StegVerse credential-shaped values. This does not grant those providers authority; it prevents their credential-bearing environment values from entering deterministic source validation.

Exact final-head evidence:

```text
Architecture Guard 31974215930 SUCCESS
validate 31974215875 SUCCESS
Compile public-knowledge and VACC source surfaces SUCCESS
Validate public-knowledge and VACC source policy SUCCESS
workflow parity SUCCESS
Run canonical Goal 4 verification SUCCESS
Confirm validation-only authority boundary SUCCESS
all 67 substantive validate steps SUCCESS
PR #164 merge 2452d23531bafdbd9a20de0ba0dd28aa127991a4
```

Claim `tasks/LLMA-WORKFLOW-CONSOLIDATE-PUBLIC-KNOWLEDGE-VACC-041.json` is released as `MERGED_INTO_CANONICAL_WORKSTREAM`.

## Current accounting

The preceding released main contained 20 workflow files. PR #164 removed exactly one default-branch workflow file and added no workflow file. Therefore:

```text
workflow_files_baseline: 49
workflow_files_current_on_main: 19
workflow_files_removed_or_consolidated: 30
classified_and_remediated: 33/49 = 67.35%
remaining_unclassified_or_unconsolidated: 16/49
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

## Next safe task

Under a fresh noncolliding claim, read the applicable specialized handoff and classify the next remaining default-branch workflow file against canonical StegVerse owners and the `<=2` target. Reusable `workflow_call`, publication, HIL, VACC governed-runtime, image-publication, and portable-image surfaces require their specific ownership/permission semantics to be read before mutation.

## Archive condition

This session remains a distinct support lane while workflow/token remediation remains incomplete. Nineteen actual workflow files remain on main versus the adopted <=2 target, and 16/49 canonical audit-start surfaces remain unclassified/unconsolidated. No archive claim is permitted until all session-specific requirements are complete, superseded, or durably transferred and no distinct support role remains.
