# HIL RTG Deployment and Recovery Runbook

## Purpose

This runbook deploys the HIL response-packet intake as a real-time Relational Transition Geometry application. The durable system is the addressable transition boundary, custody/evidence state, notification outbox, and recovery record. The intake and delivery workers may be short-lived.

Ecosystem Chat Node, KnowledgeVault, and Continuity Vault Kit may strengthen reconstruction and continuation, but none is required for basic response submission.

## Required boundaries

- The public Site may send only the response PDF, its governed provenance manifest, explicitly supplied participant metadata, and optional attempt-notification authorization.
- `Rigel@stegverse.org` receives a privacy-minimized notification for each server-received attempt.
- A participant receives a copy only when an address is supplied and the scope is exactly `ATTEMPT_NOTIFICATION_ONLY`.
- Participant addresses exist only in the restricted notification-delivery envelope.
- Submission outcome and notification-delivery outcome remain independent.
- Provider credentials never enter the public browser or response packet.

## Runtime topology

```text
Site commit action
  -> wakeable HTTPS intake boundary
  -> ephemeral gateway execution
  -> TVC intake decision reconstruction
  -> PDF/provenance validation
  -> custody commit or bounded refusal/failure
  -> receiver receipt
  -> public privacy-minimized notification artifact
  -> restricted delivery envelope
  -> intake execution expires

notification event or scheduled recovery
  -> ephemeral delivery worker
  -> required Rigel delivery
  -> optional participant delivery
  -> recipient-specific result persistence
  -> unresolved recipients remain retryable
  -> delivery execution expires
```

## Intake environment

Required:

```text
STEGVERSE_HIL_STORAGE_ROOT
STEGVERSE_HIL_RECEIPT_KEY
STEGVERSE_TVC_DECISION_RECEIPT
```

`STEGVERSE_TVC_DECISION_RECEIPT_FILE` may replace the inline TVC receipt.

The storage root must preserve these private directories across executions:

```text
packets/
receipts/
attempts/
notifications/
notification-outbox/
```

Only intentionally published derivatives may cross into a public repository or public object path.

## Delivery environment

Required only by the separate delivery worker:

```text
STEGVERSE_NOTIFICATION_FROM
STEGVERSE_SMTP_HOST
STEGVERSE_SMTP_PORT
STEGVERSE_SMTP_USERNAME
STEGVERSE_SMTP_PASSWORD
STEGVERSE_SMTP_STARTTLS
STEGVERSE_HIL_STORAGE_ROOT
```

Intake must remain operational when delivery credentials are absent. Missing or failed email transport leaves notification delivery pending; it does not invalidate an accepted packet.

## Commands

Run Site-compatible intake:

```bash
python -m llm_adapter.service_gateway_site
```

Process pending notification envelopes:

```bash
python -m llm_adapter.notification_delivery
```

Verify contracts and tests:

```bash
python scripts/verify_hil_rtg_notification_contract.py
pytest -q tests/test_hil_notification_delivery.py tests/test_hil_gateway_attempt_contract.py
```

## Attempt outcomes

### Accepted

Persist packet custody, receipt, attempt state, public notification, and restricted delivery envelope. The public notification contains no participant address or response prose.

### Refused

Persist the attempt identifier, refusal stage, bounded reason, cleanup result, retry eligibility, public notification, and restricted delivery envelope. Rejected bytes are removed unless a separately governed quarantine rule admits retention.

### Infrastructure failure

Persist the last completed transition, available hashes, custody state, cleanup state, and reconciliation requirement. A failure after custody commit resumes from custody; it must not create a second independent submission.

### Duplicate restoration

Return the prior valid receipt while creating a new attempt notification for the new attempted submit. Duplicate restoration does not resend already completed recipient deliveries from an earlier attempt because each attempt has its own outbox envelope.

## Delivery recovery

Delivery is recipient-idempotent:

- completed recipients are not sent again;
- only unresolved recipients are retried;
- `PARTIAL` means at least one recipient completed and at least one remains unresolved;
- `DELIVERED` means all admitted recipients completed;
- `DELIVERY_FAILED` means none completed in the most recent aggregate state;
- retry exhaustion must preserve the submission outcome and unresolved delivery evidence.

## Activation checklist

1. Confirm the TVC receipt admits only the intake storage and receipt-signing capabilities.
2. Provide durable private storage.
3. Start or connect the wakeable intake boundary.
4. Configure the Site receiver URL.
5. Verify `/api/hil/readiness` reports the exact canonical paper, prompt, provenance, and notification scope.
6. Submit a controlled PDF with no participant email.
7. Confirm packet, receipt, attempt, notification, and one-recipient envelope creation.
8. Submit a controlled PDF with participant opt-in.
9. Confirm the address occurs only in the restricted envelope.
10. Run the delivery worker and confirm recipient-specific results.
11. Simulate participant-delivery failure and confirm Rigel is not resent during recovery.
12. Confirm no email-delivery outcome changes packet acceptance or refusal.

## Public claim boundary

Activation demonstrates a governed, event-induced HIL intake path with durable evidence and independently recoverable notification delivery. It does not by itself demonstrate universal hosting independence, general framework certification, scientific validity of submitted responses, or publication authority.
