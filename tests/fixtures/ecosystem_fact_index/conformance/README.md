# Ecosystem fact index conformance vector

Shared, pinned conformance cases for `llm_adapter/ecosystem_fact_index.py`
(`build_index` / `lookup`). Any other implementation of the same fact index,
for example RT-ECOSYSTEM-CHAT-LOCAL-ANSWER-001 in StegVerse-Labs, can vendor
this directory and must produce the same results.

## Contents

- `conformance-vector.json` is the manifest (`stegverse.ecosystem-fact-index-conformance/v1`).
- `sources/` holds byte-identical copies of the four pinned registry fixture subsets in
  `tests/fixtures/ecosystem_fact_index/`. Their revision is `fixture-subset`, and
  `subset_of` records the upstream revision each one was trimmed from.
- `refusal/` holds small registry files used by the build-refusal cases.

Every fixture path is relative to this directory. Each file is pinned by
`sha256` in the manifest, and the manifest itself is pinned by
`MANIFEST_SHA256` in `tests/test_ecosystem_fact_index_conformance.py`.

## Vendoring

1. Copy this directory at a pinned LLM-adapter commit.
2. Check that `sha256(conformance-vector.json)` equals the digest you pinned.
   Then check every `source_fixtures[*]` and `refusal_fixtures[*]` file against its
   `sha256`. If anything does not match, stop.
3. For each entry in `indexes`, build an index from the listed `source_fixtures`
   (repository, path, revision, sha256 and the file bytes). Expect `ALLOW` and
   `expected_fact_count` facts.
4. Run each case:
   - `operation: "lookup"`: look up `query` (and `kind`, if present) in the named
     index. Match exactly, with no case folding and no whitespace stripping.
   - `operation: "build"`: build from `sources`. A source is either a
     `source_fixture` reference or an inline declaration (repository, path,
     revision, `declared_sha256`) with the bytes of `refusal_fixture`. Pass
     `declared_sha256` exactly as written, because some cases are wrong on purpose.
5. Assert the exact results:
   - `expected_status` is `ANSWER`, `NOT_FOUND` or `REFUSED`.
   - `expected_disposition` follows from it: `ANSWER` is `ALLOW`, and
     `NOT_FOUND`/`REFUSED` is `FAIL_CLOSED`.
   - For `ANSWER`, the ordered answers must equal `expected_answers` on `key`,
     `kind` and `citation` (`{repository}@{revision}:{path}:{line}`).
   - For `FAIL_CLOSED`, `failure_code` and `failed_predicate` must equal the
     expected values, and all six fields in `rules.fail_closed_required_fields`
     must be non-empty.

When the vector changes, update `MANIFEST_SHA256` in the test, then re-pin the
new digest in each consumer.
