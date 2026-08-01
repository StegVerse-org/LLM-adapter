# VA Claim Assistant Governed Retrieval — Adapter Handoff

## State

```text
program: VA Claim Assistant governed session layer
state: BUILDING
public activation: NOT AUTHORIZED
adapter issue: #90
site parent issue: StegVerse-Labs/Site#113
site source/provenance issue: StegVerse-Labs/Site#115
tvc capability issue: StegVerse-Labs/TVC#9
master-records custody issue: master-records/orchestration#12
```

## Inputs owned by Site

- `StegVerse-Labs/Site/data/va-claim-assistant/source-registry.json`
- `StegVerse-Labs/Site/data/va-claim-assistant/source-registry.schema.json`
- `StegVerse-Labs/Site/data/va-claim-assistant/answer-record.schema.json`
- `StegVerse-Labs/Site/scripts/check_va_claim_assistant_governance.py`

The adapter must consume commit-pinned copies or immutable references. It must not silently fork the authority taxonomy or answer contract.

## Required pipeline

1. Classify the question into one governed VA route.
2. Resolve the current Site source-registry version.
3. Retrieve only admitted sources.
4. Preserve source authority class, effective date, retrieval time, supersession state, and proposition locator.
5. Keep controlling authority above official operational guidance, professional support, and experiential material.
6. Separate source fact, user-record fact, inference, contradiction, uncertainty, and procedural guidance.
7. Apply refusal and referral gates.
8. Request the named TVC capability rather than loading repository-local provider credentials.
9. Produce a secret-free answer record conforming to the Site schema.
10. Submit the answer record to Master Records custody and return the custody/reconstruction references.

## Required VA routes

- claim_type
- evidence_requirement
- service_connection
- rating_criteria
- effective_date
- appeal_or_supplemental_claim
- cp_examination
- document_organization
- lay_statement
- private_record_collection
- procedural_filing
- representation_referral
- urgent_safety

## Mandatory fail-closed rules

The adapter must refuse or stop when:

- no admitted source supports a material source proposition;
- a lower authority source conflicts with controlling authority;
- a controlling source is stale, superseded, or unresolved;
- a requested answer would invent a diagnosis, nexus, event, symptom, record, or rating result;
- a user asks for a guaranteed outcome or percentage targeting;
- TVC returns unavailable, unauthorized, revoked, expired, or incompatible capability status;
- custody or reconstruction cannot preserve the final receipt.

Missing repository-local credentials mean `AUTHORITY_RESOLUTION_REQUIRED`, not `BLOCKED`, until TVC resolution has been attempted.

## Minimal implementation slice

The first adapter slice should support a single public-source question without private documents:

- route: `evidence_requirement`
- admitted sources: official VA evidence guidance plus controlling statute or regulation when applicable
- output: one schema-valid answer record with proposition-level citations
- authority flags: all false
- TVC: secret-free capability/readiness or execution receipt
- Master Records: custody `RECORDED` and reconstruction `PASS`

This slice may establish `SOURCE_GROUNDED_ASSISTANT` after deployed verification. It does not establish `DOCUMENT_AWARE_ASSISTANT` or `GOVERNED_CLAIM_SESSION`.

## Exit evidence

Issue #90 may close only after one deployed request produces:

- deterministic route classification;
- admitted and authority-ranked citations;
- schema-valid answer record;
- no unsupported propositions;
- all authority flags false;
- TVC execution/readiness receipt;
- Master Records custody and reconstruction references;
- stable final receipt hash;
- Site projection that does not overstate the capability.
