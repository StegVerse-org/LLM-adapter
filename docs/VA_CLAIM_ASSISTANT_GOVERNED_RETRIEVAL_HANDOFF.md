# VA Claim Assistant Governed Retrieval — Adapter Handoff

## Identity

```text
program: VA Claim Assistant governed session layer
goal_id: VACP-ADAPTER-GOVERNED-ROUTES
repository: StegVerse-org/LLM-adapter
canonical_issue: StegVerse-org/LLM-adapter#90
current_sovereign_correction_issue: StegVerse-org/LLM-adapter#142
current_sovereign_task: tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
site_parent_issue: StegVerse-Labs/Site#113
four_app_issue: StegVerse-Labs/Site#241
site_document_issue: StegVerse-Labs/Site#116
master_records_issue: master-records/orchestration#15
credential_authority: TV/TVC
github_token_runtime_authority: NONE
public_activation: NOT_AUTHORIZED_BY_THIS_SLICE
```

## Source of truth

The adapter consumes, and does not silently fork, the Site VA source registry and answer-record schema, TVC service-connection admission, and canonical StegGate runtime identity owned by `StegVerse-Labs/StegCore`.

Canonical StegGate identity remains:

```text
contract_version: stegverse.steggate.runtime-identity.v1
runtime_identity: stegverse:steggate:canonical:three-layer:v1
canonical_owner: StegVerse-Labs/StegCore
canonical_admissibility_runtime: stegcore.three_layer.evaluate_three_layer
transport_identity_authoritative: false
application_specific_policy_authority: false
```

## Released implementation

The route implementation remains released and complete at source level:

- thirteen deterministic governed routes;
- urgent safety fails closed pending admitted official source;
- public-source generators remain bounded;
- document organization accepts only sanitized derived context;
- raw documents and direct identifiers are rejected;
- governed retrieval remains classifier-first;
- provider/model execution is not inferred from deterministic route success;
- service-connection execution observation remains fail closed.

The observer `scripts/observe_va_service_connection_execution.py` remains authoritative for execution-readiness state. Absent real execution evidence produces `BLOCKED`; invalid evidence produces `REVIEW_REQUIRED`; only schema-valid TVC-bound evidence may produce `COMPLETE` and `READY_FOR_MASTER_RECORDS`.

## Historical hosted evidence

Historical workflow run `31339681257`, job `93311292315`, artifact `9045428133`, and its digest remain release provenance only. They proved CI identity binding and deterministic route/observer behavior at that time. They did not prove real provider execution or public activation.

## Workflow consolidation

Cleanup claim: `tasks/LLMA-WORKFLOW-CONSOLIDATE-VA-GOVERNED-RETRIEVAL-050.json`.

The historical `.github/workflows/va-claim-assistant-governed-retrieval.yml` combined two different responsibilities:

1. deterministic source/route/dispatch/observer validation; and
2. recurring GitHub-hosted observation with `contents: write`, token-backed checkout/setup, receipt writeback, and artifact transport.

Under claim 050 the deterministic capability is preserved while the hosted lifecycle is removed:

```text
.github/workflows/va-claim-assistant-governed-retrieval.yml
  -> CONSOLIDATED/TRANSFERRED
  -> removed
scripts/verify_goal4_full.py
  -> executes route-classifier fixture
  -> executes route-generator fixture
  -> executes governed-retrieval fixture
  -> executes governed-dispatch fixture
  -> executes service-connection observer
  -> executes scripts/validate_va_claim_assistant_governed_retrieval_receipts.py
scripts/validate_va_claim_assistant_governed_retrieval_receipts.py
  -> preserves the former inline hash/route/identity/readiness assertions
pyproject.toml dev dependency set
  -> includes canonical StegCore pinned to 8c484e584d60a3bd2763d6948d0eb3f4afd67e0c
  -> anonymous source dependency; no GitHub credential is required by the validation path
```

The canonical global `validate.yml` remains `permissions: {}`, explicitly refuses credential-bearing environment variables, acquires the exact source anonymously, performs no schedule, writeback, artifact upload, hosted activation, or runtime/control-plane action, and executes canonical Goal 4. Its exact iOS workflow mirror remains the same validation carrier.

## Current machine-owned live continuation

Live VACC provider execution/observation is not owned by GitHub Actions. Canonical continuation is:

```text
StegVerse-Labs/.github resident sovereign heartbeat
-> StegVerse-Labs/TVC route authority
-> StegVerse-org/LLM-adapter#142
-> tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
-> scripts/observe_va_service_connection_execution.py
-> master-records/orchestration#15
-> StegVerse-Labs/Site#113/#241 after immutable evidence
```

Credential rules:

```text
credential_authority: TV/TVC
credential_requirement: NONE for the admitted sovereign local-model route
github_token_required: false
github_token_runtime_authority: NONE
non-TV/TVC secrets or tokens: PROHIBITED
hosted provider fallback: DISALLOWED
third_party_runtime_authority: NONE
```

## Machine-observable release condition for live activation

The live lane remains incomplete until a resident sovereign worker produces real service-connection execution evidence through the admitted TVC capability and canonical StegGate identity, the observer transitions to `COMPLETE`, Master Records returns custody `RECORDED` plus reconstruction `PASS`, and Site projects only the immutable verified capability. Missing execution evidence must remain `BLOCKED`.

## Exact remaining product tasks

- issue #142/task 023: sovereign VACC provider execution through TVC;
- `master-records/orchestration#15`: custody and reconstruction of genuine execution/privacy events;
- `StegVerse-Labs/Site#113/#241`: receipt-derived deployed capability projection;
- `StegVerse-Labs/Site#116`: production PII detection/redaction/model-leakage and substantive document evidence;
- admitted current `VA-CRISIS-LINE` source or continued urgent-safety fail-closed posture;
- veteran-authorized filing transport with revocation, duplicate prevention, confirmation and custody before filing can activate.

## Authority boundary

```text
deterministic validation != provider execution
canonical runtime identity != provider execution
TVC admission != provider execution
provider execution != claim authority
custody != execution
reconstruction != filing authority
receipt verification != signature/submission
GitHub workflow success != governed activation
```

## Consolidation

```text
MERGED INTO: StegVerse-org/LLM-adapter#90
MERGED INTO: StegVerse-org/LLM-adapter#142
MERGED INTO: StegVerse-org/LLM-adapter/tasks/VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023.json
MERGED INTO: StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md
MERGED INTO: StegVerse-Labs/TVC
MERGED INTO: master-records/orchestration#15
MERGED INTO: StegVerse-Labs/Site#113/#241
MERGED INTO: StegVerse-Labs/Site#116
```

The source implementation remains complete. Claim 050 is not released until exact-head Architecture Guard/global validate pass, PR merge, post-merge workflow census, claim release, and canonical workflow handoff finalization.
