# Governed Wiki Publication Transition Mirror Handoff

Status: ACTIVE — SOURCE MERGED / AUTHENTIC RUNTIME DECISION NOT YET OBSERVED
Goal Task ID: `GOVERNED-WIKI-PUBLICATION-TRANSITION-001`
COSV ID: NOT ESTABLISHED IN CANONICAL TASK REGISTRY

## Canonical predecessors

- SDK reviewed-candidate binding merged in StegVerse-SDK PR #307 as `e025175f1c2e5ec4bd9c91d8ab093200f28f856c`.
- SDK authoritative Interlock/InTr posture-request binding merged in PR #308 as `ecccfb511c6baf012c33ea27aa8e747dfe482273`.
- The existing External Chat review store retains the cooperative review package, correction receipt, and `external_framework_wiki_publication_transition`.
- The existing LLM-adapter Service Gateway already owns TV/TVC-materialized transport of the Master Records recorder service URL and token, used only for optional downstream recording.
- The organization holds the canonical state-transition receipt of each transition (custody stays with the organization ledger). Master Records (`master-records/orchestration`) is the downstream recorder of released organization batch receipts; it cannot create, admit, authorize, infer or repair a transition and nothing awaits it.

## This seam

A publication candidate may progress toward repository mutation only when all of the following are bound to the same identity:

1. exact stored publication-transition object and SHA-256;
2. exact SDK ingress manifest whose payload is that transition;
3. exact SDK governed result with `governance_state=ALLOW`;
4. authoritative Interlock/InTr posture binding for task `GOVERNED-WIKI-PUBLICATION-TRANSITION-001`;
5. separately observed external Interlock/InTr ingress decision with `disposition=ALLOW`, exact transition-request hash, receipt hash, carrier reference, and no locally generated allow;
6. the organization's canonical publication state-transition receipt (`stegverse.canonical-state-transition-receipt/v1`), carried with the mutation request;
7. local verification of that receipt: exact canonical digest equality with `transition_receipt_sha256`, every required-evidence item digest-valid, and `master_records_may_grant_transition_authority=false`.

The SDK posture binding is not itself re-labeled as an ALLOW decision.

## Optional downstream Master Records recording

`record_governed_publication_closure(...)` may hand the released organization receipt downstream to Master Records for cross-organization reconstruction. It reuses the same server-side `STEGVERSE_MASTER_RECORDS_ENDPOINT`, `STEGVERSE_MASTER_RECORDS_TOKEN`, timeout, host allowlist, and TV/TVC materialization semantics already used by the Service Gateway StegBrowser relay, against `master-records/orchestration /api/master-records/state-transitions`. This recording is optional and never gates the publication: an unconfigured recorder, a failed write or a failed reconstruction returns `state=NOT_RECORDED` data carrying `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal` and `next_attempt`, with `gates_publication=false`, instead of raising. Invalid transition evidence still raises, because no organization receipt exists. It creates no second record database, alternate ledger, or credential path.

## Mutation gate

The existing `/api/external-review/repository-mutations` request carries the organization's publication transition receipt (`transition_receipt`) and its canonical digest (`transition_receipt_sha256`; the legacy field `master_records_receipt_sha256` is accepted as the same digest, never as a Master Records lookup, and exactly one digest is required). Before any GitHub read/write, the adapter verifies that receipt locally with `verify_publication_transition_receipt(...)`; no Master Records reconstruction or reply is consulted or awaited. It requires:

- publication transition decision `ALLOW_PUBLICATION_CANDIDATE`;
- canonical transition outcome `ALLOW`;
- exact publication-transition ID and SHA-256 binding;
- exact target repository/path binding;
- external Interlock/InTr `ALLOW` origin and `locally_generated_allow=false`;
- every required-evidence manifest item digest-valid;
- exact canonical digest of `transition_receipt` equal to `transition_receipt_sha256`.

