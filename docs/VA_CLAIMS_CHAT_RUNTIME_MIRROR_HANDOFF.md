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

The active governed-retrieval implementation owns `va_claim_assistant/**`, its tests, and `.github/workflows/va-claim-assistant-governed-retrieval.yml`. This subordinate contract task owns only the runtime contract, its fail-closed validator and retained receipt, and this handoff. Workflow-maintenance claim `LLMA-WORKFLOW-CONSOLIDATE-VA-RUNTIME-CONTRACT-048` may alter only how deterministic validation is invoked; it does not seize runtime ownership.

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

The retained canonical receipt remains release evidence. `scripts/validate_va_claims_chat_runtime_contract.py` remains the authoritative fail-closed validator and writes its deterministic receipt into the local workspace when invoked.

## Current validation carrier

The historical standalone `.github/workflows/va-claims-chat-runtime-contract.yml` had a six-hour schedule, `contents: write`, token-backed `actions/checkout@v4` with persisted credentials, repository commit/pull/push writeback, and `actions/upload-artifact@v4`. That recurring GitHub surface is being consolidated under claim `LLMA-WORKFLOW-CONSOLIDATE-VA-RUNTIME-CONTRACT-048`.

Current deterministic path on the cleanup branch:

```text
.github/workflows/validate.yml
  -> permissions: {}
  -> anonymous exact-SHA source acquisition
  -> explicit credential refusal
  -> no schedule
  -> no repository writeback
  -> no artifact transport
  -> executes scripts/verify_goal4_full.py
scripts/verify_goal4_full.py
  -> executes scripts/validate_va_claims_chat_runtime_contract.py
```

The exact iOS global workflow mirror already invokes the same Goal 4 aggregate, so no separate mirror-only contract step or second dispatcher is required. Receipt generation during hosted validation is workspace-local; the committed PASS receipt is not rewritten by GitHub Actions.

## Authority boundary

The contract grants no VA, representation, medical-opinion, adjudication, rating, signature, submission, provider-output, custody-derived execution, filing, publication, wallet, or runtime activation authority. Contract validation does not activate a runtime, document upload path, or filing transport.

## Integration obligations

The active adapter implementation lane must implement generators route by route. Each route remains fail-closed until it has admitted source contract, deterministic fixtures, hash-bound receipt, TVC readiness/invocation evidence, Master Records custody `RECORDED` and reconstruction `PASS`, deployed secret-free request evidence, and exact Site capability projection. `document_organization` additionally requires sanitized derived context from Site#116; raw veteran documents must not enter this adapter.

The filing state may not advance beyond preparation until every gate in `filing_boundary.required_before_filing_ready` verifies and an authorized VA or accredited-representative transport exists.

## Transfer

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
```

Continuation owner remains the active governed-retrieval/runtime implementation lane; this workflow cleanup creates no competing owner.

## Archive conditions

The originating subordinate runtime-contract task remains archive-safe: its complete state is committed in the contract, retained PASS receipt, issue state, and this handoff. Broader VACC activation remains machine-owned/incomplete.

Workflow cleanup claim 048 is not complete until exact-head Architecture Guard/global validate pass, PR merge, post-merge census, claim release, and canonical workflow handoff finalization.
