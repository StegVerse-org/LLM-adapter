# TV/TVC Service Receipt Return

Every TV/TVC service request emitted by this repository must receive a governed return bundle. The return is not an optional operator message and must not be reduced to a workflow status.

## Required return package

```text
orchestrated service bundle
+ TV ledger append receipt
+ requester return receipt
```

The package must bind:

- requester repository and request path;
- request ID and service ID;
- canonical request SHA-256;
- estimate line;
- authority evidence;
- CGE admissibility result or explicit pending state;
- service execution or refusal receipt;
- actual invoice line;
- TV ledger append receipt;
- return timestamp and destination;
- package SHA-256.

## Requester-owned paths

```text
receipts/tv-tvc/<request-id>/service-bundle.json
receipts/tv-tvc/<request-id>/ledger-append-receipt.json
receipts/tv-tvc/<request-id>/return-receipt.json
```

These files are governed projections. Raw capability values, secret material, and private vault values must never be returned.

## State transition

```text
REQUESTED
→ DISCOVERED
→ ESTIMATED
→ ADMISSIBILITY_EVALUATED
→ EXECUTED_OR_REFUSED
→ RECEIPTED
→ INVOICED
→ LEDGER_APPENDED
→ RETURNED
→ CONSUMED
```

`RETURNED` does not imply that the requesting component has consumed or acted on the service result. Consumption is a separate transition and must be receipted where it changes state.

## Inline accounting

The estimate and actual service line must remain visible in conversation, session, project, entity, organization, and ecosystem invoice projections. `VALUATION_PENDING` remains visible and must never be rendered as a silent zero-cost service.

## Authority boundary

Receipt return proves that the service lifecycle produced governed evidence. It does not grant public release, Master Record custody, payment settlement, or additional execution authority.
