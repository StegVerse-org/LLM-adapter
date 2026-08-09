# Ecosystem Chat Runtime Mirror Handoff

## Active goal and claim

- Goal ID: `ECOSYSTEM-CHAT-ACTIVATION`
- Originating session goal: complete the governed Ecosystem Chat vertical slice and prevent unresolved work from being classified as unspecified external tasks.
- Repository / branch: `StegVerse-org/LLM-adapter` / `main`.
- Canonical runtime owner: `StegVerse-org/LLM-adapter#18`.
- Repository-local implementation: `COMPLETE` for adapter/runtime, verification, stable status, immutable VERIFIED-receipt publication path, downstream wiring, and bounded run-scoped Master-Records custody binding.
- Active execution state: `MACHINE_OWNED` + `BLOCKED` at real-provider execution authority. The bounded GitHub Models lane no longer needs pre-provisioned Master-Records endpoint/token/allowlist configuration.
- `LLMA-PROVIDER-READINESS-CHURN-018`: `COMPLETE / RELEASED`.
- `LLMA-RUNSCOPED-CUSTODY-BINDING-018`: `COMPLETE / VALIDATED / RELEASED`.
- Remaining release condition: a valid unexpired provider-execution approval receipt triggers one real governed provider execution; the same execution must prove provider usage persistence, authenticated provider-usage and transition custody/reconstruction, immutable zero-blocker activation, Site activation, and downstream verified ingestion.
- Sovereign completion owner: `StegVerse-002/micro-node-runtime#16`; certificate control: `StegVerse-002/StegGuardian#4`.

## Authoritative surfaces

- Repository-wide handoff: `LLM_ADAPTER_MIRROR_HANDOFF.md`
- Runtime: `llm_adapter/deployed_gateway.py`
- Live verifier: `scripts/verify_live_ecosystem_chat_activation.py`
- Authorized execution verifier: `scripts/verify_authorized_provider_activation.py`
- Live workflow: `.github/workflows/ecosystem-chat-live-activation.yml`
- Bounded provider workflow: `.github/workflows/ecosystem-chat-github-models-execution.yml`
- Validation: `.github/workflows/validate.yml`
- Canonical image publication: `.github/workflows/stegdeploy-image.yml`
- Image build: `Dockerfile`
- Publication receipt: `receipts/stegdeploy-image-publication.json`
- Provider request: `authority/provider-execution-authority.github-models.request.json`
- Provider binding status: `status/stegverse-live-baseline-provider-authority-binding.json`
- Required approval destination: `receipts/provider-execution-authority.github-models.v1.json`
- Canonical custody implementation: `master-records/orchestration/services/master_records_custody_api.py`
- Regression guard: `tests/test_live_activation_automation_contract.py`
- Deployment contracts: `render.yaml`, `render-production.yaml`
- Site continuation: `StegVerse-Labs/Site/docs/ECOSYSTEM_CHAT_ACTIVATION_MIRROR_HANDOFF.md`

## Current proven state

- Canonical image publication is `PUBLISHED`: run `31290173179`, digest `sha256:c5281db3a6dcbebda0b20038c45b822ecbe928661d035b08f7511c25b81aa707`, build/attestation/fresh pull all successful, `consumer_pull_verified=true`, blockers `[]`.
- The immediately preceding publication run `31290093567` failed closed because the slim image lacked `git` while the service install now pulls pinned StegCore through a Git URL. Commit `c439e67da829f6cb028019c0b0b007fb53ef8806` installs the required VCS client; run `31290173179` proves the repair.
- Bounded GitHub Models execution now checks out `master-records/orchestration`, creates masked run-scoped custody auth/signing material, starts the canonical custody API on loopback, verifies custody health, and only then consumes provider authority. Installed by `adede2414a286a3b74169d91115f76f443d26972`.
- Regression coverage for custody-before-authority ordering and removal of repository-level Master-Records secret/variable dependencies was installed by `58f5514d979d554a878644b571a7708dedb5e3d2`.
- Fresh hosted validation run `31290296565` completed `SUCCESS` after the publication repair. Every validation/test/gate step completed successfully, including `Test Master-Records provider usage custody submission`, `Test live activation automation contract`, immutable receipt checks, deployed probe, workflow parity, authority/receipt/provider-capture/recovery checks, canonical Goal 4 verification, and destination activation-state persistence.
- The provider approval receipt `receipts/provider-execution-authority.github-models.v1.json` is still absent. Therefore no provider execution authority is claimed or synthesized.
- Live activation remains `PENDING`; no immutable `receipts/ecosystem-chat-live-activation.verified.json`, Site `ACTIVATION_COMPLETE`, or downstream verified production ingestion is claimed.

## Execution inventory

### EC-001 — Repository implementation
- Owner: `StegVerse-org/LLM-adapter`.
- State: `COMPLETE / VALIDATED`.
- Next action: none; missing runtime authority evidence does not reopen design work.

### EC-002 — Provider-readiness/deployment-churn stabilization
- Owner/claim: `LLMA-PROVIDER-READINESS-CHURN-018`.
- State: `COMPLETE / RELEASED`.
- Collision boundary: do not create another heartbeat/provider-readiness repository writer.

### EC-002A — Run-scoped custody + image regression repair
- Owner/claim: `LLMA-RUNSCOPED-CUSTODY-BINDING-018`.
- State: `COMPLETE / VALIDATED / RELEASED`.
- Files: `.github/workflows/ecosystem-chat-github-models-execution.yml`, `tests/test_live_activation_automation_contract.py`, `Dockerfile`.
- Evidence: commits `adede2414a286a3b74169d91115f76f443d26972`, `58f5514d979d554a878644b571a7708dedb5e3d2`, `c439e67da829f6cb028019c0b0b007fb53ef8806`; image run `31290173179` success; hosted validation `31290296565` success.
- Collision boundary: reuse `master-records/orchestration`; do not duplicate custody authority in LLM-adapter.

