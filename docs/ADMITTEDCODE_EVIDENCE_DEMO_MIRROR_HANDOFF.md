# AdmittedCode Evidence Demo Mirror Handoff

## Source of truth

This file is the task source of truth for the AdmittedCode evidence-demo slice in `StegVerse-org/LLM-adapter`.

## Goal

Produce portable, secret-free `stegverse.admittedcode.review_packet.v1` inputs deterministically from existing canonical LLM-adapter fixtures so AdmittedCode can review real StegVerse repository evidence without importing the StegVerse runtime.

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

```bash
python scripts/build_admittedcode_review_packets.py
git diff --exit-code -- examples/end_to_end/admittedcode_review/
pytest tests/test_admittedcode_review_packet_binding.py -v
python scripts/verify_admittedcode_review_fixture.py
```

The build must reproduce the committed packets byte-for-byte. Any canonical source-fixture change therefore makes packet drift visible.

## Downstream

- `AdmittedCode/provider-harness`: portable standalone review demo and source-snapshot hash verification.
- `StegVerse-org/StegVerse-SDK`: non-authorizing receipt consumer and independent receipt-hash verifier.

## Remaining work

Observe hosted CI for this binding, merge when green, then refresh the portable AdmittedCode source snapshot and SDK receipt fixture from the merged canonical packet contract. Do not convert fixture evidence into live-provider or execution claims.
