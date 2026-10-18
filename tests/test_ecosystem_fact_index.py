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
from llm_adapter.chat_profiles import SourceCandidate, evaluate_source, load_profile
from llm_adapter.ecosystem_fact_index import (
    EcosystemFactIndex,
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

    def test_miss_and_refusal_fall_through_to_existing_fallback(self):
        tampered = fixture_sources()
        tampered[1]["sha256"] = "f" * 64
        for message in self.MESSAGES:
            baseline = backend.build_ai_entry_backend_response(message).to_dict()
            for sources in (fixture_sources(), tampered):
                with self.subTest(message=message):
                    configured = backend.build_ai_entry_backend_response(
                        message, ecosystem_fact_sources=sources
                    ).to_dict()
                    self.assertEqual(configured, baseline)
        refused = backend.build_ai_entry_backend_response(
            "Show the registry record for QUANTUM-RESILIENCE-001",
            ecosystem_fact_sources=tampered,
        )
        self.assertNotEqual(refused.primary_route, "ecosystem_fact_index")
        self.assertIn("does not invent an answer", refused.stegverse_response)
        self.assertEqual(
            refused.to_dict(),
            backend.build_ai_entry_backend_response("Show the registry record for QUANTUM-RESILIENCE-001").to_dict(),
        )

    def test_earlier_resolvers_keep_precedence(self):
        # Public knowledge is consulted first; the registry index is the third resolver.
        message = "What is the coordination state of SHWP-ECOSYSTEM-CHAT-INFERENCE-001?"
        configured = backend.build_ai_entry_backend_response(message, ecosystem_fact_sources=fixture_sources())
        self.assertEqual(configured.primary_route, "public_knowledge")
        self.assertEqual(configured.to_dict(), backend.build_ai_entry_backend_response(message).to_dict())

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
