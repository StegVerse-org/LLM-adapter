# Shared Attachment + Math Image Review Mirror Handoff

## Canonical identity

```text
goal_id: LLMA-SHARED-ATTACHMENT-MATH-IMAGE-183
repository: StegVerse-org/LLM-adapter
canonical_issue: #183
shared_gateway_owner: #72
math_runtime_owner: #132
site_math_owner: StegVerse-Labs/Site#240
canonical_math_specialty: profiles/math-educator-specialty.v1.json
credential_authority: TV/TVC
github_token_runtime_authority: NONE
source_state: SOURCE_VALIDATED_GLOBAL_CI_DEPENDENCY_BLOCKED
```

## Product decision

HIL document upload and mathematics image upload are profiles over one shared governed attachment/service-gateway concept, not independent upload systems.

```text
browser / client
  -> existing StegVerse deployed gateway
  -> shared attachment intake
       -> exact uploaded bytes
       -> detected media type
       -> SHA-256 content binding
       -> durable/local gateway storage state
       -> deterministic non-authorizing receipt
  -> specialty consumer
       HIL: existing HIL protocol/lifecycle path
       math: backend image review
```

The HIL endpoints are not replaced by this source slice. Existing HIL protocol, provenance, review, TVC lifecycle, and publication ownership remain unchanged. The new attachment root reuses `STEGVERSE_HIL_DATA_DIR` unless an explicit `STEGVERSE_ATTACHMENT_DATA_DIR` is configured, so the deployed gateway can share the established artifact-storage plane without coupling math to HIL-specific review semantics.

## Implemented source slice

```text
llm_adapter/attachment_intake.py
tests/test_shared_attachment_math_image.py
llm_adapter/deployed_gateway.py
llm_adapter/combined_gateway.py
pyproject.toml
tasks/LLMA-SHARED-ATTACHMENT-MATH-IMAGE-183.json
```

The deployed gateway exposes:

```text
GET  /api/attachments/v1/readiness
POST /api/attachments/v1/intake
POST /api/math-solver/v1/image-review
```

The existing `/api/stegverse-node` advertisement now publishes all three endpoints so a client can discover image upload/review alongside ordinary Ecosystem Chat, Math Solver, and HIL endpoints.

The first attachment profile is `math-image-v1`.

Accepted decoded formats:

```text
PNG
JPEG
WebP
HEIF/HEIC when supported by the installed pillow-heif decoder
```

The portable-node image already installs `.[service]`; this slice adds `pillow` and `pillow-heif` to that service extra, so raw image decode is part of the actual portable-node dependency set rather than a documentation-only capability.

The service does not trust the browser-provided content type. It decodes the exact uploaded bytes and records the detected format. Maximum math image upload is 25 MiB and decoded images are bounded to 80,000,000 pixels before full image load/review.

## Shared storage semantics

For each accepted attachment the service persists:

```text
attachments/<attachment_id>/source.<detected-extension>
attachments/<attachment_id>/metadata.json
attachment-receipts/<attachment_id>.json
```

Math review is persisted separately:

```text
math-image-reviews/<attachment_id>.json
```

Duplicate attachment IDs are idempotent only when profile, content hash, and decoded media type match. Reusing an attachment ID with different bytes fails closed with `409 attachment_id_content_conflict` and does not replace the original source state.

This separation is deliberate. Upload acceptance does not imply review, review does not imply transcription, and transcription would not imply mathematical truth or solver execution.

## Backend math image review

The backend performs real raw-image decoding and bounded whole-frame feature extraction. It emits the exact normalized feature names required by the released sovereign visual-evidence runtime:

```text
schema: stegverse.normalized-region-features/v1
mean_r
mean_g
mean_b
saturation
luminance
edge_density
texture_variance
region_solidity
```

The feature extractor is aligned to the already released `StegVerse-002/micro-node-runtime` visual contract. It does not create another visual model or runtime.

The review also records deterministic quality flags for very low spatial resolution, extreme exposure, and very low edge information. These are review hints only; they do not establish whether the mathematics was semantically understood.

## Critical image/transcription boundary

The mathematics specialty contract is enforced as separate states:

```text
source_image
  -> real accepted image bytes/hash/dimensions/features

interpreted_mathematical_transcription
  -> NOT_PRODUCED in this slice
```

The source image remains immutable. A future transcription correction must create a successor interpretation state rather than rewriting the source image or silently converting an interpretation into source fact.

## Sovereign visual runtime binding

Existing released source:

```text
StegVerse-002/micro-node-runtime
SOVEREIGN-LOCAL-VISION-MODEL-002: COMPLETE_RELEASED
SOVEREIGN-LOCAL-VISION-RUNTIME-003: COMPLETE_RELEASED
reference model: stegverse-reference-visual-evidence-v1
input schema: stegverse.normalized-region-features/v1
```

That reference model is deliberately low-level and is explicitly **not** a raw-image decoder, OCR system, equation transcription model, or production VLM. This gateway slice supplies the missing raw-image decode/feature boundary but does not misrepresent the current reference model as math OCR.

Therefore the review returns:

```text
interpreted_mathematical_transcription.state = NOT_PRODUCED
next_stage = MATH_CAPABLE_VISUAL_TRANSCRIPTION_REQUIRED
```

A true math-capable visual transcription capability is the next bounded runtime/model integration requirement.

## Validation evidence

Implementation head before task-record writeback:

```text
16d3ceb456c69f32213089b88a3dcbdd9948d817
```

Focused functional validation passed for:

```text
real PNG decode
canonical eight-feature vector in range 0..1
browser content-type spoof resistance
exact SHA-256 binding / exact-byte preservation
invalid image fail closed
declared hash mismatch fail closed
same-source review idempotency
source_image != interpreted_mathematical_transcription
transcription state = NOT_PRODUCED
```

Source review then added:

```text
conflicting duplicate attachment-id rejection
pre-load decoded pixel bound
Python 3.9-compatible type syntax
portable-node service dependency binding for Pillow/HEIF
node endpoint advertisement for intake/review discovery
```

Hosted repository-wide validation remains blocked before project tests by the already-known public-distribution dependency defect:

```text
validate run: 32571850375 -> FAIL at dependency installation
capability-runtime run: 32571850359 -> FAIL at dependency installation
cause: credential-clean install cannot anonymously acquire the protected direct StegCore source dependency
issue-183 code reached by hosted tests: NO
```

That defect is owned by the StegVerse SDK + TVC portable-artifact publication chain. This handoff does not authorize a GitHub-token workaround, repository-visibility change, or parallel publisher.

## Authority boundary

```text
attachment acceptance != execution authority
attachment hash != custody
image review != transcription
visual feature inference != mathematical truth
transcription != source fact
transcription != solver authority
solver result != proof authority
model output != execution authority
credential authority = TV/TVC
GitHub token runtime authority = NONE
NON-TV/TVC production secrets/tokens = PROHIBITED
second gateway = NOT CREATED
second vision runtime = NOT CREATED
second custody path = NOT CREATED
```

## Completion / continuation

This source slice is implemented and focused-validated. Canonical source completion still requires PR merge after fresh collision check. Merge does not establish live carrier observation.

After merge:

```text
#72 -> shared gateway persistent/live carrier observation
#132 -> Math Solver consumes accepted math image + review state
Site#240 -> public image composer only after Site mutation authority/admission
micro-node runtime / TVC -> add/admit a genuine math-capable visual transcription runtime
Master Records -> custody only under its existing authority after actual execution where required
```

This handoff does not claim persistent public hosting, live visual-route admission, semantic math transcription, Site activation, custody, or publication.
