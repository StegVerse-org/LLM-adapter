# HIL Runtime Mirror Handoff

## Source of truth

This document describes the LLM-adapter compatibility/intake surface for HIL v1.1. Production HIL continuation is owned by the StegVerse TVC controlled-cycle backend and its active lifecycle claims.

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

## Sovereign public receiver lane — SOURCE MERGED / LIVE ACTIVATION SEPARATE

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

The existing `HIL-RECEIVER-RECEIPT-v2` intake is bound directly to the resident StegVerse carrier rather than requiring an external participant/developer machine or a separately hosted HIL server. The bounded implementation includes `llm_adapter/hil_sovereign_receiver_profile.py` and a public non-secret carrier projection at `/api/hil/sovereign-receiver-profile`.

On a non-sovereign runtime the profile is inert. On the canonical carrier it requires the carrier-level durable-state contract:

```text
STEGVERSE_RUNTIME_PROFILE=sovereign-carrier
STEGVERSE_SOVEREIGN_STATE_DURABLE=true
STEGVERSE_SOVEREIGN_STATE_DIR=<non-temporary carrier state root>
```

The profile maps that existing carrier state into the compatibility receiver by setting only non-secret runtime configuration for HIL intake and durable state. Missing durability attestation or a temporary state root fails closed. No HIL-specific credential is minted and no GitHub/provider secret becomes production authority.

The node advertisement exposes the HIL readiness/submission/profile endpoints plus explicit `participant_machine_required=false`, `developer_machine_required=false`, `github_hosted_runtime_required=false`, and `third_party_runtime_required=false` fields.

Source completion does not equal activation. The real receiver still requires current sovereign-runtime observation, READY response, public HTTPS rendezvous, real Site browser upload, durable receiver receipt, exact-byte post-restart verification, and transfer into the existing TVC lifecycle lane.

## Post-submit reconstruction lane — issue #192

```text
task: LLMA-HIL-POST-SUBMIT-RECONSTRUCTION-029
issue: StegVerse-org/LLM-adapter#192
branch: feat/hil-post-submit-reconstruction-192
state: SOURCE_INSTALLED_VALIDATION_PENDING
public_status_endpoint: /api/hil/submissions/{submission_id}/status
exact_bytes_endpoint: /api/hil/submissions/{submission_id}/exact-bytes
exact_bytes_auth: EXISTING TV/TVC STEGVERSE_HIL_REVIEW_TOKEN
new_credential_or_token_minted: false
```

This lane closes a source-level gap in the restart/replacement proof path without weakening privacy or creating a second authority surface.

The public status endpoint returns only stable evidence fields: submission identity, HIL Primary/prompt identities, submitted-file SHA-256, provenance-manifest SHA-256, chain state, size, validation state, active-content state, and explicit non-authority fields. It does **not** expose participant identifier, publication consent, review notes, filesystem paths, provenance content, or submitted bytes.

The exact-byte endpoint is not public anonymous content. It reuses the existing TV/TVC-owned HIL review authentication boundary; no new capability token, participant secret, GitHub credential, or provider credential is created. After authentication it resolves the persisted artifact only inside the admitted HIL `originals/` root, rereads the bytes, recomputes SHA-256, verifies the stored size, and fails closed on missing bytes, path-boundary mismatch, size mismatch, or digest mismatch. A successful response returns the exact PDF with `Cache-Control: no-store` and an `EXACT_BYTES_HASH_VERIFIED` reconstruction header.

Required tests on this lane prove:

```text
public status privacy boundary
unauthenticated exact-byte denial
authorized exact-byte equality
recomputed SHA-256 binding
tamper detection / fail closed
private review remains separately authenticated
```

Passing source tests for this lane will mean the receiver has a bounded mechanism capable of performing the post-restart proof. It will **not** mean a restart, receiver replacement, public HTTPS activation, browser submission, TVC admission, publication, or Master Records release actually occurred.

## Superseded assumptions

The former host-neutral deployment instructions, locally generated review/publication secrets, and hosted GitHub restart-cycle proof are no longer production continuation mechanisms. No third-party hosting surface is a production HIL dependency. LLM-adapter does not mint, own, copy, or persist production HIL credentials.

The legacy `.github/workflows/hil-process-restart-controlled-cycle.yml` and `scripts/run_hil_process_restart_cycle.py` were retired because the workflow executed on GitHub-hosted infrastructure, received GitHub repository credentials for workflow mechanics, and duplicated restart/private-review behavior that is already governed by TVC.

Historical workflow artifacts remain provenance only and do not establish activation.

## Completed LLM-adapter compatibility work

- HIL v1.1 intake router with exact Primary/prompt/response/provenance validation.
- Exact uploaded PDF and manifest persistence beneath the configured data directory.
- Receiver receipt generation.
- Sovereign receiver profile/source binding merged in `40eaa9af5cb7e3845ddaf4e79e02d299c76b9655`.
- Private-review/publication protocol compatibility surfaces remain fail-closed when no governed credential is present.
- No compatibility surface grants execution, acceptance, publication, custody, Master Record, or release authority.

## Canonical production continuation

```text
StegVerse-Labs/.github#246
StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
StegVerse-Labs/TVC/docs/EXPERIMENT_BACKEND_MIRROR_HANDOFF.md
StegVerse-Labs/TVC#8
StegVerse-Labs/StegCore/docs/HIL_SESSION_CONSOLIDATION_MIRROR_HANDOFF.md
StegVerse-Labs/Site#67
master-records/orchestration#13
```

The TVC backend already proves generalized controlled-cycle state, deterministic artifact reconstruction, custody receipt, successor-runtime continuity, stable lookup, and non-authorizing projection. Genuine participant custody for `HIL-20260731-GPT56-001` is retained there. The authenticated private-review decision is still pending under TVC #8.

## Activation denominator

```text
1 generalized TVC backend merged/validated: COMPLETE
2 authentic participant custody/reconstruction: COMPLETE
3 sovereign public receiver source binding: COMPLETE_MERGED
4 post-submit reconstruction source contract: SOURCE_INSTALLED_VALIDATION_PENDING / #192
5 real sovereign receiver READY + public HTTPS + browser receipt: PENDING / .github#246 + Site
6 authenticated private review: PENDING / TVC #8
7 separately authenticated publication: PENDING
8 Site projection after authenticated decision: PENDING
9 Master Record assembly/release: PENDING
10 downstream verification/publication: PENDING
```

The receiver and reconstruction source lanes do not claim product activation from source alone.

## Collision / credential rule

- No non-TV/TVC production secret or token may be introduced or consumed.
- GitHub/GitHub Actions credentials have no HIL runtime authority.
- Do not create a second private-review or production lifecycle lane here.
- Do not make host availability, hosted CI, or compatibility workflow success a production release condition.
- Do not require a participant/developer iMachine, laptop, or local server for the public receiver.
- Do not expose exact submitted bytes anonymously merely to satisfy reconstruction proof.

## Session consolidation

```text
SOURCE RECONSTRUCTION WORK: StegVerse-org/LLM-adapter#192
SOVEREIGN LIVE RECEIVER: StegVerse-Labs/.github#246
CANONICAL LIFECYCLE: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
ACTIVE PRIVATE REVIEW CLAIM: StegVerse-Labs/TVC#8
```
