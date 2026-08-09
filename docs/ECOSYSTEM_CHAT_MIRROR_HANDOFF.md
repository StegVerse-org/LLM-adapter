# Ecosystem Chat Runtime Mirror Handoff

## Active goal and claim

- Goal ID: `ECOSYSTEM-CHAT-ACTIVATION`
- Originating session goal: complete the governed Ecosystem Chat vertical slice and prevent unresolved work from being classified as unspecified external tasks.
- Repository: `StegVerse-org/LLM-adapter`
- Branch: `main`
- Canonical runtime owner: `StegVerse-org/LLM-adapter#18`
- Repository-local implementation claim: `COMPLETE` for the installed adapter/runtime, verification, stable status, immutable VERIFIED-receipt publication path, downstream automation wiring, and bounded run-scoped Master-Records custody binding.
- Active execution state: `MACHINE_OWNED` and `BLOCKED` at the real-provider execution-authority boundary; the bounded GitHub Models path no longer requires pre-provisioned Master-Records endpoint/token/allowlist configuration.
- Released validation claim: `LLMA-PROVIDER-READINESS-CHURN-018`.
- Completed scoped implementation claim: `LLMA-RUNSCOPED-CUSTODY-BINDING-018`.
- Claim release condition met: run-scoped custody workflow, regression guard, and canonical image-build repair are committed on `main`, image publication run `31290173179` passed, and the resulting publication receipt is `PUBLISHED` with a sha256 digest and fresh consumer pull verification.
- Remaining activation release condition: a valid unexpired provider-execution approval receipt triggers one real governed provider execution; the same execution must prove provider usage persistence, authenticated provider-usage and transition custody/reconstruction, immutable zero-blocker activation, Site activation, and downstream verified ingestion.
- Sovereign completion remains owned by `StegVerse-002/micro-node-runtime#16` and certificate control by `StegVerse-002/StegGuardian#4`.

## Authoritative surfaces

- Repository-wide handoff: `LLM_ADAPTER_MIRROR_HANDOFF.md`
- Runtime: `llm_adapter/deployed_gateway.py`
- Bootstrap/verifier: `scripts/stegdeploy_bootstrap.py`
- Live verifier: `scripts/verify_live_ecosystem_chat_activation.py`
- Authorized execution verifier: `scripts/verify_authorized_provider_activation.py`
- Stable status writer: `scripts/write_live_activation_status.py`
- Live activation workflow: `.github/workflows/ecosystem-chat-live-activation.yml`
- Bounded real-provider workflow: `.github/workflows/ecosystem-chat-github-models-execution.yml`
- Validation workflow: `.github/workflows/validate.yml`
- iOS workflow mirror: `iosnoperiod/github/workflows/validate.yml`
- Canonical image publication: `.github/workflows/stegdeploy-image.yml`
- Image build: `Dockerfile`
- Publication receipt: `receipts/stegdeploy-image-publication.json`
- Provider authority request: `authority/provider-execution-authority.github-models.request.json`
- Provider authority binding status: `status/stegverse-live-baseline-provider-authority-binding.json`
- Required provider approval destination: `receipts/provider-execution-authority.github-models.v1.json`
- Run-scoped custody source: `master-records/orchestration/services/master_records_custody_api.py`
- Regression guard: `tests/test_live_activation_automation_contract.py`
- Deployment contracts: `render.yaml`, `render-production.yaml`
- Public endpoint: `https://stegverse-ecosystem-chat-gateway.onrender.com`
- Hosting/task issue: `StegVerse-org/LLM-adapter#18`
- Site consumer handoff: `StegVerse-Labs/Site/docs/ECOSYSTEM_CHAT_ACTIVATION_MIRROR_HANDOFF.md`

## Current proven state

- Canonical StegDeploy image publication is restored to `PUBLISHED` after a real hosted build regression was found and repaired. Current receipt: image `ghcr.io/stegverse-org/llm-adapter:main`, digest `sha256:c5281db3a6dcbebda0b20038c45b822ecbe928661d035b08f7511c25b81aa707`, publication run `31290173179`, successful registry login/build/attestation/fresh pull, `consumer_pull_verified=true`, blockers `[]`.
- The preceding publication run `31290093567` correctly failed closed because `python:3.12-slim` lacked `git` while `.[service]` now installs pinned StegCore from Git. Commit `c439e67da829f6cb028019c0b0b007fb53ef8806` installs the required VCS client before service dependency installation; run `31290173179` directly proves the repair.
- Bounded GitHub Models execution now checks out canonical `master-records/orchestration`, generates masked run-scoped custody authentication/signing material, starts `services.master_records_custody_api:app` on loopback, verifies custody health, and only then consumes provider authority. This was installed at commit `adede2414a286a3b74169d91115f76f443d26972`.
- Regression coverage for that custody-before-authority ordering and removal of repository-level Master-Records secret/variable dependencies is committed at `58f5514d979d554a878644b571a7708dedb5e3d2`.
- The live gateway health path is reachable; live observation remains fail-closed rather than implying activation.
- The current retained generic authorized-provider projection may still show `CONFIGURATION_REQUIRED` for long-lived deployment bindings. That does not reopen the bounded GitHub Models custody implementation; the bounded execution workflow supplies canonical run-scoped custody internally.
- Real provider execution is still not confirmed because `receipts/provider-execution-authority.github-models.v1.json` has not been observed. The authority request exists, but approval/dispatch/provider-execution authority remains false until a valid approval receipt exists.
- The current stable live-activation state remains `PENDING`; no immutable `receipts/ecosystem-chat-live-activation.verified.json` is claimed, Site is not claimed `ACTIVATION_COMPLETE`, and downstream production ingestion is not claimed verified.

