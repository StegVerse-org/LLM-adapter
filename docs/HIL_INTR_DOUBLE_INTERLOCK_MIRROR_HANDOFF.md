# HIL InTr Double-Interlock Mirror Handoff

Updated: 2026-08-29

```text
goal_id: LLMA-HIL-INTR-DOUBLE-INTERLOCK-031
issue: StegVerse-org/LLM-adapter#212
repository: StegVerse-org/LLM-adapter
branch: fix/hil-intr-double-interlock-20260829
state: IMPLEMENTED_ON_BRANCH_CI_PENDING
credential_authority: TV/TVC
github_token_runtime_authority: NONE
always_on_receiver_required: false
participant_second_machine_required: false
third_party_runtime_required: false
runtime_activation: false
tvc_admission: false
```

## Corrected runtime contract

The participant action is the beginning of the transport transaction. Receiver readiness is not a precondition for the browser to begin the governed upload.

```text
Submit
-> browser creates stegverse.hil.intr_ingress_envelope/v1
-> InTr transport attempt begins immediately
-> receiving boundary validates exact PDF + canonical provenance hashes
-> receiver issues stegverse.intr.hop_receipt/v1
     DEVICE -> HIL_INGRESS
-> exact bytes/provenance persist + read back
-> receiver issues second hop receipt
     HIL_INGRESS -> HIL_CUSTODY
     prior_receipt_hash = first receipt hash
-> receiver persists stegverse.hil.intr_egress_envelope/v1
     HIL_CUSTODY -> TVC_HIL_LIFECYCLE
     prior_receipt_hash = custody receipt hash
-> TVC validates the upstream chain and issues the next receipt only after actual admission
```

The browser does not self-issue a receiver receipt. The receiver does not self-issue a TVC receipt.

## Idempotency

The ingress operation id and envelope hash are persisted with the submission. A retry of the exact same operation/envelope returns the original persisted receiver receipt. Reusing an operation id with a different envelope fails closed. This permits automatic continuation after an ambiguous HTTP outcome without duplicate custody.

## Persistent evidence

A successful receiver transaction persists:

- exact response PDF;
- canonical provenance manifest;
- ingress operation/envelope identity;
- DEVICE->HIL_INGRESS receipt;
- HIL_INGRESS->HIL_CUSTODY receipt;
- TVC-bound egress Interlock envelope;
- complete receipt-chain object;
- HIL-RECEIVER-RECEIPT-v2.

Public status may expose the non-sensitive chain hash and next transition, but not the artifact bytes or private metadata.

## Downstream boundary

The receiver egress envelope is only `READY_FOR_INTERLOCK_ADMISSION`. Existing TVC HIL lifecycle authority remains the next subsystem. TVC must validate the receipt chain and exact artifact identity before producing its own admission/custody evidence. Private review, publication, Master Records, and release remain separate authorities.

## Non-claims

CI/source merge does not prove a live InTr hop, runtime materialization, public transport, TVC admission, private review, publication, or Master Records release.
