# HIL Runtime Mirror Handoff

## Source of truth

This document is the current LLM-adapter HIL v1.1 compatibility/intake continuation record. Production lifecycle authority remains with the existing StegVerse TVC controlled-cycle lane.

```text
Primary: v1.1
Primary SHA-256: a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462
Protocol: HIL-PROTOCOL-v1.1
Prompt: HIL-PROMPT-v1.1
Prompt SHA-256: cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c
Intake router: llm_adapter/hil_intake_v1_1_api.py
Compatibility gateway: llm_adapter/combined_gateway.py
credential_authority: TV/TVC
github_token_runtime_authority: NONE
third_party_runtime_dependency: NONE_ALLOWED
production_owner: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
private_review_owner: StegVerse-Labs/TVC#8
```

## Sovereign public receiver source — complete / live activation separate

```text
goal: LLMA-HIL-SOVEREIGN-RECEIVER-021
issue: StegVerse-org/LLM-adapter#185
merge: 40eaa9af5cb7e3845ddaf4e79e02d299c76b9655
participant_machine_required: false
developer_machine_required: false
github_hosted_runtime_required: false
render_runtime_required: false
third_party_runtime_required: false
canonical_runtime: existing StegVerse sovereign carrier
source_state: COMPLETE_MERGED
live_activation_state: NOT_PROVEN_HERE
```

The `HIL-RECEIVER-RECEIPT-v2` intake is bound to the StegVerse sovereign carrier and does not require a participant/developer machine or separately hosted HIL server. The carrier profile requires only the non-secret sovereign durability contract:

```text
STEGVERSE_RUNTIME_PROFILE=sovereign-carrier
STEGVERSE_SOVEREIGN_STATE_DURABLE=true
STEGVERSE_SOVEREIGN_STATE_DIR=<non-temporary carrier state root>
```

Missing durability or a temporary state root fails closed. No GitHub/provider credential becomes runtime authority. Source completion does not establish a current receiver process, public HTTPS route, Site readiness, browser receipt, restart proof, or TVC lifecycle handoff.

## Post-submit reconstruction source — complete, validated and released

```text
task: LLMA-HIL-POST-SUBMIT-RECONSTRUCTION-029
issue: StegVerse-org/LLM-adapter#192
pull_request: #193
validated_head: 1736cc8c2f61a42aba1fb112beeeb2e38987bba0
merge: f90be5e4cb277c46426b0aa956ee1652f9b60b4a
targeted_hil_validation_run: 32691608816 SUCCESS
repository_validation_run: 32691608760 SUCCESS
state: COMPLETE_MERGED_VALIDATED_RELEASED
public_status_endpoint: /api/hil/submissions/{submission_id}/status
exact_bytes_endpoint: /api/hil/submissions/{submission_id}/exact-bytes
exact_bytes_auth: EXISTING TV/TVC STEGVERSE_HIL_REVIEW_TOKEN
new_credential_or_token_minted: false
```

PR #193 closes the source-level reconstruction gap needed by the real restart/replacement evidence lane. The public status endpoint exposes only stable non-sensitive evidence: submission identity, HIL Primary/prompt identities, submitted-file SHA-256, provenance-manifest SHA-256, chain state, size, validation state, active-content state, and explicit non-authority fields. It does not expose participant identifier, publication consent, review notes, filesystem paths, provenance content, or submitted bytes.

The exact-byte endpoint is intentionally not anonymous. It reuses the existing TV/TVC-owned HIL review authentication boundary. After authentication it:

```text
resolves the persisted artifact only inside the admitted HIL originals root
-> rereads exact bytes
-> recomputes SHA-256
-> compares SHA-256 to the immutable submission row
-> compares byte length to stored size_bytes
-> fails closed on path escape, missing file, size mismatch, or digest mismatch
-> returns application/pdf only after exact verification
```

Successful reconstruction returns `X-SteGVerse-HIL-Reconstruction-State: EXACT_BYTES_HASH_VERIFIED` and `Cache-Control: no-store`. No filesystem path is returned.

Exact-head targeted HIL validation proved the public-status privacy boundary, denial without the existing TV/TVC review authentication, authorized exact-byte equality/hash verification, tamper detection, sovereign receiver source invariants, and no participant/developer/third-party runtime dependency. The complete credential-free repository validation also passed on the same PR head.

These runs are source/integration proof only. They do not prove that a receiver restart or replacement actually occurred or that the persisted bytes survived one on the production path.

## Completed compatibility/source capabilities

- HIL v1.1 intake with exact Primary/prompt/response/provenance validation.
- Exact uploaded PDF and provenance persistence beneath the configured HIL data directory.
- `HIL-RECEIVER-RECEIPT-v2` generation.
- Sovereign carrier receiver profile/source binding.
- Privacy-bounded public submission status lookup.
- TV/TVC-authenticated exact-byte reconstruction with path, hash, size, and tamper checks.
- Node advertisement of readiness, submission, status, reconstruction, and sovereign-profile routes.
- Private-review/publication compatibility remains separately authenticated and fail-closed.
- No compatibility endpoint grants execution, acceptance, publication, custody, Master Record append, or release authority.

## Canonical live continuation

```text
StegVerse-Labs/.github#246
StegVerse-Labs/.github/docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md
StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
StegVerse-Labs/TVC/docs/EXPERIMENT_BACKEND_MIRROR_HANDOFF.md
StegVerse-Labs/TVC#8
StegVerse-Labs/Site#67
master-records/orchestration#13
```