## Current task inventory

### EC-001 — Repository implementation
- Owner: `StegVerse-org/LLM-adapter`.
- State: `COMPLETE`.
- Validation: hosted validation evidence exists; current implementation remains on `main`.
- Integration: runtime/validation/activation automation installed.
- Next action: none; do not reopen design work from missing runtime evidence alone.

### EC-002 — Provider-readiness/deployment-churn stabilization
- Claim: `LLMA-PROVIDER-READINESS-CHURN-018`.
- State: `COMPLETE`; claim `RELEASED`.
- Collision boundary: do not create another provider-readiness observer or heartbeat repository writer.

### EC-002A — Run-scoped Master-Records custody binding and image regression repair
- Claim: `LLMA-RUNSCOPED-CUSTODY-BINDING-018`.
- Origin: continuation of EC-003 without synthesizing provider authority.
- State: `COMPLETE`; claim `RELEASED`.
- Files: `.github/workflows/ecosystem-chat-github-models-execution.yml`, `tests/test_live_activation_automation_contract.py`, `Dockerfile`.
- Commits: `adede2414a286a3b74169d91115f76f443d26972`, `58f5514d979d554a878644b571a7708dedb5e3d2`, `c439e67da829f6cb028019c0b0b007fb53ef8806`.
- Strongest direct evidence: StegDeploy image run `31290173179` completed success through build, attestation, fresh pull, receipt retention, and enforcement; publication receipt is PUBLISHED at sha256 digest `c5281db3a6dcbebda0b20038c45b822ecbe928661d035b08f7511c25b81aa707`.
- Collision boundary: do not recreate custody service logic inside LLM-adapter; reuse `master-records/orchestration` as the canonical custody implementation.

### EC-003 — Authorized real-provider execution
- Owner: issue `StegVerse-org/LLM-adapter#18` plus existing provider authority surfaces.
- State: `BLOCKED` / `MACHINE_OWNED` at authority, not at bounded custody configuration.
- Exact locations: `authority/provider-execution-authority.github-models.request.json`, `status/stegverse-live-baseline-provider-authority-binding.json`, required approval `receipts/provider-execution-authority.github-models.v1.json`, execution `.github/workflows/ecosystem-chat-github-models-execution.yml`.
- Current authority state: request exists; valid approval receipt not observed; dispatch/provider execution authorization false.
- Machine-observable release condition: a valid unexpired approval receipt matching the exact GitHub Models provider contract is committed and has not already been consumed. The existing workflow then validates authority, starts owned run-scoped custody, consumes authority, and executes exactly one governed request.
- Prohibited action: do not synthesize provider/model permission, cost authority, approval, or custody authority.

### EC-004 — Real governed provider execution and immutable activation receipt
- Owner: adapter repository automation after EC-003 releases.
- State: `BLOCKED`.
- Required output: `receipts/ecosystem-chat-live-activation.verified.json` with schema `stegverse.ecosystem_chat.live_activation.v1`, `state=VERIFIED`, `blockers=[]`, valid result hash, and all authority flags false.
- Required evidence from the same execution: provider used, durable usage persisted, provider-usage custody RECORDED, provider-usage reconstructability PASS, transition custody RECORDED, transition reconstructability PASS.

### EC-005 — Site import and activation
- Owner: `StegVerse-Labs/Site`.
- State: `MACHINE_OWNED`, awaiting EC-004.
- Locations: `scripts/acquire_ecosystem_chat_live_activation_receipt.py`, `scripts/update_ecosystem_chat_activation_state.py`, `data/ecosystem-chat-activation-state.json`.
- Release condition: valid immutable VERIFIED receipt accepted and Site state becomes `ACTIVATION_COMPLETE`.

### EC-006 — Downstream propagation
- Owners/destinations: `GCAT-BCAT-Engine/Publisher`, `StegVerse-Labs/admissibility-wiki`, `StegVerse-002/stegguardian-wiki`.
- State: `MACHINE_OWNED`, awaiting Site activation packet.
- Source packet: `StegVerse-Labs/Site/data/ecosystem-chat-activation-propagation.json`.
- Release condition: each canonical consumer records verified ingestion of the Site activation projection.

