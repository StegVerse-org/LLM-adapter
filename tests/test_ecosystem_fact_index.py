"""Tests for the exact-identifier ecosystem registry fact index and its AI Entry wiring."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest import mock
import urllib.request

from llm_adapter import ai_entry_backend_service as backend
from llm_adapter import ecosystem_fact_index as fact_index_module
from llm_adapter.chat_profiles import SourceCandidate, evaluate_source, load_profile
from llm_adapter.ecosystem_fact_index import (
    EcosystemFactIndex,
    EcosystemFactSourceConfigError,
    _parse_located_json,
    _plain,
    build_index,
    load_source_manifest,
    lookup,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "ecosystem_fact_index"
REVISION = "fixture-subset"

# (repository, registry path, fixture file, pinned sha256 of the fixture bytes)
PINNED_FIXTURES = (
    ("SV-LLM/.github", "data/organization-tree.json", "organization-tree.json",
     "73ae5929ba8a55fb45ac17db8f1b04e239f40d54333ac3b19cbcb6828bb6d1e1"),
    ("StegVerse-Labs/.github", "data/canonical-task-registry.json", "canonical-task-registry.json",
     "262ce4c39e2e67cc39cbe7409f77f42263eb0e5babf9a521cfd4a224877b1e1f"),
    ("StegVerse-Labs/.github", "data/reusable-task-registry.json", "reusable-task-registry.json",
     "c46ccdeed614cc28f6e4057de1390f274e9afadfb5442de81012b583df2a0644"),
    ("StegVerse-Labs/.github", "data/task-registry-global-invariants.json", "task-registry-global-invariants.json",
     "48a9ad4fd192ccedba4b783f1b5de088e34f5b89068421741a79bd9c9977b078"),
)

SIX_FIELDS = (
    "failure_code",
    "failed_predicate",
    "required_evidence_or_repair",
    "retry_entrypoint",
    "owning_existing_goal",
    "next_attempt",
)


def fixture_sources() -> list[dict]:
    return [
        {
            "repository": repository,
            "path": path,
            "revision": REVISION,
            "sha256": digest,
            "bytes": (FIXTURES / name).read_bytes(),
        }
        for repository, path, name, digest in PINNED_FIXTURES
    ]


def built_index() -> EcosystemFactIndex:
    result = build_index(fixture_sources())
    assert result.status == "ALLOW", result.to_dict()
    assert result.index is not None
    return result.index


def nested_organization_tree_source(total_depth: int) -> dict:
    """Organization-tree source whose deepest container sits at ``total_depth``.

    Root object (1), ``repositories`` array (2) and the entry object (3) are
    followed by ``total_depth - 3`` nested arrays under ``extra``.
    """

    inner = total_depth - 3
    raw = (
        '{"schema": "sv-llm.organization-tree/v1", "repositories": [{"name": "Deep_Entity", "extra": '
        + "[" * inner + "]" * inner + "}]}"
    ).encode("utf-8")
    return {
        "repository": "SV-LLM/.github",
        "path": "data/organization-tree.json",
        "revision": "deep",
        "sha256": sha256(raw).hexdigest(),
        "bytes": raw,
    }


def raw_source(repository: str, path: str, raw: bytes) -> dict:
    return {
        "repository": repository,
        "path": path,
        "revision": "raw",
        "sha256": sha256(raw).hexdigest(),
        "bytes": raw,
    }


def _forbidden(*_args, **_kwargs):
    raise AssertionError("network or subprocess use is forbidden")


def no_io_patches():
    return (
        mock.patch.object(socket, "socket", _forbidden),
        mock.patch.object(socket, "create_connection", _forbidden),
        mock.patch.object(urllib.request, "urlopen", _forbidden),
        mock.patch.object(subprocess, "Popen", _forbidden),
    )


class EcosystemFactIndexTests(unittest.TestCase):
    def test_fixtures_match_pinned_digests(self):
        for _repository, _path, name, digest in PINNED_FIXTURES:
            with self.subTest(name=name):
                self.assertEqual(sha256((FIXTURES / name).read_bytes()).hexdigest(), digest)

    def test_located_parser_matches_stdlib_json(self):
        for _repository, _path, name, _digest in PINNED_FIXTURES:
            text = (FIXTURES / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertEqual(_plain(_parse_located_json(text)), json.loads(text))

    def test_indexes_documented_keys_per_source(self):
        index = built_index()
        kinds = {}
        for facts in index.facts.values():
            for fact in facts:
                kinds.setdefault(fact.kind, set()).add(fact.key)
        self.assertEqual(
            kinds["organization_entity"],
            {".github", "schemas", "sandbox", "StegVerse_AI", "Ecosystem_Chat"},
        )
        self.assertEqual(
            kinds["canonical_task"],
            {
                "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
                "QUANTUM-RESILIENCE-001",
                "SHWP-ECOSYSTEM-CHAT-INFERENCE-001",
            },
        )
        self.assertEqual(
            kinds["reusable_task"],
            {"RT-README-VALIDATION-001", "RT-MIRROR-HANDOFF-VALIDATION-001", "RT-STEGINDEX-VALIDATION-001"},
        )
        self.assertIn("stegos_device_role", kinds["global_invariant"])
        self.assertIn("runtime_substrate_review_order", kinds["global_invariant"])
        self.assertEqual(len(kinds["global_invariant"]), 9)

    def test_hit_cites_exact_line_of_supplied_bytes(self):
        index = built_index()
        cases = (
            ("SHWP-ECOSYSTEM-CHAT-INFERENCE-001", "canonical-task-registry.json",
             "StegVerse-Labs/.github@fixture-subset:data/canonical-task-registry.json:56",
             {"coordination_state": "ACTIVE", "parent_task_id": None}),
            ("Ecosystem_Chat", "organization-tree.json",
             "SV-LLM/.github@fixture-subset:data/organization-tree.json:28",
             {"class": "ECOSYSTEM_ENTITY", "authority_effect": "NONE"}),
            ("RT-MIRROR-HANDOFF-VALIDATION-001", "reusable-task-registry.json",
             "StegVerse-Labs/.github@fixture-subset:data/reusable-task-registry.json:14",
             {"name": "Mirror Handoff Validation"}),
            ("stegos_device_role", "task-registry-global-invariants.json",
             "StegVerse-Labs/.github@fixture-subset:data/task-registry-global-invariants.json:8",
             {"value": "INTERCHANGEABLE_TRANSPORT_NODE"}),
        )
        for query, fixture, citation, expected_values in cases:
            with self.subTest(query=query):
                result = lookup(index, query)
                self.assertEqual(result["status"], "ANSWER")
                self.assertEqual(result["evidence_class"], "OBSERVED")
                self.assertEqual(len(result["answers"]), 1)
                answer = result["answers"][0]
                self.assertEqual(answer["citation"], citation)
                self.assertEqual(answer["evidence_class"], "OBSERVED")
                for key, value in expected_values.items():
                    self.assertEqual(answer["value"][key], value)
                line_no = int(citation.rsplit(":", 1)[1])
                line_text = (FIXTURES / fixture).read_text(encoding="utf-8").splitlines()[line_no - 1]
                self.assertIn(json.dumps(query), line_text)

    def test_minified_bytes_cite_line_one(self):
        raw = json.dumps(json.loads((FIXTURES / "reusable-task-registry.json").read_text("utf-8"))).encode()
        result = build_index([{
            "repository": "StegVerse-Labs/.github",
            "path": "data/reusable-task-registry.json",
            "revision": "r1",
            "sha256": sha256(raw).hexdigest(),
            "bytes": raw,
        }])
        self.assertEqual(result.status, "ALLOW")
        answer = lookup(result.index, "RT-README-VALIDATION-001")["answers"][0]
        self.assertEqual(answer["citation"], "StegVerse-Labs/.github@r1:data/reusable-task-registry.json:1")

    def test_miss_returns_not_found_with_six_fields(self):
        index = built_index()
        for query in (
            "NO-SUCH-TASK-001",
            "ecosystem_chat",  # case differs: exact match only
            "SHWP-ECOSYSTEM-CHAT",  # prefix: no fuzzy matching
            "DEP-QUANTUM-RESIDENT-AWARENESS",  # nested id, not indexed
            "",
        ):
            with self.subTest(query=query):
                result = lookup(index, query)
                self.assertEqual(result["status"], "NOT_FOUND")
                for field in SIX_FIELDS:
                    self.assertTrue(str(result[field]).strip(), field)
                self.assertEqual(result["failure_code"], "ECOSYSTEM_FACT_NOT_FOUND")
                self.assertEqual(result["failed_predicate"], "FACT_PRESENT_IN_SUPPLIED_REGISTRIES")
                self.assertEqual(result["retry_entrypoint"], "llm_adapter.ecosystem_fact_index.lookup")
                self.assertEqual(result["owning_existing_goal"], "SHWP-ECOSYSTEM-CHAT-INFERENCE-001")
                self.assertNotIn("answers", result)

    def test_kind_filter_is_exact(self):
        index = built_index()
        self.assertEqual(lookup(index, "Ecosystem_Chat", kind="canonical_task")["status"], "NOT_FOUND")
        self.assertEqual(lookup(index, "Ecosystem_Chat", kind="organization_entity")["status"], "ANSWER")

    def test_digest_mismatch_refuses_whole_build(self):
        tampered = fixture_sources()
        tampered[1]["bytes"] = tampered[1]["bytes"].replace(b'"ACTIVE"', b'"CLOSED"')
        wrong_declared = fixture_sources()
        wrong_declared[0]["sha256"] = "0" * 64
        for sources in (tampered, wrong_declared):
            result = build_index(sources)
            self.assertEqual(result.status, "REFUSED")
            self.assertIsNone(result.index)
            refusal = result.to_dict()
            self.assertNotEqual(refusal["status"], "ALLOW")
            for field in SIX_FIELDS:
                self.assertTrue(str(refusal[field]).strip(), field)
            self.assertEqual(refusal["failure_code"], "ECOSYSTEM_FACT_SOURCE_DIGEST_MISMATCH")
            self.assertEqual(refusal["failed_predicate"], "REGISTRY_BYTES_MATCH_DECLARED_SHA256")
            self.assertEqual(refusal["owning_existing_goal"], "SHWP-ECOSYSTEM-CHAT-INFERENCE-001")
            self.assertNotEqual(refusal["source"]["observed_sha256"], refusal["source"]["declared_sha256"])

    def test_unsupported_and_unrecognized_sources_refuse(self):
        unsupported = fixture_sources()
        unsupported[0]["repository"] = "SV-LLM/other"
        self.assertEqual(build_index(unsupported).refusal["failure_code"], "ECOSYSTEM_FACT_SOURCE_UNSUPPORTED")

        wrong_schema = fixture_sources()[:1]
        payload = (FIXTURES / "reusable-task-registry.json").read_bytes()
        wrong_schema[0].update(path="data/organization-tree.json", bytes=payload, sha256=sha256(payload).hexdigest())
        refusal = build_index(wrong_schema).refusal
        self.assertEqual(refusal["failure_code"], "ECOSYSTEM_FACT_SOURCE_SCHEMA_UNRECOGNIZED")
        self.assertEqual(refusal["failed_predicate"], "REGISTRY_SCHEMA_RECOGNIZED")

        self.assertEqual(build_index([]).refusal["failure_code"], "ECOSYSTEM_FACT_SOURCES_EMPTY")
        duplicate = fixture_sources()[:1] * 2
        self.assertEqual(build_index(duplicate).refusal["failure_code"], "ECOSYSTEM_FACT_SOURCE_DUPLICATE")

    def test_no_network_or_subprocess_used(self):
        sources = fixture_sources()
        patches = no_io_patches()
        for patch in patches:
            patch.start()
        try:
            result = build_index(sources)
            self.assertEqual(result.status, "ALLOW")
            self.assertEqual(lookup(result.index, "QUANTUM-RESILIENCE-001")["status"], "ANSWER")
            response = backend.build_ai_entry_backend_response(
                "What does the registry say about QUANTUM-RESILIENCE-001?",
                ecosystem_fact_sources=sources,
            )
            self.assertEqual(response.primary_route, "ecosystem_fact_index")
        finally:
            for patch in reversed(patches):
                patch.stop()

    def test_load_source_manifest_reads_only_named_local_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "sources.json"
            manifest.write_text(json.dumps({
                "schema": "stegverse.ecosystem-fact-sources/v1",
                "sources": [
                    {
                        "repository": repository,
                        "path": path,
                        "revision": REVISION,
                        "sha256": digest,
                        "local_path": str(FIXTURES / name),
                    }
                    for repository, path, name, digest in PINNED_FIXTURES
                ],
            }), encoding="utf-8")
            loaded = load_source_manifest(manifest)
        self.assertEqual([item["bytes"] for item in loaded], [item["bytes"] for item in fixture_sources()])
        self.assertEqual(build_index(loaded).status, "ALLOW")


class EcosystemFactIndexHardeningTests(unittest.TestCase):
    """PR #426 review: nesting bound, duplicate keys and exact (unstripped) lookup."""

    def assert_six_field_refusal(self, refusal: dict, failure_code: str) -> None:
        self.assertEqual(refusal["status"], "REFUSED")
        for field in SIX_FIELDS:
            self.assertTrue(str(refusal[field]).strip(), field)
        self.assertEqual(refusal["failure_code"], failure_code)
        self.assertEqual(refusal["owning_existing_goal"], "SHWP-ECOSYSTEM-CHAT-INFERENCE-001")
        self.assertEqual(refusal["authority_effect"], "NONE")

    def test_nesting_bound_is_below_effective_frame_budget(self):
        # Each nesting level costs two Python frames (parse_value + parse_object/array).
        self.assertLessEqual(fact_index_module._MAX_DEPTH, 128)
        self.assertLess(2 * fact_index_module._MAX_DEPTH + 50, __import__("sys").getrecursionlimit())

    def test_nesting_at_limit_is_indexed(self):
        result = build_index([nested_organization_tree_source(fact_index_module._MAX_DEPTH)])
        self.assertEqual(result.status, "ALLOW", result.to_dict())
        self.assertEqual(lookup(result.index, "Deep_Entity")["status"], "ANSWER")

    def test_nesting_beyond_limit_refuses_without_recursion_error(self):
        for depth in (fact_index_module._MAX_DEPTH + 1, 129, 600, 5000):
            with self.subTest(depth=depth):
                result = build_index([nested_organization_tree_source(depth)])
                self.assertEqual(result.status, "REFUSED")
                self.assertIsNone(result.index)
                refusal = result.to_dict()
                self.assert_six_field_refusal(refusal, "ECOSYSTEM_FACT_SOURCE_NESTING_TOO_DEEP")
                self.assertEqual(refusal["failed_predicate"], "REGISTRY_NESTING_WITHIN_BOUND")
                self.assertEqual(refusal["source"]["path"], "data/organization-tree.json")

    def test_recursion_error_is_refused_even_if_bound_is_not_reached(self):
        with mock.patch.object(fact_index_module, "_MAX_DEPTH", 10 ** 6):
            result = build_index([nested_organization_tree_source(5000)])
        self.assertEqual(result.status, "REFUSED")
        self.assert_six_field_refusal(result.to_dict(), "ECOSYSTEM_FACT_SOURCE_NESTING_TOO_DEEP")

    def test_duplicate_json_keys_refuse(self):
        top_level = raw_source(
            "SV-LLM/.github", "data/organization-tree.json",
            b'{"schema": "sv-llm.organization-tree/v1",\n "repositories": [],\n'
            b' "repositories": [{"name": "Shadow_Entity"}]}',
        )
        nested = raw_source(
            "StegVerse-Labs/.github", "data/canonical-task-registry.json",
            b'{"schema": "stegverse.canonical-task-registry/v1", "tasks": [\n'
            b'  {"task_id": "TASK-A-001",\n   "task_id": "TASK-B-001"}]}',
        )
        invariant = raw_source(
            "StegVerse-Labs/.github", "data/task-registry-global-invariants.json",
            b'{"schema": "stegverse.task-registry-global-invariants/v1", "invariants": '
            b'{"k": 1, "k": 2}}',
        )
        for source, line in ((top_level, 3), (nested, 3), (invariant, 1)):
            with self.subTest(path=source["path"]):
                result = build_index([source])
                self.assertEqual(result.status, "REFUSED")
                self.assertIsNone(result.index)
                refusal = result.to_dict()
                self.assert_six_field_refusal(refusal, "ECOSYSTEM_FACT_SOURCE_DUPLICATE_KEY")
                self.assertEqual(refusal["failed_predicate"], "REGISTRY_OBJECT_KEYS_UNIQUE")
                self.assertTrue(refusal["detail"].endswith(f"_at_line_{line}"), refusal["detail"])

    def test_lookup_matches_exactly_without_whitespace_normalization(self):
        index = built_index()
        self.assertEqual(lookup(index, "QUANTUM-RESILIENCE-001")["status"], "ANSWER")
        for query in (" QUANTUM-RESILIENCE-001", "QUANTUM-RESILIENCE-001 ", "QUANTUM-RESILIENCE-001\n", "\tEcosystem_Chat"):
            with self.subTest(query=query):
                result = lookup(index, query)
                self.assertEqual(result["status"], "NOT_FOUND")
                self.assertEqual(result["query"], query)
        self.assertEqual(lookup(index, None)["status"], "NOT_FOUND")

    def test_deeply_nested_manifest_raises_config_error_not_recursion_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "sources.json"
            manifest.write_text("[" * 200000 + "]" * 200000, encoding="utf-8")
            with self.assertRaises(EcosystemFactSourceConfigError):
                load_source_manifest(manifest)


