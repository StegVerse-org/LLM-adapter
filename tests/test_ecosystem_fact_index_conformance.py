"""Shared conformance vector for llm_adapter.ecosystem_fact_index.

Runs every case in tests/fixtures/ecosystem_fact_index/conformance/conformance-vector.json
through build_index/lookup and asserts the exact expectations. Consumers (for
example RT-ECOSYSTEM-CHAT-LOCAL-ANSWER-001) vendor that directory and pin the
manifest sha256 asserted below.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest

from llm_adapter.ecosystem_fact_index import (
    BUILD_ENTRYPOINT,
    LOOKUP_ENTRYPOINT,
    OWNING_GOAL,
    build_index,
    lookup,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "ecosystem_fact_index"
VECTOR_DIR = FIXTURES / "conformance"
MANIFEST = VECTOR_DIR / "conformance-vector.json"
MANIFEST_SHA256 = "b5929144b5384805edaedd774b378edbed74205b70188d726d693532125520d6"
SCHEMA = "stegverse.ecosystem-fact-index-conformance/v1"
DISPOSITION = {"ANSWER": "ALLOW", "NOT_FOUND": "FAIL_CLOSED", "REFUSED": "FAIL_CLOSED"}
SIX_FIELDS = (
    "failure_code",
    "failed_predicate",
    "required_evidence_or_repair",
    "retry_entrypoint",
    "owning_existing_goal",
    "next_attempt",
)


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def verified_bytes(relative: str, digest: str) -> bytes:
    payload = (VECTOR_DIR / relative).read_bytes()
    if sha256(payload).hexdigest() != digest:
        raise AssertionError(f"conformance fixture {relative} does not match its pinned sha256")
    return payload


def source_from_fixture(fixture: dict) -> dict:
    return {
        "repository": fixture["repository"],
        "path": fixture["path"],
        "revision": fixture["revision"],
        "sha256": fixture["sha256"],
        "bytes": verified_bytes(fixture["fixture"], fixture["sha256"]),
    }


def build_sources(manifest: dict, declared: list) -> list[dict]:
    by_source = {item["id"]: item for item in manifest["source_fixtures"]}
    by_refusal = {item["id"]: item for item in manifest["refusal_fixtures"]}
    sources = []
    for entry in declared:
        if "source_fixture" in entry:
            sources.append(source_from_fixture(by_source[entry["source_fixture"]]))
            continue
        fixture = by_refusal[entry["refusal_fixture"]]
        sources.append({
            "repository": entry["repository"],
            "path": entry["path"],
            "revision": entry["revision"],
            "sha256": entry["declared_sha256"],
            "bytes": verified_bytes(fixture["fixture"], fixture["sha256"]),
        })
    return sources


def run_case(manifest: dict, case: dict, indexes: dict) -> dict:
    if case["operation"] == "lookup":
        index = indexes[case["index"]]
        return lookup(index, case["query"], kind=case.get("kind"))
    result = build_index(build_sources(manifest, case["sources"]))
    return result.to_dict()


class EcosystemFactIndexConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()
        cls.indexes = {}
        by_source = {item["id"]: item for item in cls.manifest["source_fixtures"]}
        for name, spec in cls.manifest["indexes"].items():
            result = build_index([source_from_fixture(by_source[sid]) for sid in spec["source_fixtures"]])
            assert result.status == spec["expected_build_status"] == "ALLOW", result.to_dict()
            assert result.to_dict()["fact_count"] == spec["expected_fact_count"], result.to_dict()
            cls.indexes[name] = result.index

    def test_manifest_digest_is_pinned(self):
        self.assertEqual(sha256(MANIFEST.read_bytes()).hexdigest(), MANIFEST_SHA256)

    def test_manifest_shape(self):
        manifest = self.manifest
        self.assertEqual(manifest["schema"], SCHEMA)
        self.assertEqual(manifest["authority_effect"], "NONE")
        self.assertEqual(manifest["subject"]["build_entrypoint"], BUILD_ENTRYPOINT)
        self.assertEqual(manifest["subject"]["lookup_entrypoint"], LOOKUP_ENTRYPOINT)
        self.assertEqual(manifest["subject"]["owning_existing_goal"], OWNING_GOAL)
        self.assertEqual(manifest["rules"]["disposition"], DISPOSITION)
        self.assertEqual(tuple(manifest["rules"]["fail_closed_required_fields"]), SIX_FIELDS)
        ids = [case["id"] for case in manifest["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for case in manifest["cases"]:
            with self.subTest(case=case["id"]):
                self.assertIn(case["operation"], {"lookup", "build"})
                self.assertEqual(DISPOSITION[case["expected_status"]], case["expected_disposition"])

    def test_every_fixture_file_is_pinned(self):
        declared = {item["fixture"]: item["sha256"] for item in self.manifest["source_fixtures"]}
        declared.update({item["fixture"]: item["sha256"] for item in self.manifest["refusal_fixtures"]})
        on_disk = {
            path.relative_to(VECTOR_DIR).as_posix()
            for path in VECTOR_DIR.rglob("*.json")
            if path != MANIFEST
        }
        self.assertEqual(on_disk, set(declared))
        for relative, digest in declared.items():
            with self.subTest(fixture=relative):
                verified_bytes(relative, digest)

    def test_vendored_sources_equal_repository_fixtures(self):
        for item in self.manifest["source_fixtures"]:
            with self.subTest(source=item["id"]):
                self.assertEqual(
                    (VECTOR_DIR / item["fixture"]).read_bytes(),
                    (FIXTURES / Path(item["fixture"]).name).read_bytes(),
                )

    def test_coverage(self):
        cases = self.manifest["cases"]
        hit_kinds = {
            answer["kind"]
            for case in cases
            if case["expected_status"] == "ANSWER"
            for answer in case["expected_answers"]
        }
        self.assertEqual(
            hit_kinds,
            {"organization_entity", "canonical_task", "reusable_task", "global_invariant"},
        )
        refused = {case["expected_failure_code"] for case in cases if case["expected_status"] == "REFUSED"}
        self.assertTrue({
            "ECOSYSTEM_FACT_SOURCE_DIGEST_MISMATCH",
            "ECOSYSTEM_FACT_SOURCE_DUPLICATE_KEY",
            "ECOSYSTEM_FACT_SOURCE_NESTING_TOO_DEEP",
            "ECOSYSTEM_FACT_SOURCES_EMPTY",
            "ECOSYSTEM_FACT_SOURCE_UNSUPPORTED",
        } <= refused)

    def test_cases(self):
        for case in self.manifest["cases"]:
            with self.subTest(case=case["id"]):
                record = run_case(self.manifest, case, self.indexes)
                status = record["status"]
                self.assertEqual(status, case["expected_status"])
                self.assertEqual(DISPOSITION[status], case["expected_disposition"])
                self.assertEqual(record["authority_effect"], "NONE")
                if status == "ANSWER":
                    self.assertEqual(record["query"], case["query"])
                    self.assertEqual(record["evidence_class"], "OBSERVED")
                    self.assertIs(record["model_memory_used_as_source"], False)
                    self.assertIs(record["network_retrieval_performed"], False)
                    observed = [
                        {"key": item["key"], "kind": item["kind"], "citation": item["citation"]}
                        for item in record["answers"]
                    ]
                    self.assertEqual(observed, case["expected_answers"])
                    for item in record["answers"]:
                        self.assertEqual(item["evidence_class"], "OBSERVED")
                    continue
                for name in SIX_FIELDS:
                    self.assertTrue(str(record.get(name) or "").strip(), name)
                self.assertEqual(record["failure_code"], case["expected_failure_code"])
                self.assertEqual(record["failed_predicate"], case["expected_failed_predicate"])
                self.assertEqual(record["owning_existing_goal"], OWNING_GOAL)
                expected_retry = LOOKUP_ENTRYPOINT if status == "NOT_FOUND" else BUILD_ENTRYPOINT
                self.assertEqual(record["retry_entrypoint"], expected_retry)
                if status == "NOT_FOUND":
                    self.assertEqual(record["query"], case["query"])
                    self.assertNotIn("answers", record)


if __name__ == "__main__":
    unittest.main()
