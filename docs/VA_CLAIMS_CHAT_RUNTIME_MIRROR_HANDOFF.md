# VA Claims Chat Runtime Mirror Handoff

## Identity

```text
Task ID: VACC-RUNTIME-CONTRACT-001
Originating goal: governed VA Claims Chat with document-workspace parity and a staged path toward veteran-approved automated claim filing
Repository: StegVerse-org/LLM-adapter
Branch: main
Canonical adapter issue: StegVerse-org/LLM-adapter#90
Canonical Site issue: StegVerse-Labs/Site#113
Document workspace issue: StegVerse-Labs/Site#116
```

## Collision and ownership

The existing adapter claim in `docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md` owns:

```text
va_claim_assistant/**
tests/test_va_claim_assistant_*.py
.github/workflows/va-claim-assistant-governed-retrieval.yml
```

This task did not modify those surfaces. It owns only:

```text
contracts/va-claims-chat-runtime.json
scripts/validate_va_claims_chat_runtime_contract.py
.github/workflows/va-claims-chat-runtime-contract.yml
receipts/va-claims-chat-runtime-contract-validation.json
docs/VA_CLAIMS_CHAT_RUNTIME_MIRROR_HANDOFF.md
```

## Claim

```text
claim state: RELEASED_COMPLETE
role: INTEGRATION_CONTRACT
claim created: 2026-08-02T20:47:00Z
claim released: PASS receipt committed and requirements recorded in adapter issue #90
validation evidence: receipts/va-claims-chat-runtime-contract-validation.json
collision boundary preserved: no generator, classifier, dispatcher, test, provider, custody, deployment, or filing transport implementation
```

## Installed contract

The runtime contract establishes:

- all thirteen governed VA routes;
- route-specific generator and source requirements;
- source fact, user-record fact, inference, contradiction, uncertainty, referral, custody, and reconstruction fields;
- raw-document rejection by the adapter;
- acceptance only of sanitized derived document context from `Site#116`;
- staged runtime capability states;
- veteran-retained submission authority;
- automated filing inactive;
- explicit filing gates and authorized-transport requirement;
- fail-closed runtime states;
- receipt-derived Site projection.

## Validation result

```text
state: PASS
route_count: 13
required_routes_present: true
raw_documents_rejected: true
sanitized_derived_context_required: true
automated_filing_active: false
veteran_submission_authority_preserved: true
authority_effect: false
activation_effect: false
```

The contract validator and workflow remain machine-owned observers for future contract drift.

## Authority boundary

The contract grants no:

- VA authority;
- representation authority;
- medical-opinion authority;
- adjudication authority;
- rating authority;
- signature authority;
- submission authority;
- provider-output authority;
- execution authority from custody.

It does not activate a runtime, document upload, or filing transport.

## Machine-owned validation

```text
workflow: .github/workflows/va-claims-chat-runtime-contract.yml
trigger: owned-path push, every six hours, or workflow dispatch
input: contracts/va-claims-chat-runtime.json
output: receipts/va-claims-chat-runtime-contract-validation.json
current result: PASS
```

## Integration obligations

The active adapter implementation lane must implement generators route by route. Each route remains fail-closed until it has:

1. admitted source contract;
2. deterministic fixtures;
3. hash-bound validation receipt;
4. TVC readiness and invocation evidence;
5. Master Records custody `RECORDED` and reconstruction `PASS`;
6. deployed secret-free request evidence;
7. exact Site capability projection.

`document_organization` additionally requires sanitized derived context from `StegVerse-Labs/Site#116`; the adapter must not receive raw veteran documents.

The filing state may not advance beyond preparation until every gate in `filing_boundary.required_before_filing_ready` verifies and an authorized VA or accredited-representative transport exists.

## Transfer

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
```

Transferred requirements:

- governed Claims Chat runtime state model;
- complete route activation requirements;
- document-context boundary;
- filing authority boundary;
- Site projection contract;
- release evidence required for each route.

Continuation owner: the active, nonexpired adapter implementation claim recorded in `docs/VA_CLAIM_ASSISTANT_GOVERNED_RETRIEVAL_HANDOFF.md`.

## Archive conditions

This subordinate contract task is archive-safe. Its complete state is committed in the contract, PASS receipt, workflow, issue comment, and this handoff. No chat history is required for continuation.

The broader session remains active while governed route generators, substantive document execution, filing integration, deployed surface observation, and Ecosystem Chat activation remain incomplete.

## Percentages

```text
developed files: 5/5
validation: 1/1 PASS
integration: transferred to active adapter implementation lane
activation: 0 percent; contract grants no activation
```
