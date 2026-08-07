# AdmittedCode Evidence Demo Mirror Handoff

## Source of truth

This file is the task source of truth for the AdmittedCode evidence-demo slice in `StegVerse-org/LLM-adapter`.

## Goal

Produce portable, secret-free `stegverse.admittedcode.review_packet.v1` inputs deterministically from existing canonical LLM-adapter fixtures so AdmittedCode can review real StegVerse repository evidence without importing the StegVerse runtime.

## Status

**COMPLETE AND MERGED.** This slice no longer owns implementation work.

## Installed paths

- `examples/end_to_end/admittedcode_review/review_packet.allow.json`
- `examples/end_to_end/admittedcode_review/review_packet.deny.json`
- `scripts/build_admittedcode_review_packets.py`
- `scripts/verify_admittedcode_review_fixture.py`
- `tests/test_admittedcode_review_packet_binding.py`
- this handoff

## Canonical source bindings

ALLOW packet:

- source: `examples/end_to_end/simple_query.json`
- source expected outcome: `ALLOW`
- canonical source SHA-256: `f2829c88bb6f876fe78868736c41eb11ea56feb981fb6a4148aaf0ae1436eef9`
- AdmittedCode pressure: `a=2 <= min(g=5,c=5,t=5)`

Refusal packet:

- source: `examples/end_to_end/action_commit_candidate.json`
- source expected outcome: `QUARANTINE`
- canonical source SHA-256: `fb5e02a0dfa24b97917b2a08a33c8a3ea93f2f120217d81ccaac2c5f439f49e7`
- AdmittedCode pressure: `a=6 > min(g=5,c=5,t=5)`

The refusal packet intentionally demonstrates independent review semantics: StegVerse's canonical fixture says `QUARANTINE`; the portable provider-harness expresses its own execution-boundary result as `DENY`. Neither term is rewritten to falsely imply they are the same authority class.

## Boundary

The demo remains fixture-first. It makes no live provider call, does not mutate repositories, does not publish externally, does not grant execution/review/publication/custody authority, and does not claim Master-Records persistence. `authority_effect` must remain `NONE`.

## Portable contract

`canonical StegVerse fixture -> deterministic review_packet.json -> AdmittedCode review -> admissibility_receipt.json -> SDK independent verification`

The packet contains declared request, consent posture, budget, GCAT/BCAT values, source hash, evidence references, and continuity references. It contains no provider secret values.

## Validation

Canonical validation commands:

```bash
python scripts/build_admittedcode_review_packets.py
git diff --exit-code -- examples/end_to_end/admittedcode_review/
pytest tests/test_admittedcode_review_packet_binding.py -v
python scripts/verify_admittedcode_review_fixture.py
```

Hosted PR validation for PR #122 passed before merge. PR #122 merged as commit `12eefc095479b325ccb5551c7279b7ecec1d0283`.

## Downstream completion evidence

- `AdmittedCode/provider-harness` source-verification integration merged in PR #2 as `c4eb15c63f4d0869080f59a57207449a8bf629e7`.
- `StegVerse-org/StegVerse-SDK` source-verified receipt consumption merged in PR #12 as `6227454a78b9c210a8ec0d3eb5be3f15b977c6e7`.
- compact external reviewer packet merged in `AdmittedCode/provider-harness` PR #3 as `b5b942d64cb7d7278b7a4137704fea75f325a77f`.

## Canonical continuation

MERGED INTO: `AdmittedCode/.github/ADMITTEDCODE_MIRROR_HANDOFF.md`

The next ecosystem integration is `StegVerse-Labs/Site`, but current Site orchestration denies external task/session claims. The machine-owned release-condition observer and blocked task live in:

- `AdmittedCode/.github/data/tasks/ADMITTEDCODE-SITE-REVIEW-INTEGRATION.json`
- `AdmittedCode/.github/.github/workflows/site-admission-watch.yml`

No additional work from this LLM-adapter slice is required until a future canonical source-contract change requires packet regeneration and validation.
