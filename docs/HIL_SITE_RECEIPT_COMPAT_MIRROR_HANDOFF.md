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
state: SOURCE_INSTALLED_VALIDATION_PENDING
```

The current Site durable-ingress browser predicate requires a successful `HIL-RECEIVER-RECEIPT-v2` to carry both:

```text
custody_state: EXACT_BYTES_PERSISTED
registry_state: RECORDED
```

The receiver previously persisted the PDF and SQLite submission row but returned the narrower legacy custody label `GATEWAY_EXACT_BYTES_PRESERVED` and omitted `registry_state`. That shape would cause the current Site client to reject an otherwise successful governed submission as `ingress_custody_not_durable`.

## Bounded repair

The receiver now asserts durable state only after:

```text
PDF bytes written to the admitted HIL originals path
+ provenance written
+ SQLite submission INSERT committed
+ submission row independently re-read
+ persisted hash/path identity rechecked
```

Only after those predicates pass may the receipt report:

```text
custody_state: EXACT_BYTES_PERSISTED
registry_state: RECORDED
```

The public privacy-bounded submission status surface reports the same state, but still exposes no participant identifier, publication consent, review notes, storage paths, provenance content, or PDF bytes.

## Authority boundary

This compatibility repair does not grant acceptance, review, publication, Master Records append, lifecycle, route, or execution authority. It mints no new credential/token and does not make GitHub, participant hardware, developer hardware, Render, or another third-party runtime production authority.

## Validation predicate

```text
receiver unit/integration tests mirror Site durable-ingress acceptance
exact bytes and manifest exist before receipt issuance
registry row can be re-read before RECORDED assertion
receipt custody_state == EXACT_BYTES_PERSISTED
receipt registry_state == RECORDED
public status retains privacy boundary
targeted HIL source validation PASS
full credential-free repository validation PASS
merge to main
```

Source/CI success is not a live browser submission, public HTTPS activation, receiver restart proof, or TVC lifecycle completion.
