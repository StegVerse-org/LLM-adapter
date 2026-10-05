# Canonical Node Standing Ingress Mirror Handoff

Updated: 2026-10-02
Parent Goal: StegVerse-org/.github `SVORG-STEGOS-PORTABILITY-001`
Parent contract head reviewed: `320aab81a5c386324ae41c0dc5e05152bf5b137d`
Authority effect: NONE

## Existing surfaces mapped

No endpoint was added. The existing `/api/stegverse-node` advertisement now maps existing surfaces for bounded chat, resident-node rendezvous request/ack, organization InTr frame/ack, evaluator InTr, HIL intake and attachment intake.

The mapping is discovery only and grants no authority.

## Canonical standing seam

`governed_manifest_ingress.validate_ingress_manifest` now requires a declared predecessor key and generation. A present `null` predecessor is accepted only for generation 1 and is labeled `ESTABLISH_GENESIS`. Later generations require the canonical predecessor shape `generation, manifest_sha256, result_sha256, heartbeat_epoch` and are labeled `VERIFY_EXISTING`. Missing or malformed continuity fails closed before the SDK endpoint is called. Failed existing-node verification never falls back to genesis.

The predecessor shape and oscillator ordering reuse the StegVerse-SDK contract at `50d6ed8c1e9058092ce5056fa09157804b2c70d3`; this adapter does not define a second receipt-chain predecessor semantics.

## Processing selection repair

The bounded AI-entry backend accepts an already-declared route as authoritative for its local response classification and uses message keyword classification only when no declared route exists. This prevents message content from substituting a governed manifest-selected processing declaration on a governed caller path.

The production `/api/ecosystem-chat` request model still accepts caller-supplied transition identity. It is not promoted to canonical standing by this repair. Direct public-chat binding into the canonical standing validator remains a separate source gap and must fail closed wherever canonical standing is required.

## Regressions added

- missing predecessor key fails closed
- explicit generation-1 null predecessor is carried as ESTABLISH_GENESIS
- generation >1 canonical predecessor is carried as VERIFY_EXISTING
- failed existing-node verification does not re-enroll
- node advertisement exposes standing semantics, maps existing continuations, and withholds the machine continuation until standing resolves `ALLOW`

## Proof boundary

Source changes and regression definitions do not prove deployed propagation, authentic node standing, attestation, external transport, custody, KV-as-node, or StegBrowser-as-KV-surface. Those remain NOT_PROVEN unless their canonical owners provide evidence.


## Machine-readable continuation instructions

Two non-authorizing instruction profiles exist, and canonical standing is what releases them. `LLM_MACHINE_CONTINUATION` directs a machine that already has a canonical manifest to `llm_adapter.governed_manifest_ingress` and the existing distributed SDK manifest transfer. `EXTERNAL_FRAMEWORK_MANIFEST_CONTINUATION` directs a framework to the SDK-owned `stegverse.manifest_builder.build_manifest` / `stegverse manifest build` and `stegverse.external_framework_runner.manifest_external_framework_submission` / `stegverse external-run` path.

The advertisement does not serve either profile. `GET /api/stegverse-node` names `node_standing_readiness_endpoint` and `node_standing_endpoint` and declares `machine_readable_instructions_available_unauthenticated: false`; `llm_adapter.node_standing` resolves `POST /api/node-standing` and the profiles are returned on `ALLOW` and from nowhere else. This is the gap this amendment closes: the advertisement previously declared `ALL_EXTERNAL_ECOSYSTEM_INGRESS_REQUIRES_CANONICAL_NODE_STANDING` and served the continuation in the same unauthenticated response, so the requirement was a statement the surface made about itself rather than a gate anything crossed.

`GET /api/node-standing/readiness` publishes the requirement before anyone attempts it — mandatory `predecessor` key, `null` for explicit genesis, absent key `FAIL_CLOSED`, the two modes, oscillator-epoch ordering only — and grants nothing. A failed `VERIFY_EXISTING` stays failed; `failed_verification_becomes_genesis` and `silent_reenrollment_permitted` are both false and are asserted as such.

The predecessor field set is read off `stegverse.external_interlock_bootstrap.successor_predecessor_binding` at import rather than restated in this repository, because `lineage_contract.owner` is `StegVerse-org/StegVerse-SDK` and `local_second_predecessor_semantics_permitted` is false. The owner's binding function cannot be re-run from a standing request: it consumes the predecessor manifest and result, while the request carries their digests only. A declared predecessor is therefore checked against the owner's shape, not recomputed, and both the readiness and the disposition carry `declared_predecessor_lineage_recomputed: false`.

