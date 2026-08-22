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

## Sovereign public receiver lane — ACTIVE IMPLEMENTATION

```text
goal: LLMA-HIL-SOVEREIGN-RECEIVER-021
issue: StegVerse-org/LLM-adapter#185
branch: feat/hil-sovereign-receiver-185
participant_machine_required: false
developer_machine_required: false
github_hosted_runtime_required: false
render_runtime_required: false
third_party_runtime_required: false
canonical_runtime: existing StegVerse sovereign carrier
```

The existing `HIL-RECEIVER-RECEIPT-v2` intake is now being bound directly to the resident StegVerse carrier rather than requiring an external participant/developer machine or a separately hosted HIL server. The bounded implementation adds `llm_adapter/hil_sovereign_receiver_profile.py` and a public non-secret carrier projection at `/api/hil/sovereign-receiver-profile`.

On a non-sovereign runtime the profile is inert. On the canonical carrier it requires the carrier-level durable-state contract:

```text
STEGVERSE_RUNTIME_PROFILE=sovereign-carrier
STEGVERSE_SOVEREIGN_STATE_DURABLE=true
STEGVERSE_SOVEREIGN_STATE_DIR=<non-temporary carrier state root>
```

The profile then maps that existing carrier state into the compatibility receiver by setting only non-secret runtime configuration for HIL intake and durable state. Missing durability attestation or a temporary state root fails closed. No HIL-specific credential is minted and no GitHub/provider secret becomes production authority.

The node advertisement now exposes the HIL readiness/submission/profile endpoints plus explicit `participant_machine_required=false`, `developer_machine_required=false`, `github_hosted_runtime_required=false`, and `third_party_runtime_required=false` fields.

Source completion does not equal activation. Completion of #185 requires a current carrier observation, READY response, real browser upload, durable receiver receipt, exact-byte retrieval/hash verification after restart or replacement, and transfer into the existing TVC lifecycle lane.

## Superseded assumptions

The former host-neutral deployment instructions, locally generated review/publication secrets, and hosted GitHub restart-cycle proof are no longer production continuation mechanisms. No third-party hosting surface is a production HIL dependency. LLM-adapter does not mint, own, copy, or persist production HIL credentials.

The legacy `.github/workflows/hil-process-restart-controlled-cycle.yml` and `scripts/run_hil_process_restart_cycle.py` were retired because the workflow executed on GitHub-hosted infrastructure, received GitHub repository credentials for workflow mechanics, and duplicated restart/private-review behavior that is already governed by TVC.

Historical workflow artifacts remain provenance only and do not establish activation.

## Completed LLM-adapter compatibility work

- HIL v1.1 intake router with exact Primary/prompt/response/provenance validation.
- Exact uploaded PDF and manifest persistence beneath the configured data directory.
- Receiver receipt generation.
- Private-review/publication protocol compatibility surfaces remain fail-closed when no governed credential is present.
- No compatibility surface grants execution, acceptance, publication, custody, Master Record, or release authority.

## Canonical production continuation

```text
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
3 sovereign public receiver source binding: IMPLEMENTATION_IN_PROGRESS / #185
4 authenticated private review: PENDING / TVC #8
5 separately authenticated publication: PENDING
6 Site projection after authenticated decision: PENDING
7 Master Record assembly/release: PENDING
8 downstream verification/publication: PENDING
```

The added receiver lane does not claim product activation from source alone.

## Collision / credential rule

- No non-TV/TVC production secret or token may be introduced or consumed.
- GitHub/GitHub Actions credentials have no HIL runtime authority.
- Do not create a second private-review or production lifecycle lane here.
- Do not make host availability, hosted CI, or compatibility workflow success a production release condition.
- Do not require a participant/developer iMachine, laptop, or local server for the public receiver.

## Session consolidation

```text
ACTIVE RECEIVER IMPLEMENTATION: StegVerse-org/LLM-adapter#185
CANONICAL LIFECYCLE: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
ACTIVE PRIVATE REVIEW CLAIM: StegVerse-Labs/TVC#8
```