A verification failure is HTTP 409 `DENY` carrying `failure_code`, `failed_predicate=organization_publication_transition_receipt_verified`, `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal` and `next_attempt`, with `repository_mutation_performed=false`. The mutation health surface reports `closes_on=ORGANIZATION_TRANSITION_RECEIPT` and `master_records_gates_mutation=false`.

`DENY_PUBLICATION` and `REVIEW_REQUIRED` stop before custody/mutation consequence and produce zero repository mutation.

## Authority boundaries

- submitter direct repository mutation authority: false
- publication candidate grants publication authority: false
- SDK manifest grants publication authority: false
- LLM-adapter does not generate Interlock/InTr ALLOW
- Master Records grants no transition/publication authority and does not gate the mutation
- mutation adapter remains consequence-only and requires exact predecessor closure
- no new runtime, scheduler, dispatcher, WorkerCoordinator, custody store, authority plane, credential path, or device prerequisite

## Completion truth

Source/CI success is not authentic publication completion. End-to-end completion requires an authentic retained Interlock/InTr ALLOW (Interlock/InTr admits the publication transition), the organization's publication transition receipt of that decision, and a resulting Publisher/repository mutation receipt for an admitted publication candidate. Non-ALLOW negative controls must retain zero mutation. Downstream Master Records recording is not a completion predicate.


## Source implementation — current branch

`llm_adapter/wiki_publication_master_records.py` validates exact publication-transition/SDK-manifest identity, requires posture-bound SDK execution plus a separately observed external Interlock/InTr `ALLOW`, and builds the organization's `PUBLIC_WIKI_GOVERNED_PUBLICATION_DECISION` state-transition receipt (`build_publication_state_receipt`). `verify_publication_transition_receipt(...)` verifies that receipt locally. `record_governed_publication_closure(...)` is optional, non-gating downstream recording of the released receipt into Master Records.

`llm_adapter/external_publication_mutation.py` requires `transition_receipt` plus one canonical digest and verifies it locally before any GitHub operation. The receipt must bind the same publication transition, target repository/path, external InTr ALLOW, and exact digest equality. Non-ALLOW publication transitions remain rejected before closure or mutation consequence.

Under #368 (companion runtime PR #380) the earlier pre-GitHub Master Records reconstruction gate (`require_publication_master_records_organization_record`, which made `master_records_receipt_sha256` a mandatory reconstruction lookup) was retired; the mutation closes on the organization receipt.


## Source merge and authentic caller boundary

LLM-adapter PR #348 merged to `main` as `9e21949926b4f082e93fbf4087f8e3c9ac2b2f09` after all eight exact-head workflows succeeded.

The merged source, as amended by companion runtime PR #380 under #368, contains the organization-receipt builder, the local pre-GitHub receipt verification and the optional downstream recorder; `record_governed_publication_closure(...)` has no production caller on current `main`, and none is required for mutation.

The traced existing chain is:

```text
Site External Chat compatibility
-> cooperative review package
-> delegated correction receipt
-> LLM-adapter create_publication_transition(...)
-> stored external_framework_wiki_publication_transition
-> [FIRST AUTHENTIC CALLER BOUNDARY]
-> SDK prepare_wiki_publication_manifest(...)
-> existing SDK governed execution
-> authoritative Interlock/InTr posture binding
-> separately observed external Interlock/InTr ALLOW
-> organization publication transition receipt (build_publication_state_receipt)
-> existing repository-mutation endpoint (transition_receipt verified locally)
   (downstream, non-gating: record_governed_publication_closure(...) may record the released receipt in Master Records)
```

Current Site reviewer UI stops after correction. Current LLM-adapter records publication transitions but does not invoke the SDK publication converter or SDK execution path. No LLM-adapter source on `main` imports or calls `prepare_wiki_publication_manifest(...)` or `run_external_framework(...)`.

Therefore the next caller must be attached only to an existing execution surface that actually possesses both:

