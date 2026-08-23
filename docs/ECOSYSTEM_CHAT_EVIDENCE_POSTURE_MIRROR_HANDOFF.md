# Ecosystem Chat Evidence Posture Mirror Handoff

Updated: `2026-08-23T14:18:00-05:00`

```text
goal_id: LLMA-ECOSYSTEM-CHAT-EVIDENCE-POSTURE-190
repository: StegVerse-org/LLM-adapter
branch: feat/ecosystem-chat-evidence-posture-190
canonical_issue: StegVerse-org/LLM-adapter#190
state: ACTIVE_UNIQUE_WORK
credential_authority: TV/TVC
provider_output_authority: NONE
erl_authority: EVIDENCE_SOURCE_ONLY
model_output_authority: NONE
github_token_runtime_authority: NONE
render_authority: NONE
```

## Goal

Keep the Ecosystem Chat answer conversational while retaining a reconstructable evidence receipt containing the exact answer, actual source/artifact data, ERL relationships, model observations, contradictions, uncertainty, and machine-readable evidence posture that constrained the answer's certainty language.

## Invariants

1. Evidence posture constrains wording; it does not grant execution or factual authority.
2. Provider/model agreement does not create truth by majority vote.
3. ERL supplies governed evidence relationships and provenance; it does not become response authority.
4. The exact final response shown to the user is retained in the evidence receipt.
5. Each evidence source retained in a receipt carries its source reference plus the actual normalized data used by the response path.
6. Contradictions and unresolved uncertainty are retained, not silently collapsed.
7. Conversational certainty may be weaker than the evidence posture but MUST NOT exceed it.
8. User-visible response metadata is a minimum projection; full evidence remains in the reconstructable receipt/custody path.
9. TV/TVC remains sole credential/route authority. No NON-TV/TVC secret/token, GitHub-token runtime authority, Render authority, or model-output execution authority is introduced.

## First source slice

- `llm_adapter/evidence_posture.py`
  - canonical evidence-posture vocabulary and ordering;
  - evidence receipt construction and deterministic digest;
  - evidence-source/ERL/model-observation preservation;
  - contradiction/uncertainty retention;
  - certainty-language ceiling validation;
  - minimum user projection.
- `tests/test_evidence_posture.py`
  - deterministic preservation, certainty ceiling, contradiction, and minimum-projection tests.

## Integration continuation

After source validation, bind the receipt builder into `llm_adapter/ecosystem_chat_gateway.py` so a completed bounded response emits both the ordinary conversational `response` and a reconstructable evidence receipt/pointer. Then bind Site's unified conversational surface to display only the conversational answer by default with an optional evidence/history control.

## Completion chain

```text
source implementation
-> deterministic validation
-> gateway integration
-> main merge
-> live governed response
-> Master Records custody/reconstruction
-> Site conversational projection
-> one real evidence receipt proving why displayed certainty was permitted
```

Source/CI/merge are not product activation.
