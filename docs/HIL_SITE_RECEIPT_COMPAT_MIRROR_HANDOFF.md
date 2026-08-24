# HIL Site Receipt Compatibility Mirror Handoff

## Source of truth

```text
goal_id: LLMA-HIL-SITE-RECEIPT-COMPAT-030
issue: StegVerse-org/LLM-adapter#194
parent_handoff: docs/HIL_RUNTIME_MIRROR_HANDOFF.md
site_contract_source: StegVerse-Labs/Site/assets/hil-direct-upload-v1.js
credential_authority: TV/TVC
github_token_runtime_authority: NONE
participant_machine_required: false
developer_machine_required: false
third_party_runtime_required: false
state: COMPLETE_MERGED_VALIDATED_RELEASED
pull_request: #195
validated_head: 9327370d7db2241535499dfc0fa30aeaba66650f
merge: 9928284a2abf229dd7c7c19eae75eb9838024e43
hil_site_receipt_compat_run: 32735122756 SUCCESS
hil_sovereign_receiver_source_run: 32735122701 SUCCESS
repository_validation_run: 32735122719 SUCCESS
```

The current Site durable-ingress browser predicate requires a successful `HIL-RECEIVER-RECEIPT-v2` to carry both `custody_state: EXACT_BYTES_PERSISTED` and `registry_state: RECORDED`.

The receiver previously persisted the PDF and SQLite submission row but returned the narrower legacy custody label `GATEWAY_EXACT_BYTES_PRESERVED` and omitted `registry_state`. That shape would cause the current Site client to reject an otherwise successful governed submission as `ingress_custody_not_durable`.

## Installed repair

The receiver now asserts durable state only after:

```text
PDF bytes written to the admitted HIL originals path
+ provenance written
+ SQLite submission INSERT committed
+ submission row independently re-read
+ persisted hash/path identity rechecked
```

Only after those predicates pass does the receipt report:

```text
custody_state: EXACT_BYTES_PERSISTED
registry_state: RECORDED
```

The public privacy-bounded submission status surface reports the same durable state while still exposing no participant identifier, publication consent, review notes, storage paths, provenance content, or PDF bytes.

The regression test mirrors the current Site browser durable-ingress acceptance predicate, including the exact Primary/prompt hashes and the two durable-state fields. The dedicated credential-free HIL compatibility workflow, the sovereign-receiver source workflow, and the full credential-free repository validation all passed on the exact PR head before merge.

## Authority boundary

This compatibility repair does not grant acceptance, review, publication, Master Records append, lifecycle, route, or execution authority. It mints no new credential/token and does not make GitHub, participant hardware, developer hardware, Render, or another third-party runtime production authority.

## Continuation

This source/interface defect is closed. The next HIL backend evidence remains the real runtime chain:

```text
resident WorkerCoordinator HIL invocation
-> ACTIVE_SOVEREIGN_RECEIVER
-> READY
-> public HTTPS rendezvous
-> controlled Site browser submission
-> durable HIL-RECEIVER-RECEIPT-v2
-> receiver restart/replacement
-> TV/TVC-authenticated exact-byte reconstruction with original SHA-256
-> existing TVC lifecycle handoff
```

Source/CI compatibility is not itself live browser submission, public HTTPS activation, receiver restart proof, or TVC lifecycle completion.