class AIEntryEcosystemFactRouteTests(unittest.TestCase):
    MESSAGES = (
        "",
        "hello",
        "Compare StegVerse with ChatGPT",
        "How do I access the SDK?",
        "What is StegVerse?",
        "Explain governance admissibility",
        "What is the coordination state of NO-SUCH-TASK-999?",
        "Show the registry record for NO-SUCH-TASK-999",
    )

    def setUp(self):
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        os.environ.pop(backend.ECOSYSTEM_FACT_SOURCES_ENV, None)
        self.addCleanup(patcher.stop)

    def test_unconfigured_responses_are_unchanged(self):
        for message in self.MESSAGES + ("Show the registry record for QUANTUM-RESILIENCE-001",):
            with self.subTest(message=message):
                default = backend.build_ai_entry_backend_response(message).to_dict()
                explicit_none = backend.build_ai_entry_backend_response(message, ecosystem_fact_sources=None).to_dict()
                self.assertEqual(default, explicit_none)
                self.assertNotEqual(default["primary_route"], "ecosystem_fact_index")
                self.assertNotIn("evidence_class", default["governance"])

    def test_configured_registry_question_returns_cited_observed_answer(self):
        response = backend.build_ai_entry_backend_response(
            "Show the registry record for QUANTUM-RESILIENCE-001",
            ecosystem_fact_sources=fixture_sources(),
        )
        citation = "StegVerse-Labs/.github@fixture-subset:data/canonical-task-registry.json:29"
        self.assertEqual(response.primary_route, "ecosystem_fact_index")
        self.assertIn(citation, response.stegverse_response)
        self.assertIn('"coordination_state": "PROPOSED"', response.stegverse_response)
        self.assertIn(citation, response.route_guidance)
        self.assertEqual(response.governance["evidence_class"], "OBSERVED")
        self.assertEqual(response.governance["ecosystem_fact_citations"], [citation])
        decision = response.governance["source_decisions"][0]
        self.assertEqual(decision["status"], "ALLOW_OBSERVED_REGISTRY_FACT")
        self.assertEqual(decision["fact_label"], "observed_registry_fact")
        self.assertEqual(decision["evidence_class"], "OBSERVED")
        self.assertIs(decision["allowed_as_authority"], False)
        self.assertIs(response.governance["authority_issued"], False)

    def test_configured_via_environment_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "sources.json"
            manifest.write_text(json.dumps({
                "schema": "stegverse.ecosystem-fact-sources/v1",
                "sources": [
                    {"repository": r, "path": p, "revision": REVISION, "sha256": d, "local_path": str(FIXTURES / n)}
                    for r, p, n, d in PINNED_FIXTURES
                ],
            }), encoding="utf-8")
            with mock.patch.dict(os.environ, {backend.ECOSYSTEM_FACT_SOURCES_ENV: str(manifest)}):
                response = backend.build_ai_entry_backend_response("Registry entry for StegVerse_AI")
        self.assertEqual(response.primary_route, "ecosystem_fact_index")
        self.assertIn("SV-LLM/.github@fixture-subset:data/organization-tree.json:22", response.stegverse_response)

    def assert_surfaced_refusal(self, response, baseline, failure_code: str) -> dict:
        """Answer text and route come from the existing resolvers; the refusal is visible."""

        configured = response.to_dict()
        refusal = configured["governance"].pop("ecosystem_fact_index_refusal")
        self.assertEqual(configured, baseline.to_dict())
        self.assertEqual(refusal["status"], "REFUSED")
        for field in SIX_FIELDS:
            self.assertTrue(str(refusal[field]).strip(), field)
        self.assertEqual(refusal["failure_code"], failure_code)
        self.assertEqual(refusal["owning_existing_goal"], "SHWP-ECOSYSTEM-CHAT-INFERENCE-001")
        self.assertEqual(refusal["authority_effect"], "NONE")
        self.assertIs(response.governance["authority_issued"], False)
        self.assertNotEqual(response.primary_route, "ecosystem_fact_index")
        self.assertNotIn("evidence_class", response.governance)
        return refusal

    def test_miss_falls_through_to_existing_fallback(self):
        for message in self.MESSAGES:
            with self.subTest(message=message):
                baseline = backend.build_ai_entry_backend_response(message).to_dict()
                configured = backend.build_ai_entry_backend_response(
                    message, ecosystem_fact_sources=fixture_sources()
                ).to_dict()
                self.assertEqual(configured, baseline)
                self.assertNotIn("ecosystem_fact_index_refusal", configured["governance"])

    def test_refused_sources_are_surfaced_not_silent(self):
        tampered = fixture_sources()
        tampered[1]["sha256"] = "f" * 64
        wrong_schema = fixture_sources()[:1]
        payload = (FIXTURES / "reusable-task-registry.json").read_bytes()
        wrong_schema[0].update(path="data/organization-tree.json", bytes=payload, sha256=sha256(payload).hexdigest())
        duplicate_key = [raw_source(
            "SV-LLM/.github", "data/organization-tree.json",
            b'{"schema": "sv-llm.organization-tree/v1", "schema": "sv-llm.organization-tree/v1", "repositories": []}',
        )]
        cases = (
            (tampered, "ECOSYSTEM_FACT_SOURCE_DIGEST_MISMATCH"),
            (wrong_schema, "ECOSYSTEM_FACT_SOURCE_SCHEMA_UNRECOGNIZED"),
            (duplicate_key, "ECOSYSTEM_FACT_SOURCE_DUPLICATE_KEY"),
            ([], "ECOSYSTEM_FACT_SOURCES_EMPTY"),
        )
        messages = self.MESSAGES[1:] + ("Show the registry record for QUANTUM-RESILIENCE-001",)
        for sources, failure_code in cases:
            for message in messages:
                with self.subTest(failure_code=failure_code, message=message):
                    baseline = backend.build_ai_entry_backend_response(message)
                    response = backend.build_ai_entry_backend_response(message, ecosystem_fact_sources=sources)
                    self.assert_surfaced_refusal(response, baseline, failure_code)
        refused = backend.build_ai_entry_backend_response(
            "Show the registry record for QUANTUM-RESILIENCE-001",
            ecosystem_fact_sources=tampered,
        )
        self.assertIn("does not invent an answer", refused.stegverse_response)
        self.assertEqual(
            refused.governance["ecosystem_fact_index_refusal"]["failed_predicate"],
            "REGISTRY_BYTES_MATCH_DECLARED_SHA256",
        )

    def test_deeply_nested_source_does_not_raise_through_backend(self):
        message = "Registry entry for Deep_Entity"
        baseline = backend.build_ai_entry_backend_response(message)
        for depth in (fact_index_module._MAX_DEPTH + 1, 600):
            with self.subTest(depth=depth):
                response = backend.build_ai_entry_backend_response(
                    message, ecosystem_fact_sources=[nested_organization_tree_source(depth)]
                )
                self.assert_surfaced_refusal(response, baseline, "ECOSYSTEM_FACT_SOURCE_NESTING_TOO_DEEP")

    def test_bad_environment_manifest_is_surfaced_not_silent(self):
        message = "Show the registry record for QUANTUM-RESILIENCE-001"
        baseline = backend.build_ai_entry_backend_response(message)
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            wrong_schema = Path(tmp) / "wrong-schema.json"
            wrong_schema.write_text(json.dumps({"schema": "other/v1", "sources": []}), encoding="utf-8")
            missing_local = Path(tmp) / "missing-local.json"
            missing_local.write_text(json.dumps({
                "schema": "stegverse.ecosystem-fact-sources/v1",
                "sources": [{"repository": "SV-LLM/.github", "path": "data/organization-tree.json",
                             "revision": "r", "sha256": "0" * 64, "local_path": "absent.json"}],
            }), encoding="utf-8")
            deep = Path(tmp) / "deep.json"
            deep.write_text("[" * 200000 + "]" * 200000, encoding="utf-8")
            digest_mismatch = Path(tmp) / "mismatch.json"
            digest_mismatch.write_text(json.dumps({
                "schema": "stegverse.ecosystem-fact-sources/v1",
                "sources": [{"repository": r, "path": p, "revision": REVISION, "sha256": "f" * 64,
                             "local_path": str(FIXTURES / n)} for r, p, n, _d in PINNED_FIXTURES],
            }), encoding="utf-8")
            cases = (
                (missing, "ECOSYSTEM_FACT_SOURCE_MANIFEST_REFUSED", "ecosystem_fact_source_manifest_unavailable"),
                (wrong_schema, "ECOSYSTEM_FACT_SOURCE_MANIFEST_REFUSED", "ecosystem_fact_source_manifest_schema_unsupported"),
                (missing_local, "ECOSYSTEM_FACT_SOURCE_MANIFEST_REFUSED", "ecosystem_fact_source_unreadable"),
                (deep, "ECOSYSTEM_FACT_SOURCE_MANIFEST_REFUSED", "ecosystem_fact_source_manifest_unavailable"),
                (digest_mismatch, "ECOSYSTEM_FACT_SOURCE_DIGEST_MISMATCH", None),
            )
            for manifest, failure_code, detail in cases:
                with self.subTest(manifest=manifest.name):
                    with mock.patch.dict(os.environ, {backend.ECOSYSTEM_FACT_SOURCES_ENV: str(manifest)}):
                        response = backend.build_ai_entry_backend_response(message)
                    refusal = self.assert_surfaced_refusal(response, baseline, failure_code)
                    if detail is not None:
                        self.assertEqual(refusal["detail"], detail)
                        self.assertEqual(refusal["retry_entrypoint"], "llm_adapter.ecosystem_fact_index.load_source_manifest")
                        # Local filesystem paths are not echoed into the response.
                        self.assertNotIn(tmp, json.dumps(response.to_dict()))

    def test_exact_registry_identifier_takes_precedence(self):
        # LLM-adapter#368: an exact identifier with an admitted registry answer goes first.
        message = "Show the registry record for QUANTUM-RESILIENCE-001"
        self.assertIsNone(backend.resolve_public_question(message))
        configured = backend.build_ai_entry_backend_response(message, ecosystem_fact_sources=fixture_sources())
        self.assertEqual(configured.primary_route, "ecosystem_fact_index")
        self.assertNotIn("related_public_knowledge", configured.governance)

    def test_natural_language_without_identifier_keeps_public_knowledge(self):
        for message in ("What is StegVerse?", "What is ecosystem chat?"):
            with self.subTest(message=message):
                configured = backend.build_ai_entry_backend_response(message, ecosystem_fact_sources=fixture_sources())
                self.assertEqual(configured.primary_route, "public_knowledge")
                self.assertEqual(configured.to_dict(), backend.build_ai_entry_backend_response(message).to_dict())

    def test_tie_returns_registry_fact_with_related_public_knowledge(self):
        message = "What is the coordination state of SHWP-ECOSYSTEM-CHAT-INFERENCE-001?"
        public = backend.resolve_public_question(message)
        self.assertIsNotNone(public)
        unconfigured = backend.build_ai_entry_backend_response(message)
        self.assertEqual(unconfigured.primary_route, "public_knowledge")
        configured = backend.build_ai_entry_backend_response(message, ecosystem_fact_sources=fixture_sources())
        self.assertEqual(configured.primary_route, "ecosystem_fact_index")
        self.assertTrue(configured.stegverse_response.startswith("Observed in the supplied ecosystem registries: "))
        self.assertIn("SHWP-ECOSYSTEM-CHAT-INFERENCE-001", configured.stegverse_response)
        self.assertNotIn(public.answer, configured.stegverse_response)
        self.assertEqual(configured.governance["evidence_class"], "OBSERVED")
        self.assertEqual(
            configured.governance["related_public_knowledge"],
            {"entry_id": public.entry_id, "match": public.match, "source_ids": list(public.source_ids)},
        )
        self.assertIs(configured.governance["authority_issued"], False)

    def test_unconfigured_output_is_byte_identical_across_routes(self):
        messages = self.MESSAGES + (
            "What is the coordination state of SHWP-ECOSYSTEM-CHAT-INFERENCE-001?",
            "Show the registry record for QUANTUM-RESILIENCE-001",
            "Registry entry for StegVerse_AI",
            "Does StegVerse support iPhone?",
            "Which providers are available on Android?",
        )
        for message in messages:
            for route in (None, "public_help", "sdk_access_guidance"):
                with self.subTest(message=message, route=route):
                    default = backend.build_ai_entry_backend_response(message, declared_route_id=route)
                    explicit = backend.build_ai_entry_backend_response(
                        message, declared_route_id=route, ecosystem_fact_sources=None
                    )
                    self.assertEqual(
                        json.dumps(default.to_dict(), sort_keys=True).encode("utf-8"),
                        json.dumps(explicit.to_dict(), sort_keys=True).encode("utf-8"),
                    )
                    self.assertNotIn("related_public_knowledge", default.governance)
                    self.assertNotEqual(default.primary_route, "ecosystem_fact_index")

    def test_plain_lowercase_words_are_not_registry_lookups(self):
        response = backend.build_ai_entry_backend_response(
            "tell me about sandbox", ecosystem_fact_sources=fixture_sources()
        )
        self.assertNotEqual(response.primary_route, "ecosystem_fact_index")

    def test_registry_source_classification(self):
        ecosystem = load_profile(ROOT / "profiles" / "ecosystem-chat-llm.v1.json")
        pinned = evaluate_source(ecosystem, SourceCandidate(
            source_type="stegverse_registry", uri="https://github.com/x/y", admitted=True, content_hash="a" * 64,
        ))
        self.assertEqual(pinned.status, "ALLOW_OBSERVED_REGISTRY_FACT")
        self.assertEqual(pinned.fact_label, "observed_registry_fact")
        self.assertFalse(pinned.allowed_as_authority)
        unpinned = evaluate_source(ecosystem, SourceCandidate(
            source_type="stegverse_registry", uri="https://github.com/x/y", admitted=True,
        ))
        self.assertEqual(unpinned.reasons, ("registry_source_digest_missing",))
        claims = load_profile(ROOT / "profiles" / "va-claims-chat-llm.v1.json")
        denied = evaluate_source(claims, SourceCandidate(
            source_type="stegverse_registry", uri="https://github.com/x/y", admitted=True, content_hash="a" * 64,
        ))
        self.assertEqual(denied.status, "DENY_SOURCE")


if __name__ == "__main__":
    unittest.main()
