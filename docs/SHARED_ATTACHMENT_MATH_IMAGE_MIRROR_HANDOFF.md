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
```

## Product decision

HIL document upload and mathematics image upload are profiles over one shared governed attachment service, not independent upload systems.

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

The HIL endpoints are not replaced by this source slice. Existing HIL protocol, provenance, review, TVC lifecycle, and publication ownership remain unchanged.

## Implemented source slice

```text
llm_adapter/attachment_intake.py
tests/test_shared_attachment_math_image.py
llm_adapter/deployed_gateway.py
pyproject.toml
```

The deployed gateway now exposes:

```text
GET  /api/attachments/v1/readiness
POST /api/attachments/v1/intake
POST /api/math-solver/v1/image-review
```

The first attachment profile is `math-image-v1`.

Accepted decoded formats:

```text
PNG
JPEG
WebP
HEIF/HEIC when supported by the installed pillow-heif decoder
```

The service does not trust the browser-provided content type. It decodes the exact uploaded bytes and records the detected format. Maximum math image upload is 25 MiB and decoded images are bounded to 80,000,000 pixels before review.

## Shared storage semantics

The new attachment service reuses the existing Service Gateway storage plane. `STEGVERSE_ATTACHMENT_DATA_DIR`, when present, provides an explicit attachment root; otherwise the service reuses `STEGVERSE_HIL_DATA_DIR`, preserving the current HIL-backed durable storage deployment model.

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

## Validation requirements

Focused source validation must prove:

1. real image bytes decode;
2. the canonical eight-feature vector is produced in range 0..1;
3. declared hash mismatch fails before persistence;
4. browser content-type spoofing does not override detected image format;
5. unknown profile and non-image input fail closed;
6. exact accepted bytes are preserved;
7. review is idempotent for the same source hash;
8. `source_image` and transcription remain distinct;
9. transcription remains `NOT_PRODUCED` and non-authorizing;
10. HIL routes are not removed or replaced.

Global repository validation may remain blocked before project tests by the already-known protected StegCore direct-source dependency. That dependency/publication problem is owned by the StegVerse SDK + TVC portable-artifact publication chain and must not be bypassed with a GitHub token or parallel publisher.

## Continuation after source merge

```text
#72 -> shared gateway persistent/live carrier observation
#132 -> Math Solver consumes accepted math image + review state
Site#240 -> public image composer only after Site mutation authority/admission
micro-node runtime / TVC -> admit exact visual/transcription runtime when available
Master Records -> custody only under its existing authority after actual execution where required
```

This handoff documents source implementation. It does not itself establish persistent public hosting, live vision-route admission, math transcription, Site activation, custody, or publication.