The next valid evidence chain is external to this released LLM-adapter source task:

```text
resident WorkerCoordinator allocates a real HIL claim/fresh fence
-> hil-sovereign-receiver-worker executes
-> /api/hil/sovereign-receiver-profile = ACTIVE_SOVEREIGN_RECEIVER
-> /api/hil/readiness = READY with exact v1.1 identities
-> public HTTPS StegVerse rendezvous
-> Site observes readiness and enables controlled upload
-> real browser submission returns HIL-RECEIVER-RECEIPT-v2
-> receiver process restart/replacement
-> authenticated exact-byte reconstruction returns EXACT_BYTES_HASH_VERIFIED with the original SHA-256
-> existing TVC lifecycle receives the package/receipt
```

No source merge, GitHub Actions run, repository status, or endpoint declaration may substitute for those observations.

## TVC state retained

The TVC backend already proves generalized controlled-cycle state, deterministic artifact reconstruction, custody receipt, successor-runtime continuity, stable lookup, and non-authorizing projection for its established evidence. Genuine participant custody for `HIL-20260731-GPT56-001` remains retained there. The authenticated private-review decision remains separately governed under TVC #8.

## Activation denominator

```text
1 generalized TVC backend merged/validated: COMPLETE
2 authentic prior participant custody/reconstruction: COMPLETE
3 sovereign public receiver source binding: COMPLETE_MERGED
4 post-submit reconstruction source contract: COMPLETE_MERGED_VALIDATED_RELEASED
5 real sovereign receiver execution + READY: PENDING / StegVerse-Labs/.github#246
6 public HTTPS + controlled Site browser receipt: PENDING
7 production restart/replacement exact-byte proof: PENDING
8 TVC lifecycle admission/private review: PENDING / existing TVC lane
9 separately authenticated publication: PENDING
10 Site/Master Records/downstream release and verification: PENDING
```

## Collision and credential rules

- No non-TV/TVC production secret or token may be introduced or consumed.
- GitHub/GitHub Actions credentials have no HIL runtime authority.
- Do not create a second private-review or lifecycle authority.
- Do not expose exact submitted bytes anonymously to satisfy reconstruction proof.
- Do not make hosted CI, a participant/developer iMachine, Render, or another third-party runtime a production dependency.
- Do not equate source completion with live receiver activation or restart durability.

## Session consolidation

```text
LLM-adapter reconstruction source task: COMPLETE_RELEASED
source task continuation dependency on this chat: false
sovereign live receiver owner: StegVerse-Labs/.github#246
canonical lifecycle: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
private review owner: StegVerse-Labs/TVC#8
next evidence class: REAL_RUNTIME_AND_RESTART_OBSERVATION
```


## 2026-08-29 Universal Interlock/InTr intake chain

The former live-continuation sequence that treated a continuously READY HIL receiver as a prerequisite to beginning submission is superseded by the canonical StegVerse universal transport invariant.

The HIL intake endpoint now requires a canonical transport intent alongside the PDF and provenance:

```text
schema: stegverse.universal-intr-transport/v1
protocol: InTr
source: DEVICE_SYSTEM / Site:HIL
destination: STEGOS_ECOSYSTEM / HIL:Ingress
boundary_path: [DEVICE_SYSTEM, STEGOS_ECOSYSTEM]
interlock_required: true
event_triggered: true
always_on_receiver_required: false
second_user_device_required: false
receiver_unavailable_disposition: DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION
exact_packet_transport_retry_allowed: true
blind_consequence_retry_allowed: false
credential_authority: TV/TVC
authority_transfer: false
```

The receiver independently recomputes the canonical HIL payload binding from:

```text
exact response PDF SHA-256
canonical provenance SHA-256
Primary SHA-256
Prompt SHA-256
```

and rejects any transport intent that does not bind that exact payload or attempts a noncanonical boundary path.

After exact bytes and provenance are durably persisted and re-read, the receiver creates a chained Interlock lineage:

```text
DEVICE_SYSTEM / Site:HIL
-> InTr hop receipt
-> STEGOS_ECOSYSTEM / HIL:Ingress
-> chained same-boundary Interlock receipt
-> STEGOS_ECOSYSTEM / HIL:Custody
-> durable next Interlock intent
-> STEGOS_ECOSYSTEM / TVC:HIL-Lifecycle
```

The first two completed transport events emit `stegverse.intr.hop_receipt/v1` receipts. The TVC transition is represented only as a durable next intent under `intr-outbox/tvc-hil-lifecycle/`; TVC admission is not claimed until TVC independently validates the chain and emits its own receipt.

New HIL receipt fields:

```text
intr_receipt_chain.schema = stegverse.hil.intr_receipt_chain/v2
intr_tvc_queue_hash
next_required_transition = HIL_CUSTODY_TVC_INTERLOCK_ADMISSION
transport_initiated_by_submission = true
always_on_application_receiver_required = false
second_user_device_required = false
```

Lifecycle separation remains exact:

```text
submission initiated != ingress received
ingress received != HIL custody
HIL custody != TVC lifecycle admission
TVC admission != private review
private review != publication
publication != Master Records release
```

Source implementation on this branch does not itself prove a production transport event.
