# HIL Submission Client Mirror Handoff

## Purpose

This handoff governs the dependency-absorbing local HIL submission client. The client replaces manual directory navigation, PDF hashing, provenance JSON construction, Swagger multipart entry, and receipt copying.

## User Path

```text
start-hil-submission-client.cmd
→ choose response PDF
→ read receiver readiness contract
→ compute response SHA-256
→ build exact HIL provenance manifest
→ submit multipart packet
→ display receipt
→ retain manifest and receipt beside the PDF
```

## Built Files

```text
scripts/hil_submit_client.py
scripts/start-hil-submission-client.cmd
tests/test_hil_submit_client.py
docs/HIL_SUBMISSION_CLIENT_MIRROR_HANDOFF.md
```

## Authority Boundary

The client does not grant execution, review, publication, custody, Master-Records append, or Site activation authority. It performs participant-directed packet construction and submission only. Receiver-side validation remains authoritative for intake.

Consent declarations are never inferred. The user must explicitly select publication consent and explicitly acknowledge the unedited-response and participant-consent-authority declarations when true.

## Runtime Contract

Default receiver:

```text
http://127.0.0.1:8000
```

Override:

```text
STEGVERSE_HIL_BASE_URL=https://receiver.example
```

The client derives these values from `/api/hil/readiness` rather than embedding them independently:

```text
provenance_manifest_schema
primary_version
primary_sha256
protocol_version
prompt_version
prompt_sha256
```

It computes `response_sha256` from the selected PDF and supplies an explicit `UNAVAILABLE` producer-signature state when no verified signature exists.

## Local Acceptance

```text
python -m pytest tests/test_hil_submit_client.py
scripts\start-hil-submission-client.cmd
```

Acceptance requires:

1. Receiver reports `READY`.
2. A valid PDF can be selected without shell navigation.
3. The exact manifest is generated automatically.
4. Submission errors are shown without losing the selected file.
5. Successful receipt and manifest JSON files are written beside the PDF.
6. No `.env.hil.local` value or review/publication secret is read, displayed, or committed.

## Remaining Destinations

After local acceptance and merge:

- expose the same workflow from the StegVerse iOS control surface;
- mirror the governed upload UX into `StegVerse-Labs/Site` only after the public HTTPS receiver is proven;
- preserve the Site rule that `data/hil-receiver-config.json` remains unconfigured until HTTPS and allowed-origin proof exists;
- publish acceptance evidence to the admissibility and StegGuardian wiki surfaces without claiming review, publication, or custody authority.