An `ALLOW` is structural standing, not authenticated standing. `attestation_owner_state` remains `NOT_PROVEN`, caller-supplied identity is unverified, and the released profiles still carry `NONE_INSTRUCTIONS_ONLY`. Source regressions exercise both standing modes, every neighbouring refusal, and release on `ALLOW` only. Authentic deployed discovery, external transport, far-side InTr admission and organization custody remain separate runtime proof.



## Test 5/6 external submission boundary — 2026-10-02

External instructions terminate at `SUBMIT_CANONICAL_MANIFEST` and `RETAIN_SUBMISSION_RESULT_AND_EVIDENCE`. Interlock/InTr is `INTERNAL_POST_SUBMISSION`; `EXTERNAL_INTERLOCK_INTR` is deferred to a separate successor expansion after Tests 5/6. This changes the caller instruction boundary, not the retained experiment, Test 5-before-Test 6 ordering, or downstream receipt/custody acceptance. Source tests are not Test 5/6 runtime results.

`SDK_MACHINE_CONTRACT` derives from existing SDK builder signatures, processor/route declarations, return projections and console commands. The adapter consumes that SDK projection instead of maintaining a second instruction recipe. The console wrapper already dispatched manifest/external-run; its top-level help omitted them. Shared dispatch/help declarations repair that discovery mismatch.

The external-framework helper currently reports `SDK_LOCAL_MANIFEST_HANDOFF`; it does not prove receiver observation. Adapter predecessor checks establish structural validity only, not authenticated standing. Production endpoint binding, authentic standing, runtime execution, deployment and custody remain NOT_PROVEN. No endpoint, runtime, credential path or authority was created.

Source checkpoint: SDK PR #424 at `1b24ab0fe4ca1690994a7bacb4ac2286a35f2603`; 35 local source tests and 4 subtests passed. Organization PR #31 merged as `96541b2f0dcb33c3fc23a30869d9bcb4258f1f5a` during this session; this Test 5/6 amendment is a follow-up, not part of that merge. SDK and adapter integration still require exact-head CI and merge; no deployment or runtime claim.

Counter reconciliation: session has 4 user prompts; goal recovery count was already 20/20, now 24 qualifying prompts. Do not reset the parent counter. The external Interlock/InTr successor may be registered only after this boundary is retained on canonical main; its concrete scope is reciprocal external-node transport contracts and tests, with an explicit dependency on Tests 5/6 and no change to their caller instructions. No successor ID has yet been invented or registered.


## Current-source reconciliation — 2026-10-05

Goal `SVORG-STEGOS-PORTABILITY-001` remains ACTIVE/in_progress. Session prompt 8;
parent goal prompt 28/20, retained without reset. SDK #424 is closed unmerged;
this is a newly reconciled bounded delta, not restoration of its stale branch.

COSV omission was a coordination defect, not an exemption. The orchestration
registry's closed schema does not prevent a separate canonical-profile task.v1
projection. `control/task-vector-index.json` and its referenced source metrics in
StegVerse-org/.github propose `20011100100000`, generated with the existing
StegVerse-Labs/.github `scripts/cosv.py` encoder. This is source coordination only,
not a WorkerCoordinator claim/fence or execution authority. Until reviewed/merged,
the projection remains a candidate and must not be described as canonical main.

Current SDK declarations already own manifest construction, validation, route
selection, peer governance execution profiles and local handoff evidence. The
bounded repair projects those declarations, adds missing manifest-command help,
and makes the external-framework helper reuse public run-manifest's canonical
source-bound dispatcher. Completion egress does not select the outbound route.
Adapter discovery preserves its existing adapter receiving operation; native SDK
discovery does not acquire an adapter prerequisite. No standing evaluator changes.

Both instruction profiles terminate at SUBMIT_CANONICAL_MANIFEST and
RETAIN_SUBMISSION_RESULT_AND_EVIDENCE. Interlock/InTr remains INTERNAL_POST_SUBMISSION;
EXTERNAL_INTERLOCK_INTR remains deferred until after Tests 5/6. SDK_LOCAL_MANIFEST_HANDOFF
is not receiver observation. Source tests with injected canonical source/receiver
fixtures do not establish authentic submission, transport, custody or Test 5/6 PASS.

Local validation: 50 SDK tests + 4 subtests; 53 adapter tests + 2 subtests passed
against the repaired SDK source. SDK bundled test runner also passed 18 affected tests.
Exact-head CI, review and merge remain required. No release or runtime attempt.
Remaining portability obligations retain their existing registry ownership.

Integration order: organization COSV projection PR #71, SDK PR #429 at
`9dff3c742f291265a74b42dc69c3c560cbe5942a`, then this adapter dependency update.
The pin uses that exact SDK source commit; canonical-main availability is pending
SDK review/merge. Do not describe closed #424 as the current SDK baseline.
