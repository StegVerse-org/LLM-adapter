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
source_state: SOURCE_COMPLETE_RELEASED
implementation_pr: #184
merge_commit: 4ed2b08789e8bbe0c7f474f1c448f71d5dbe5d55
```

## Product decision

HIL document upload and mathematics image upload share the existing governed Service Gateway/artifact-storage plane rather than creating independent upload systems. Existing HIL protocol, provenance, private-review, TVC lifecycle, and publication ownership remain unchanged.

```text
client
  -> existing deployed gateway
  -> shared attachment intake
       -> exact bytes + detected media type + SHA-256 + receipt
  -> specialty consumer
       -> HIL existing lifecycle
       -> Math backend image review
```

`STEGVERSE_ATTACHMENT_DATA_DIR` may provide an explicit attachment root; otherwise attachments reuse `STEGVERSE_HIL_DATA_DIR`.

## Released implementation

```text
llm_adapter/attachment_intake.py
tests/test_shared_attachment_math_image.py
llm_adapter/deployed_gateway.py
llm_adapter/combined_gateway.py
pyproject.toml
```

Routes on the deployed portable node:

```text
GET  /api/attachments/v1/readiness
POST /api/attachments/v1/intake
POST /api/math-solver/v1/image-review
```

`/api/stegverse-node` advertises all three routes, making them discoverable rather than requiring client-side hardcoding.

The first attachment profile is `math-image-v1`. Real decoded formats are PNG, JPEG, WebP, and HEIF/HEIC when handled by the installed `pillow-heif` decoder. `Dockerfile.portable-node` installs `.[service]`; this release adds Pillow and pillow-heif to that service dependency set.

The service does not trust browser content type. It decodes uploaded bytes, records the detected format, limits upload size to 25 MiB, bounds decoded images to 80,000,000 pixels before full image load, preserves exact bytes, and binds the attachment to SHA-256.

Storage surfaces:

```text
attachments/<attachment_id>/source.<detected-extension>
attachments/<attachment_id>/metadata.json
attachment-receipts/<attachment_id>.json
math-image-reviews/<attachment_id>.json
```

Duplicate IDs are idempotent only for the same profile/hash/decoded media; conflicting bytes fail closed and never replace the original source image.

## Real backend image review

The backend decodes the actual image and computes the canonical eight normalized visual features consumed by the released sovereign visual runtime:

```text
stegverse.normalized-region-features/v1
mean_r
mean_g
mean_b
saturation
luminance
edge_density
texture_variance
region_solidity
```

It also emits bounded quality-review flags for low spatial resolution, extreme exposure, and low edge information. These are image-evidence/quality signals, not claims that an equation was semantically understood.

## Image/transcription state boundary

```text
source_image
  state: IMPLEMENTED
  exact bytes/hash/dimensions/features: preserved

interpreted_mathematical_transcription
  state: NOT_PRODUCED
  is_source_fact: false
```

The source image remains immutable. A corrected transcription must be a successor interpretation state rather than a rewrite of the source image.

## Existing sovereign vision capability

```text
StegVerse-002/micro-node-runtime
SOVEREIGN-LOCAL-VISION-MODEL-002: COMPLETE_RELEASED
SOVEREIGN-LOCAL-VISION-RUNTIME-003: COMPLETE_RELEASED
reference model: stegverse-reference-visual-evidence-v1
input schema: stegverse.normalized-region-features/v1
```

That reference model is explicitly not raw-image OCR, equation transcription, or a production VLM. This released gateway slice supplies raw-image decode and normalized features but does not misrepresent the reference model as a math reader.

Therefore:

```text
interpreted_mathematical_transcription.state = NOT_PRODUCED
next capability = MATH_CAPABLE_VISUAL_TRANSCRIPTION_RUNTIME
```

## Validation evidence

Focused functional validation passed for real image decode, canonical feature output, content-type spoof resistance, exact hash/byte preservation, invalid-image and hash-mismatch rejection, idempotent review, and image/transcription separation. Source hardening additionally installed conflicting-ID rejection, pre-load pixel bounds, Python 3.9-compatible annotations, actual portable-node image dependencies, and node discovery.

Repository-wide hosted runs still fail before project code at dependency installation:

```text
validate: 32571850375
capability-runtime: 32571850359
cause: existing protected direct StegCore source dependency cannot be anonymously acquired by the credential-clean workflow
issue-183 project tests reached: false
```

That distribution defect remains owned by the StegVerse SDK + TVC portable-artifact publication chain. No GitHub-token workaround, repository-visibility change, or parallel publisher is authorized here.

## Authority boundary

```text
attachment acceptance != execution authority
attachment hash != custody
image review != transcription
visual features != mathematical truth
transcription != source fact
transcription != solver authority
solver output != proof authority
model output != execution authority
credential authority = TV/TVC
GitHub token runtime authority = NONE
second gateway = not created
second visual runtime = not created
second custody path = not created
```

## Continuation

The bounded source task is released. Do not reopen it merely to pursue transcription.

```text
#72 -> persistent/live shared-gateway carrier observation
#132 -> consume accepted image/review state in Math Solver
Site#240 -> public image composer after Site mutation admission
StegVerse-002/micro-node-runtime + TVC -> develop/admit genuine math-capable visual transcription runtime
Master Records -> existing custody authority only when required by actual execution
```

Source merge is not persistent public hosting, live visual-route admission, semantic math transcription, Site activation, custody, or publication.
