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
result: COMPATIBILITY_RUNTIME_IMPLEMENTED / PRODUCTION_LIFECYCLE_MERGED_INTO_TVC
```

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
3 authenticated private review: PENDING / TVC #8
4 separately authenticated publication: PENDING
5 Site projection after authenticated decision: PENDING
6 Master Record assembly/release: PENDING
7 downstream verification/publication: PENDING
```

HIL product activation remains 2/7. LLM-adapter compatibility tests do not change that denominator.

## Collision / credential rule

- No non-TV/TVC production secret or token may be introduced or consumed.
- GitHub/GitHub Actions credentials have no HIL runtime authority.
- Do not create a second private-review or production lifecycle lane here.
- Do not make host availability, hosted CI, or compatibility workflow success a production release condition.

## Session consolidation

```text
MERGED INTO: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md
ACTIVE CLAIM: StegVerse-Labs/TVC#8
LLM-adapter production HIL claim: NONE
```
