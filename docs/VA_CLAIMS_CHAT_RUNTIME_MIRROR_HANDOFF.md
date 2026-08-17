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

The active governed-retrieval/runtime implementation remains the canonical owner. This subordinate contract task owns only the runtime contract, fail-closed validator, retained receipt, and this handoff. Workflow-maintenance claim `LLMA-WORKFLOW-CONSOLIDATE-VA-RUNTIME-CONTRACT-048` changed only deterministic validation transport and is now released.

## Released contract

```text
claim state: RELEASED_COMPLETE
role: INTEGRATION_CONTRACT
validation evidence: receipts/va-claims-chat-runtime-contract-validation.json
collision boundary: no generator, classifier, dispatcher, provider, custody, deployment, filing transport, Site mutation, wallet action, or activation authority
```

The contract establishes all thirteen governed VA routes, route-specific generator/source requirements, source/user-record/inference/contradiction/uncertainty/referral/custody/reconstruction fields, raw-document rejection, sanitized-derived-context acceptance from Site#116, staged capability states, veteran-retained submission authority, automated filing inactive, explicit filing gates, fail-closed runtime states, and receipt-derived Site projection.

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

The committed canonical PASS receipt remains release evidence. `scripts/validate_va_claims_chat_runtime_contract.py` remains the authoritative fail-closed validator and writes a deterministic receipt only into the current workspace when invoked.

## Validation transport consolidation — RELEASED

The retired standalone `.github/workflows/va-claims-chat-runtime-contract.yml` previously had a six-hour schedule, `contents: write`, token-backed checkout with persisted credentials, repository commit/pull/push writeback, and artifact upload.

It is now removed. Deterministic validation continues through:

```text
.github/workflows/validate.yml
  -> permissions: {}
  -> anonymous exact-SHA source acquisition
  -> explicit credential refusal
  -> no schedule/writeback/artifact transport
  -> scripts/verify_goal4_full.py
scripts/verify_goal4_full.py
  -> scripts/validate_va_claims_chat_runtime_contract.py
iosnoperiod/github/workflows/validate.yml
  -> exact mirror invokes the same Goal 4 aggregate
```

Release evidence:

```text
cleanup claim: LLMA-WORKFLOW-CONSOLIDATE-VA-RUNTIME-CONTRACT-048
cleanup PR: #171
final head: 6da12cb2562a76540fdb5d39faa0fc70e082bd60
merge: b3a17c81d89d2cc8a69497d4d0a277788389bc8b
Architecture Guard: 31987117708 SUCCESS
validate: 31987118201 SUCCESS
validate job: 95263934427 SUCCESS
67/67 substantive validate steps: SUCCESS
canonical Goal 4: SUCCESS including runtime-contract validator
workflow parity: SUCCESS
validation-only authority boundary: SUCCESS
post-merge workflow files: 11
claim 048: MERGED_INTO_CANONICAL_WORKSTREAM
```

## Authority boundary

The contract grants no VA, representation, medical-opinion, adjudication, rating, signature, submission, provider-output, custody-derived execution, filing, publication, wallet, or runtime activation authority. Contract validation does not activate a runtime, document upload path, or filing transport.

## Integration obligations

The active adapter implementation lane must implement generators route by route. Each route remains fail-closed until it has admitted source contract, deterministic fixtures, hash-bound receipt, TVC readiness/invocation evidence, Master Records custody `RECORDED` and reconstruction `PASS`, deployed secret-free request evidence, and exact Site capability projection. `document_organization` additionally requires sanitized derived context from Site#116; raw veteran documents must not enter this adapter.

The filing state may not advance beyond preparation until every gate in `filing_boundary.required_before_filing_ready` verifies and an authorized VA or accredited-representative transport exists.

## Transfer

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
```

Continuation owner remains the governed-retrieval/runtime lane. Broader VACC activation remains machine-owned/incomplete.

## Archive conditions

The originating subordinate runtime-contract task remains archive-safe and the workflow-cleanup claim is released. No chat history is required for this contract's continuation.
