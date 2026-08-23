# Ecosystem Chat Evidence Posture Mirror Handoff

Updated: `2026-08-23T14:21:00-05:00`

```text
goal_id: LLMA-ECOSYSTEM-CHAT-EVIDENCE-POSTURE-190
repository: StegVerse-org/LLM-adapter
branch: main
canonical_issue: StegVerse-org/LLM-adapter#190
merged_pull_request: StegVerse-org/LLM-adapter#191
merged_commit: a8b58a4144123b3b75f61e3fdb878aa06fd2616e
state: ACTIVE_UNIQUE_WORK
credential_authority: TV/TVC
provider_output_authority: NONE
erl_authority: EVIDENCE_SOURCE_ONLY
model_output_authority: NONE
github_token_runtime_authority: NONE
render_authority: NONE
```

## Goal

Keep the Ecosystem Chat answer conversational while retaining a reconstructable evidence receipt containing the exact answer, actual source/artifact data, ERL relationships, model observations, contradictions, uncertainty, and machine-readable evidence posture that constrains the answer's certainty language.

## Invariants

1. Evidence posture constrains wording; it does not grant execution or factual authority.
2. Provider/model agreement does not create truth by majority vote.
3. ERL supplies governed evidence relationships and provenance; it does not become response authority.
4. The exact final response shown to the user is retained in the evidence receipt.
5. Each evidence source retained in a receipt carries its source reference plus the actual normalized data used by the response path.
6. Contradictions and unresolved uncertainty are retained, not silently collapsed.
7. When a governed evidence posture exists, conversational certainty may be weaker than the posture but MUST NOT exceed it.
8. Before a governed evidence aggregator has established posture, an existing provider response may be retained only as `UNKNOWN` with `certainty_constraint_applied=false`; this explicit unassessed state cannot be used with a stronger posture to bypass the ceiling.
9. User-visible response metadata is a minimum projection; full evidence remains in the reconstructable receipt/custody path.
10. TV/TVC remains sole credential/route authority. No NON-TV/TVC secret/token, GitHub-token runtime authority, Render authority, or model-output execution authority is introduced.

## Source integrated on `main`

`llm_adapter/evidence_posture.py` now provides:

- canonical `UNKNOWN`, `UNSUPPORTED`, `INCOMPLETE`, `MIXED`, `SUPPORTED`, and `STRONGLY_SUPPORTED` evidence posture states;
- conservative posture ordering and conversational certainty detection;
- deterministic evidence receipt construction and digest;
- exact final-response retention;
- evidence-source validation requiring both `source_ref` and the actual normalized `data` used by the response path;
- ERL relationship, model observation, contradiction, uncertainty, and governance-reference retention;
- explicit `certainty_constraint_applied` state;
- a fail-closed rule preventing certainty-validation bypass for any posture stronger than `UNKNOWN`;
- minimum user projection that exposes posture/counts/receipt identity without embedding raw evidence.

`tests/test_evidence_posture.py` installs deterministic cases for evidence preservation, source-data requirements, certainty ceiling, explicit UNKNOWN/unassessed provider handling, contradiction/uncertainty retention, and minimum projection.

## Repository evidence

```text
issue: #190 OPEN
PR: #191 MERGED
merge_commit: a8b58a4144123b3b75f61e3fdb878aa06fd2616e
PR_mergeable_before_merge: true
PR_triggered_CI_observed: false
source_validation_claim: NOT YET ESTABLISHED BY HOSTED CI
```

No hosted CI result is being inferred from mergeability. Source is integrated; deterministic validation remains an explicit evidence gap until an actual validator/test execution is observed.

## Existing provider boundary discovered during integration

`llm_adapter/governed_provider.py` returns provider text, provider/model identity, request/receipt identity, measured usage, cost posture, and fallback state. It does **not** establish factual evidence posture. Therefore provider output alone must not upgrade Ecosystem Chat certainty. Until ERL/source/model-evidence aggregation produces a governed posture, the response evidence state remains `UNKNOWN`/unassessed.

## Next required transitions

1. Execute deterministic validation of `tests/test_evidence_posture.py` on an observed validation path.
2. Bind the receipt builder into `llm_adapter/ecosystem_chat_gateway.py` so every bounded response retains an evidence receipt, using `UNKNOWN`/`certainty_constraint_applied=false` when no governed evidence posture exists.
3. Add an admitted evidence-aggregation input that can populate actual sources, ERL relationships, model observations, contradictions, uncertainty, and governed posture without accepting public-client self-assertion as authority.
4. When governed posture exists, enforce the certainty-language ceiling before returning the conversational response.
5. Submit the full evidence receipt through the existing Master Records custody/reconstruction path.
6. Project only the conversational answer plus minimum evidence metadata to `StegVerse-Labs/Site`, with an optional evidence/history control.
7. Prove one real deployed response reconstructs the exact answer, evidence used, posture, and why that certainty language was permitted.

## Completion chain

```text
source implementation: COMPLETE_MERGED
hosted/deterministic validation: PENDING OBSERVATION
gateway integration: PENDING
governed evidence aggregation: PENDING
Master Records custody/reconstruction: PENDING
Site conversational projection: PENDING
real governed response proof: PENDING
product activation effect: NONE CLAIMED
```

Source/merge is not product activation. This lane remains open under #190.
