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

## Completed tranches 1-16

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
```

Claims 025-039 are released.

### Tranche 12 — global validation authority cleanup

Global `.github/workflows/validate.yml` and its iOS mirror are credential-clean deterministic validation only: `permissions: {}`, anonymous exact-SHA acquisition, credential refusal, no schedule, no checkout/setup/upload action, no hosted activation probe, no repository writeback, no GitHub-token runtime authority.

### Tranches 13-15 — validation consolidation

Provider-owned usage validation, Ecosystem Chat zero-external-dependency sovereignty validation, and the outcome-level objective contract were consolidated into global validate. Final tranche-15 Architecture Guard `31965418939` and validate `31965418919` succeeded with all 61 substantive checks successful.

### Tranche 16 — Chat LLM profile validation consolidated

PR #162 merged at `c921766daefbb14c48502e51c324883510c004a5`; final head `97a046409631d5f2daf4257f7979899d849df105`.

The standalone `.github/workflows/validate-chat-llm-profiles.yml` was removed. Its continuing deterministic checks now run from the stable credential-clean global dispatcher and exact iOS mirror:

```text
$PYTHON_BIN -m pytest tests/test_chat_llm_profiles.py -q
$PYTHON_BIN scripts/verify_chat_llm_profiles.py --write-receipt
```

`docs/CHAT_LLM_PROFILES_MIRROR_HANDOFF.md` preserves the historical Python 3.9/3.11/3.12 release matrix, original artifact evidence, and retained canonical receipt. Current validation accurately claims only the dispatcher Python 3.11 lane. Generated validation receipt data remains workspace-local; no GitHub artifact transport or repository writeback is used.

Exact final-head evidence:

```text
Architecture Guard 31965758047 SUCCESS
validate 31965758039 SUCCESS
Test Chat LLM profile policy layer SUCCESS
Build deterministic Chat LLM profile validation receipt SUCCESS
workflow parity SUCCESS
Confirm validation-only authority boundary SUCCESS
all 63 substantive validate steps SUCCESS
PR #162 merge c921766daefbb14c48502e51c324883510c004a5
```

Claim `tasks/LLMA-WORKFLOW-CONSOLIDATE-CHAT-PROFILES-039.json` is released as `MERGED_INTO_CANONICAL_WORKSTREAM`.

## Current accounting

```text
workflow_files_baseline: 49
workflow_files_current_on_main: 21
workflow_files_removed_or_consolidated: 28
classified_and_remediated: 31/49 = 63.27%
remaining_unclassified_or_unconsolidated: 18/49
restoration_target: <=2 unless evidence-backed standalone technical necessity exists
current_active_tranche_claim: NONE
```

Four GitHub Actions registry-only historical paths remain absent from main: `internal-governed-reference.yml`, `stack-conformance.yml`, `portable-node-process-restart-proof.yml`, and `authorized-provider-execution-boundary.yml`; they are not current workflow files.

## Canonical ownership / convergence

```text
organization authority: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
sovereign local model/runtime: StegVerse-002/micro-node-runtime/docs/SOVEREIGN_LOCAL_MODEL_RUNTIME_MIRROR_HANDOFF.md
formal local model development: COMPLETE_RELEASED
local runtime discovery/launch/inference/proof: COMPLETE_RELEASED
live local-model activation: StegVerse-Labs/.github#60 + resident sovereign heartbeat
credential/route authority: TV/TVC / StegVerse-Labs/TVC
HIL runtime/lifecycle: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
Ecosystem Chat runtime binding: StegVerse-org/LLM-adapter#18
VA Claims Chat runtime binding: StegVerse-org/LLM-adapter#90
StegFin: StegVerse-Labs/stegfin-governance/docs/STEGFIN_MIRROR_HANDOFF.md + TV/TVC + USER_ONLY signing/broadcast
```

The released local-model/runtime implementation is not duplicated in this workflow lane.

## Collision boundaries

- Do not recreate sovereign runtime source work.
- Do not compete with resident heartbeat, TVC route authority, or live-provider owners.
- Do not infer activation from workflow cleanup.
- Do not create non-TV/TVC runtime/test tokens.
- Preserve retained release receipts and historical compatibility evidence.
- Do not restore hosted activation, artifact transport, or repository writeback.
- Do not touch wallet/trade signing, broadcast, settlement, or StegFin provider execution.

## Next safe task

Under a fresh noncolliding claim, read the applicable specialized handoff and classify the next remaining default-branch workflow file against canonical StegVerse owners and the `<=2` target. Reusable `workflow_call`, publication, HIL, and VACC surfaces require their specific ownership/permission semantics to be checked before consolidation.

## Archive condition

This session remains a distinct support lane while workflow/token remediation remains incomplete. Twenty-one actual workflow files remain on main versus the adopted <=2 target, and 18/49 canonical audit-start surfaces remain unclassified/unconsolidated. No archive claim is permitted until all session-specific requirements are complete, superseded, or durably transferred and no distinct support role remains.