### EC-007 — Sovereign completion
- Owners: `StegVerse-002/micro-node-runtime#16` and `StegVerse-002/StegGuardian#4`.
- State: `MERGED_INTO_CANONICAL_WORKSTREAM`.
- Requirement: `ZERO_EXTERNAL_PLATFORM_DEPENDENCIES`, including workload migration and `RETIRED_VERIFIED` evidence for temporary external control planes plus protected certificate/root-key custody evidence.

## Automation and fail-closed continuation

- `.github/workflows/validate.yml` validates current `main` on repository events and schedule.
- `.github/workflows/ecosystem-chat-live-activation.yml` runs every 15 minutes and after successful validation; it writes stable semantic status only when semantics change, retains volatile observations as artifacts, and creates the immutable VERIFIED receipt only after all gates pass.
- `.github/workflows/ecosystem-chat-live-activation-monitor.yml` retains volatile heartbeat evidence as artifacts only, preventing observation traffic from creating deployment churn.
- `.github/workflows/ecosystem-chat-github-models-execution.yml` is event-driven by the provider approval receipt and is single-use-authority guarded. It now owns the bounded custody startup/preflight so no manual Master-Records secret copying is required for that execution lane.
- Missing provider authority remains fail-closed and is never converted into success.

## Validation commands and evidence

- Image publication: `.github/workflows/stegdeploy-image.yml`, run `31290173179` SUCCESS after Docker repair; digest and pull verification retained in `receipts/stegdeploy-image-publication.json`.
- Repository validation: `.github/workflows/validate.yml`; concurrent validation runs that began while the preceding blocked image receipt was still current correctly failed at image-receipt retention and therefore do not prove the new custody contract. A fresh validation on current main must pass before the scoped validation role is considered fully closed.
- Live activation: `.github/workflows/ecosystem-chat-live-activation.yml` and `reports/ecosystem-chat-live-activation-status.json`.
- Current provider authority: `status/stegverse-live-baseline-provider-authority-binding.json` plus the presence/absence and validity of `receipts/provider-execution-authority.github-models.v1.json`.
- Cross-repository acceptance after VERIFIED: Site acquisition/activation-state validators, followed by Publisher/wiki consumers.

## Session consolidation

- MERGED INTO: `StegVerse-org/LLM-adapter#18` and this handoff.
- Repository-wide source of truth: `StegVerse-org/LLM-adapter/LLM_ADAPTER_MIRROR_HANDOFF.md`.
- Coordination registry: `StegVerse-Labs/StegAgents/coordination/internal_tasks.json`.
- Site continuation: `StegVerse-Labs/Site/docs/ECOSYSTEM_CHAT_ACTIVATION_MIRROR_HANDOFF.md`.
- Custody continuation: `master-records/orchestration/docs/ECOSYSTEM_CHAT_CUSTODY_MIRROR_HANDOFF.md`.
- Sovereign continuation: `StegVerse-002/micro-node-runtime#16`; certificate control: `StegVerse-002/StegGuardian#4`.
- All new implementation knowledge from this session is transferred here; the only current session-local role is distinct validation observation of a fresh current-main run after the image receipt repair.

## Completion accounting

Current activation inventory denominator: 7 task groups (`EC-001` through `EC-007`); EC-002A is a completed subtask and does not inflate the denominator.

- Task completion: 2/7 top-level activation groups complete; EC-002A is additionally complete and released; EC-003 through EC-006 remain blocked/machine-owned and EC-007 is merged to canonical sovereign owners.
- Developed files: 10/10 current repository-local activation/control deliverables developed (the prior 7 plus bounded provider workflow, custody regression guard, and canonical image-build dependency repair); scaffolding/stubs counted as complete: 0.
- Validation: 6/7 activation requirements proven; final zero-blocker live activation remains unproven. Scoped custody implementation awaits one fresh current-main validation run because concurrent validation observed the preceding blocked image receipt.
- Integration: 4/6 implementation/integration surfaces installed (runtime, observer/automation, bounded owned custody binding, image publication); real provider/custody execution evidence, Site completion, and downstream verified ingestion remain activation gates.
- Propagation: 0/3 final production propagation destinations verified from an immutable activation packet.
- Goal activation: 70% for live Ecosystem Chat activation. This increase reflects removal of the bounded Master-Records configuration dependency and restoration of canonical image publication, not real-provider activation.
- Session consolidation: 7/7 session goal groups durably represented; final archival decision additionally depends on fresh validation of the new scoped changes.

## Archive condition

Do not archive this originating conversation while the fresh current-main validation for `LLMA-RUNSCOPED-CUSTODY-BINDING-018` is still unobserved. Once that validation passes or an exact new blocker is durably transferred, this session has no unique implementation role: provider authority/execution remains machine-owned by issue #18, Site/downstream remain machine-owned by their consumers, and sovereign migration remains merged to its canonical owners. Product activation and session archival remain distinct states.
