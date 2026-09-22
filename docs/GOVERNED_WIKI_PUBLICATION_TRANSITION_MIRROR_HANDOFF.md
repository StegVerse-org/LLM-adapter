# Governed Wiki Publication Transition Mirror Handoff

Status: ACTIVE — CANONICAL CUSTODY + MUTATION GATE SOURCE IMPLEMENTATION
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
