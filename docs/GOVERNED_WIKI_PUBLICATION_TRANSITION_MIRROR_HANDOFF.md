# Governed Wiki Publication Transition Mirror Handoff

Status: ACTIVE — SOURCE MERGED / AUTHENTIC RUNTIME DECISION NOT YET OBSERVED
Goal Task ID: `GOVERNED-WIKI-PUBLICATION-TRANSITION-001`
COSV ID: NOT ESTABLISHED IN CANONICAL TASK REGISTRY

## Canonical predecessors

- SDK reviewed-candidate binding merged in StegVerse-SDK PR #307 as `e025175f1c2e5ec4bd9c91d8ab093200f28f856c`.
- SDK authoritative Interlock/InTr posture-request binding merged in PR #308 as `ecccfb511c6baf012c33ea27aa8e747dfe482273`.
- The existing External Chat review store retains the cooperative review package, correction receipt, and `external_framework_wiki_publication_transition`.
- The existing LLM-adapter Service Gateway already owns TV/TVC-materialized canonical Master Records endpoint/token transport.
- Canonical state-transition custody remains solely in `master-records/orchestration`.

## This seam

A publication candidate may progress toward repository mutation only when all of the following are bound to the same identity:

1. exact stored publication-transition object and SHA-256;
2. exact SDK ingress manifest whose payload is that transition;
3. exact SDK governed result with `governance_state=ALLOW`;
4. authoritative Interlock/InTr posture binding for task `GOVERNED-WIKI-PUBLICATION-TRANSITION-001`;
5. separately observed external Interlock/InTr ingress decision with `disposition=ALLOW`, exact transition-request hash, receipt hash, carrier reference, and no locally generated allow;
6. canonical Master Records state-transition receipt;
7. retained reconstruction with `state=PASS`, required-evidence validation `PASS`, and exact receipt/reconstruction digest equality.

The SDK posture binding is not itself re-labeled as an ALLOW decision.

## Master Records transport

The implementation reuses the same server-side `STEGVERSE_MASTER_RECORDS_ENDPOINT`, `STEGVERSE_MASTER_RECORDS_TOKEN`, timeout, host allowlist, and TV/TVC materialization semantics already used by the Service Gateway StegBrowser relay. It submits to and reconstructs from the existing `master-records/orchestration /api/master-records/state-transitions` authority. It creates no custody database, alternate ledger, or credential path.

## Mutation gate

The existing `/api/external-review/repository-mutations` request must carry only the canonical Master Records receipt SHA-256. Before any GitHub read/write, the adapter reconstructs that receipt from Master Records and requires:

- publication transition decision `ALLOW_PUBLICATION_CANDIDATE`;
- canonical transition outcome `ALLOW`;
- exact publication-transition ID and SHA-256 binding;
- exact target repository/path binding;
- `required_evidence_validation_status=PASS`;
- exact `receipt_sha256 == reconstructed_receipt_sha256`.

`DENY_PUBLICATION` and `REVIEW_REQUIRED` stop before custody/mutation consequence and produce zero repository mutation.

## Authority boundaries

- submitter direct repository mutation authority: false
- publication candidate grants publication authority: false
- SDK manifest grants publication authority: false
- LLM-adapter does not generate Interlock/InTr ALLOW
- Master Records grants no transition/publication authority
- mutation adapter remains consequence-only and requires exact predecessor closure
- no new runtime, scheduler, dispatcher, WorkerCoordinator, custody store, authority plane, credential path, or device prerequisite

## Completion truth

Source/CI success is not authentic publication completion. End-to-end completion requires an authentic retained Interlock/InTr ALLOW, canonical Master Records closure, and a resulting Publisher/repository mutation receipt for an admitted publication candidate. Non-ALLOW negative controls must retain zero mutation.


## Source implementation — current branch

Added `llm_adapter/wiki_publication_master_records.py` as a non-authorizing client over the existing canonical Master Records transport. It validates exact publication-transition/SDK-manifest identity, requires posture-bound SDK execution plus a separately observed external Interlock/InTr `ALLOW`, records `PUBLIC_WIKI_GOVERNED_PUBLICATION_DECISION`, and rereads the exact retained receipt before returning closure.

Updated `llm_adapter/external_publication_mutation.py` so `master_records_receipt_sha256` is mandatory and is independently reconstructed before any GitHub operation. The reconstructed receipt must bind the same publication transition, target repository/path, external InTr ALLOW, and exact digest equality. Non-ALLOW publication transitions remain rejected before closure or mutation consequence.


## Source merge and authentic caller boundary

LLM-adapter PR #348 merged to `main` as `9e21949926b4f082e93fbf4087f8e3c9ac2b2f09` after all eight exact-head workflows succeeded.

The merged source now contains the canonical custody client and pre-GitHub mutation gate, but `record_governed_publication_closure(...)` has no production caller on current `main`.

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
-> record_governed_publication_closure(...)
-> canonical Master Records reconstruction
-> existing repository-mutation endpoint
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
PUBLIC_WIKI_GOVERNED_PUBLICATION_DECISION_MASTER_RECORDS_CLOSURE = UNKNOWN_NOT_AUTHENTICALLY_OBSERVED
REPOSITORY_MUTATION_FROM_GOVERNED_CLOSURE = UNKNOWN_NOT_AUTHENTICALLY_OBSERVED
```

Absence is not interpreted as DENY or execution failure. No synthetic ALLOW, locally manufactured closure, direct submitter write, or alternate runtime/custody path is authorized.
