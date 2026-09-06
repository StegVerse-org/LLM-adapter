# Deterministic canonicalization and hashing specification
`stegverse.intr.anthropic.transport.v1`

Normative. Any change to this document is a protocol-version change, because
every hash basis and domain tag below is version-bound.

---

## 1. Canonical JSON (`canonical_json`)

Serialization rules, applied recursively:

1. **Objects** — keys sorted ascending by Unicode code point; no whitespace;
   `{"k":v,...}`.
2. **Object keys** — must be strings, and must be BMP-only. A key containing a
   character above `U+FFFF` is rejected (`CANONICALIZATION_ERROR`). This removes
   the UTF-16 vs. code-point ordering divergence between RFC 8785 and Python's
   native sort, so no implementation needs a surrogate-aware comparator.
3. **Arrays** — order is preserved and is semantically significant.
4. **Strings** — RFC 8259 escaping, minimal escape set, no ASCII folding
   (`ensure_ascii=false`). No Unicode normalization is applied; a producer that
   emits NFC and one that emits NFD produce different hashes, deliberately.
5. **Numbers** —
   * integers: verbatim decimal, no exponent, no `+`, no leading zeros;
   * floats with integral value and `|x| < 1e17`: emitted as the integer
     (`1.0` → `1`);
   * other floats: shortest round-trip decimal in plain form;
   * a float that requires exponent form, `NaN`, `Infinity` or `-Infinity`:
     **rejected**. Pass an integer or a decimal string instead.
6. **Booleans / null** — `true`, `false`, `null`.
7. **Anything else** (sets, bytes, dates, custom objects) — rejected.

Rationale for (5): silent float formatting divergence is the single most common
source of cross-implementation hash mismatch. Rejecting the ambiguous range is
fail-closed; clamping or rounding would not be.

## 2. Domain-separated digest (`digest`)

```
digest(domain, value) = SHA-256( utf8(domain) || 0x0A || utf8(canonical_json(value)) )
```

Lowercase hex, 64 characters. Domain tags in v1:

| Tag | Use |
|---|---|
| `stegverse.intr.anthropic.transport.v1/request` | `request_hash` |
| `stegverse.intr.anthropic.transport.v1/transport_id` | `transport_id` |
| `stegverse.intr.anthropic.transport.v1/envelope` | `envelope_hash` |
| `stegverse.intr.anthropic.transport.v1/response` | `response_hash` |
| `stegverse.intr.anthropic.transport.v1/measurement` | `measurement_id` |

Every hash accepted or emitted by this adapter must match `^[0-9a-f]{64}$`.
Uppercase hex is rejected, not normalized.

## 3. `request_hash`

Basis:

```json
{"provider":…,"model":…,"endpoint_profile":…,"payload":{…}}
```

The adapter **recomputes** this from the ProviderRequest it actually holds and
compares it exactly to both the declared `request_hash` and the ingress
decision's `request_hash`. Any of the three disagreeing is a
`HASH_BINDING_MISMATCH` and the network call does not occur.

## 4. `transport_id`

```
transport_id = "svintr-anth-" + digest(
  ".../transport_id",
  {protocol_version, transition_id, request_hash, ingress_receipt_hash,
   carrier_ref, endpoint_profile}
)
```

Exactly six inputs, per §3 of the specification. Nothing else is folded in, so
transport identity is reproducible from the ingress record alone.

## 5. `envelope_hash`

`digest(".../envelope", envelope)` over the validated 14-field envelope. The
envelope is closed: an unadmitted field is `AUTHORITY_ESCALATION`, not an
extension point.

Endpoint base URL, path and `anthropic-version` are **not** envelope fields
(the envelope field list in §2 of the specification is exhaustive). They are
admitted transport configuration, enforced pre-network by `verify_endpoint`,
and hash-bound downstream via `metadata.anthropic_api_version`, which is part
of the `response_hash` basis. Reconstruction therefore still recovers the exact
API version used.

## 6. Content-block normalization (v1, normative)

`normalization_version = "1"`.

1. `content` must be a JSON array, else fail closed.
2. Blocks are processed in provider order; the original `index` is retained.
3. Each block must be an object with a non-empty string `type`.
4. A `type` outside the known set fails closed, unless the operator explicitly
   sets `allow_unknown_block_types` — recorded in metadata as
   `unknown_block_types_admitted`.
5. Each normalized entry is
   `{"index", "type", "material", "block"}`, where `block` is the provider
   block **retained verbatim**. Nothing is dropped, reordered, merged or
   summarized, so no semantically material tool-use or structured block can be
   lost by normalization.
6. Typed projections are added: `text` for `text` blocks; `tool_name` and
   `tool_use_id` for `tool_use` / `server_tool_use` / `mcp_tool_use`.
7. `material` is true for every block type other than `text`.
8. `output` is a **display projection only**: the `text` of `text` blocks joined
   with `\n`. When any material block is present,
   `metadata.output_is_lossy_projection` is true. `output` is never the sole
   hash basis.

Known block types in v1: `text`, `thinking`, `redacted_thinking`, `tool_use`,
`server_tool_use`, `tool_result`, `web_search_tool_result`, `mcp_tool_use`,
`mcp_tool_result`, `image`, `document`.

## 7. `response_hash`

Basis:

```json
{
  "provider": "anthropic",
  "model": "<admitted model>",
  "normalized_output": "<display projection>",
  "normalized_blocks": [ … verbatim blocks, in order … ],
  "request_hash": "<64 hex>",
  "normalized_metadata": { … }
}
```

This exceeds the stated minimum: `normalized_blocks` is included so the hash
binds tool-use and structured content, not merely displayed text. Because
`normalized_metadata` carries `response_id`, `stop_reason`, `stop_sequence`,
`runtime_model`, `usage`, `transport_id`, `ingress_receipt_hash` and
`anthropic_api_version`, the reconstruction bundle in the Master Records handoff
re-hashes to the same value — asserted by
`test_reconstruction_bundle_rehashes_identically`.

## 8. `measurement_id`

```
measurement_id = "meas-" + digest(".../measurement",
  {transport_id, transition_id, response_hash})
```

Deterministic rather than random, so usage evidence is reproducible from the
transaction record and cannot be forked into two measurements for one response.

## 9. Reconstruction procedure

Given `{envelope, normalized_response}` from the Master Records handoff:

1. `validate_envelope(envelope)`; recompute `envelope_hash`; compare to evidence.
2. Recompute `compute_response_hash(normalized_response)`; compare to
   `evidence.response_hash`.
3. Recompute `compute_transport_id(...)` from the envelope's six basis fields;
   compare to `envelope.transport_id`.
4. Rebuild the wire request with `map_request_to_anthropic` from the original
   ProviderRequest and confirm `compute_request_hash` still matches.

No credential material is required for, or recoverable from, any of these steps.
