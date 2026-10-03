# Pre-Protocol Receipt Finding Mirror Handoff

Updated: 2026-10-03
Organization: `StegVerse-org`
Repository: `LLM-adapter`
Finding ID: `LLM-ADAPTER-PRE-PROTOCOL-RECEIPTS-001`
Register: `.stegverse/pre-protocol-receipt-register.json`
Status: `RECORDED / NOT REMEDIATED / REMEDIATION OWNED HERE`

## What was observed

A repository sweep left four committed receipts modified with no source change:

```text
- "retrieved_at": "2026-08-17T01:57:38+00:00"
+ "retrieved_at": "2026-10-03T13:20:26+00:00"
```

Nothing had changed except when the suite ran.

## Why

Twenty committed receipts under `receipts/` are produced by test modules or validation scripts rather than appended to a ledger. Five of those writes sit at module level, so *collecting* the test file rewrites the committed file:

```text
tests/test_va_claim_assistant_governed_dispatch.py:215
tests/test_va_claim_assistant_privacy_runtime.py:158
tests/test_va_claim_assistant_governed_retrieval.py:67
tests/test_va_claim_assistant_route_classifier.py:75
tests/test_va_claim_assistant_route_generators.py:203
```

Their timestamps come from `llm_adapter/retrieval_evidence.py::evidence_pointer`, which defaults `retrieved_at` to `utc_now_iso()` — a host clock read. So the same transition produces different content on every run.

## These are from a different ruleset

They predate the transition protocol this repository now holds, and they should be read as artifacts of the earlier one rather than as receipts of the current one.

| | Pre-protocol | Current protocol |
| --- | --- | --- |
| Ordering | host clock | `OSCILLATOR_HEARTBEAT_EPOCH_ONLY` |
| Content stability | depends on when it ran | same transition, same digest |
| Producer | a test or a script | an append to the ledger |
| Chain position | none | `previous_receipt_sha256`, hash-linked |
| Replay | not possible | the chain is the replay |
| A test run may write one | yes, and does | no |

The current protocol is declared in `.stegverse/heartbeat-awareness.json` (`progression_dependency: OSCILLATOR_ONLY`, `canonical_owner: StegVerse-Labs/.github`) and enforced in `.stegverse/transition-ledger/emit.py`, whose receipts carry `ordering`, a derived-or-supplied `hb_reference`, and `observed_at_is_descriptive_not_ordering: true`.

`receipts/work-safety/` is excluded: those manifests are authored deliberately per change set, not produced by a run.

## What this does not do

This records the finding. It deletes nothing, rewrites nothing, migrates nothing, and does not claim these files are invalid as the source evidence they were written to be. It exists so that a reader seeing this churn knows it is the finding rather than a defect introduced by whatever change was being tested, and so that nobody mistakes a clock-stamped validation artifact for a chain receipt.

## Remediation, owned here and not performed here

1. Stop test modules writing committed receipts — a run's output belongs outside the committed tree.
2. Supply `retrieved_at` from the heartbeat rather than defaulting it to a host clock, so a receipt's content does not depend on when it was produced.
3. Decide, per receipt, whether it is a ledger transition — which puts it on the chain — or a validation artifact, which should not be committed as a receipt at all.

Each is a behaviour change to committed evidence and to tests that currently depend on writing it, so each is its own reviewed change rather than a side effect of this one.
