# Service Gateway — HIT/HIL Intake

## Implemented boundary

The Service Gateway accepts an unchanged PDF plus JSON metadata, validates the PDF signature and declared SHA-256, stores the packet durably, and returns a signed `HIL-RECEIVER-RECEIPT-v2`.

Provider invocation and Master Records custody are not prerequisites for intake.

## TV/TVC authority path

The runtime requires a no-value TVC decision receipt for role `service_gateway_intake`. The receipt must authorize only:

- `service-gateway/hil-intake/storage-root`
- `service-gateway/hil-intake/receipt-key`

Secret values are injected directly into the runtime environment after TVC/CGE admission. They must never be placed in Site configuration, repository content, logs, artifacts, or receipts.

## Runtime variables

```text
STEGVERSE_TVC_DECISION_RECEIPT or STEGVERSE_TVC_DECISION_RECEIPT_FILE
STEGVERSE_HIL_STORAGE_ROOT
STEGVERSE_HIL_RECEIPT_KEY
PORT (optional, default 8080)
```

`STEGVERSE_HIL_RECEIPT_KEY` must contain at least 32 bytes of entropy. `STEGVERSE_HIL_STORAGE_ROOT` must point to a persistent mounted volume.

## Start

```bash
pip install '.[service]'
stegverse-service-gateway
```

Or build:

```bash
docker build -f Dockerfile.service-gateway -t stegverse-service-gateway .
```

## Endpoints

```text
GET  /health
GET  /ready
POST /v1/hil/intake
```

The intake request is multipart form data:

- `document`: PDF file
- `metadata`: canonical JSON string containing at minimum a stable `packet_id`; `document_hash` is strongly recommended

## Success evidence

A successful request returns:

```text
schema: HIL-RECEIVER-RECEIPT-v2
status: SUBMISSION_ACCEPTED
packet_id
document_hash
metadata_hash
document_size_bytes
received_at
storage_class
tvc_decision_id
tvc_policy_hash
receipt_hash
signature
```

Duplicate submission of the same `packet_id` restores the durable receipt instead of creating a second packet.

## Verification

```bash
pytest tests/test_service_gateway.py -v
```

The tests cover readiness, durable PDF intake, hash binding, receipt generation, duplicate recovery, and denial of mixed intake/provider scope.
