# AdmittedCode Evidence Demo Mirror Handoff

## Source of truth

This file is the task source of truth for the AdmittedCode evidence-demo slice in `StegVerse-org/LLM-adapter`.

## Goal

Produce portable, secret-free, fixture-first `stegverse.admittedcode.review_packet.v1` inputs from the governed LLM adapter so the same packets can be reviewed by AdmittedCode outside the StegVerse runtime.

## Installed paths

- `examples/end_to_end/admittedcode_review/review_packet.allow.json`
- `examples/end_to_end/admittedcode_review/review_packet.deny.json`
- `scripts/verify_admittedcode_review_fixture.py`
- this handoff

## Boundary

The demo is fixture-first. It makes no live provider call, does not mutate repositories, does not publish externally, does not grant execution/review/publication/custody authority, and does not claim Master-Records persistence. `authority_effect` must remain `NONE`.

## Portable contract

`review_packet.json -> AdmittedCode review -> admissibility_receipt.json`

The packet contains declared request, consent posture, budget, GCAT/BCAT values, evidence references, and continuity references. It contains no provider secret values.

## Validation

Run:

```bash
python scripts/verify_admittedcode_review_fixture.py
```

Expected: `PASS admittedcode review fixtures: 2/2`.

## Downstream

- `AdmittedCode/provider-harness`: portable standalone review demo.
- `StegVerse-org/StegVerse-SDK`: non-authorizing receipt consumer and verifier.

## Remaining work

Observe hosted CI for this branch/PR; then bind the portable packet generation to canonical fixture outputs without converting fixture evidence into live-provider or execution claims.