### EC-003 — Authorized real-provider execution
- Owner: `StegVerse-org/LLM-adapter#18` + existing authority surfaces.
- State: `BLOCKED / MACHINE_OWNED` at provider authority.
- Required approval: `receipts/provider-execution-authority.github-models.v1.json`.
- Release condition: valid, unexpired, exact-contract approval receipt exists and is unconsumed. Existing workflow then validates it, starts run-scoped custody, consumes authority, and performs exactly one governed request.
- Prohibited: synthesizing provider/model permission, paid-resource/cost authority, approval, or custody authority.

### EC-004 — Real provider execution + immutable activation
- Owner: adapter automation after EC-003.
- State: `BLOCKED`.
- Output: `receipts/ecosystem-chat-live-activation.verified.json` with `state=VERIFIED`, `blockers=[]`, valid hash, authority flags false.
- Same-execution evidence required: provider used; durable usage; provider-usage custody RECORDED + reconstruction PASS; transition custody RECORDED + reconstruction PASS.

### EC-005 — Site activation
- Owner: `StegVerse-Labs/Site`.
- State: `MACHINE_OWNED`, awaiting EC-004.
- Locations: `scripts/acquire_ecosystem_chat_live_activation_receipt.py`, `scripts/update_ecosystem_chat_activation_state.py`, `data/ecosystem-chat-activation-state.json`.
- Release: valid VERIFIED receipt accepted and state becomes `ACTIVATION_COMPLETE`.

### EC-006 — Downstream propagation
- Owners: `GCAT-BCAT-Engine/Publisher`, `StegVerse-Labs/admissibility-wiki`, `StegVerse-002/stegguardian-wiki`.
- State: `MACHINE_OWNED`, awaiting Site packet.
- Source: `StegVerse-Labs/Site/data/ecosystem-chat-activation-propagation.json`.
- Release: each consumer records verified ingestion.

### EC-007 — Sovereign completion
- Owners: `StegVerse-002/micro-node-runtime#16`, `StegVerse-002/StegGuardian#4`.
- State: `MERGED_INTO_CANONICAL_WORKSTREAM`.
- Requirement: `ZERO_EXTERNAL_PLATFORM_DEPENDENCIES` plus `RETIRED_VERIFIED` temporary-control-plane evidence and protected certificate/root-key custody evidence.

## Automation, validation, and authority boundaries

- `validate.yml` validates current implementation on repository events/schedule.
- `ecosystem-chat-live-activation.yml` observes every 15 minutes and after successful validation; it fails closed and creates the immutable VERIFIED receipt only when all gates pass.
- `ecosystem-chat-live-activation-monitor.yml` retains volatile heartbeat evidence as artifacts only.
- `ecosystem-chat-github-models-execution.yml` is triggered by the approval receipt, is single-use guarded, and now starts/preflights canonical run-scoped custody before consuming authority.
- Missing provider authority is an explicit blocked state, never success.
- Provider output != authority; custody != execution authority; workflow success != live activation; image publication != provider authorization.

## Session consolidation

- MERGED INTO: `StegVerse-org/LLM-adapter#18` and this handoff.
- Repository-wide source: `StegVerse-org/LLM-adapter/LLM_ADAPTER_MIRROR_HANDOFF.md`.
- Coordination registry: `StegVerse-Labs/StegAgents/coordination/internal_tasks.json`.
- Custody continuation: `master-records/orchestration/docs/ECOSYSTEM_CHAT_CUSTODY_MIRROR_HANDOFF.md`.
- Site continuation: `StegVerse-Labs/Site/docs/ECOSYSTEM_CHAT_ACTIVATION_MIRROR_HANDOFF.md`.
- Sovereign continuation: `StegVerse-002/micro-node-runtime#16`; certificate control: `StegVerse-002/StegGuardian#4`.
- All implementation and validation knowledge added by this conversation is durable. No active claim from this conversation remains.

## Completion accounting

Denominator: 7 top-level activation groups (`EC-001` through `EC-007`); EC-002A is a completed subtask and does not inflate the denominator.

- Task completion: 2/7 top-level groups complete; EC-002A additionally complete/validated/released; EC-003–EC-006 blocked/machine-owned; EC-007 merged to sovereign owners.
- Developed files: 10/10 current repository-local activation/control deliverables developed; scaffolding/stubs counted complete: 0.
- Validation: 6/7 activation requirements proven; the remaining requirement is real zero-blocker governed activation evidence, not repository test coverage.
- Integration: 4/6 implementation/integration surfaces installed; real provider/custody execution evidence, Site completion, and downstream verified ingestion remain activation gates.
- Propagation: 0/3 final production propagation destinations verified from an immutable activation packet.
- Goal activation: 70%. The increase from 67% reflects bounded Master-Records dependency removal and restored image publication, not real-provider activation.
- Session consolidation: 7/7 session goal groups completed or durably transferred.

## Archive condition

The scoped validation role is complete and released by hosted run `31290296565`. This conversation no longer contains unique implementation, validation, integration, propagation, or authority information required for continuation. Remaining activation is durably owned by issue #18 and downstream/sovereign machine workstreams. Therefore this conversation is archive-safe even though Ecosystem Chat is not fully activated. Product activation and session archival are distinct states.