1. the exact SDK run artifact for this stored publication transition; and
2. a separately observed external Interlock/InTr ingress decision whose `disposition=ALLOW`, `authority=Interlock/InTr`, request hash equals the SDK transition-request hash, transition identity matches the SDK request, a valid ingress receipt hash exists, and `locally_generated_allow=false`.

The SDK posture binding alone is not that decision and must never be promoted to ALLOW.

## Runtime evidence state

Repository searches across the canonical task, SDK, LLM-adapter, StegVerse-Labs control-plane surfaces, and master-records did not find a retained authentic external Interlock/InTr ALLOW or a retained `PUBLIC_WIKI_GOVERNED_PUBLICATION_DECISION` closure for this task.

Current runtime state:

```text
AUTHENTIC_EXTERNAL_INTR_ALLOW = UNKNOWN_NOT_AUTHENTICALLY_OBSERVED
PUBLIC_WIKI_GOVERNED_PUBLICATION_DECISION_ORGANIZATION_TRANSITION_RECEIPT = UNKNOWN_NOT_AUTHENTICALLY_OBSERVED
REPOSITORY_MUTATION_FROM_GOVERNED_CLOSURE = UNKNOWN_NOT_AUTHENTICALLY_OBSERVED
```

Absence is not interpreted as DENY or execution failure. No synthetic ALLOW, locally manufactured closure, direct submitter write, or alternate runtime/custody path is authorized.


## Existing Interlock/InTr decision-surface trace

The first unsatisfied predicate remains:

```text
AUTHENTIC_EXTERNAL_INTR_ALLOW = UNKNOWN_NOT_AUTHENTICALLY_OBSERVED
```

A bounded trace of existing InTr surfaces found two materially different contracts:

1. **Universal InTr materialization ingress** — the existing shared Service Gateway forwards `/intr/materialization` to the existing sovereign Universal InTr listener. The canonical-work and device-local ingress implementations validate the exact request hash and retain write-once `INGRESS_ADMITTED` receipts. Their authority effect is ingress-transition/admission only. Those receipts do not contain the required publication decision contract: no `disposition=ALLOW`, no `authority=Interlock/InTr`, and no explicit `locally_generated_allow=false`. Therefore `INGRESS_ADMITTED` cannot be promoted to the publication-governance ALLOW required by `build_publication_state_receipt(...)`.

2. **Provider-specific InTr transport verification** — `llm_adapter/anthropic_intr_transport.py` defines an `IngressDecision` with the needed `disposition`, `request_hash`, `transition_id`, `ingress_receipt_hash`, `carrier_ref`, and `authority=Interlock/InTr` shape, and its durable verification explicitly records `locally_generated_allow=false`. However, this code only verifies an externally supplied decision for the Anthropic provider transport; it does not obtain that decision from a generic InTr authority service and is bound to the Anthropic request/endpoint contract. `anthropic_convergence_bridge.py` likewise constructs a provider-specific verification envelope from caller-supplied ingress fields. It is not a generic publication-governance decision surface.

The existing SDK `resolve_task_security_posture(...)` surface remains posture resolution only. Its exact `transition_request_sha256` binding is necessary but is not a governance ALLOW.

### Result

No existing source surface was found that both:

- consumes the exact SDK transition request for a stored `external_framework_wiki_publication_transition`; and
- returns an externally authoritative decision with all of:
  - `disposition=ALLOW`
  - exact `request_hash`
  - exact `transition_id`
  - valid `ingress_receipt_hash`
  - nonempty `carrier_ref`
  - `authority=Interlock/InTr`
  - `locally_generated_allow=false`

Therefore no caller is connected between `create_publication_transition(...)` and the SDK publication execution path in this pass. No runtime, scheduler, dispatcher, WorkerCoordinator, custody, credential, mutation, or authority surface is changed.

The next progression condition is authentic retained evidence from an already-existing Interlock/InTr decision surface that satisfies the exact decision contract above. Until then, absence remains `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED`, not DENY, failure, or authorization.
