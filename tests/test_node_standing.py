"""Standing is a gate, not a statement, and the instructions sit behind it.

`CANONICAL-NODE-INGRESS-CONTRACT-001` requires every covered ecosystem entry
to establish explicit genesis standing or prove continuity from a canonical
predecessor, and says the continuation is exposed *after* that. The
advertisement served those instructions to anyone who asked, so reaching them
required nothing and the requirement was a statement rather than a gate.

These cases hold the gate. Both standing modes resolve, every neighbouring
declaration is refused with a named disposition rather than an opaque error, a
failed verification never becomes a genesis, and the instructions are released
on ALLOW and on nothing else.

They also hold what standing is *not*. An ALLOW here means a well-formed
declaration whose lineage holds; it does not mean the caller is authenticated,
and the disposition says so in its own fields.

Source validation only. Standing grants no execution, route, credential or
transition authority.
"""
from __future__ import annotations

import unittest

import pytest

from llm_adapter import node_standing as ns


def genesis(**overrides):
    request = {"mode": ns.ESTABLISH_GENESIS, "node_ref": "evaluator-node-1",
               "generation": 1, "predecessor": None}
    request.update(overrides)
    return request


def binding(generation=1, epoch=4096):
    return {"generation": generation, "manifest_sha256": "a" * 64,
            "result_sha256": "b" * 64, "heartbeat_epoch": epoch}


def existing(**overrides):
    request = {"mode": ns.VERIFY_EXISTING, "node_ref": "evaluator-node-1",
               "generation": 2, "predecessor": binding()}
    request.update(overrides)
    return request


# --- readiness publishes the requirement and grants nothing ------------------

def test_readiness_publishes_what_standing_requires():
    r = ns.readiness()
    assert r["contract_id"] == ns.CONTRACT_ID
    assert r["standing_modes"] == [ns.ESTABLISH_GENESIS, ns.VERIFY_EXISTING]
    assert r["predecessor_key_required"] is True
    assert r["null_predecessor_means"] == "EXPLICIT_GENESIS_ONLY"
    assert r["absent_predecessor_key_disposition"] == ns.FAIL_CLOSED
    assert r["instructions_released_only_on"] == ns.ALLOW


def test_readiness_is_not_standing_and_claims_no_authority():
    r = ns.readiness()
    assert r["readiness_is_not_standing"] is True
    assert r["authority_effect"] == "NONE_READINESS_ONLY"


def test_readiness_names_the_lineage_owner_rather_than_restating_the_rule():
    r = ns.readiness()
    assert r["lineage_owner"] == "StegVerse-org/StegVerse-SDK"
    assert any("successor_predecessor_binding" in f for f in r["lineage_functions"])


def test_readiness_says_ordering_is_an_oscillator_count():
    r = ns.readiness()
    assert r["ordering"] == "OSCILLATOR_HEARTBEAT_EPOCH_ONLY"
    assert r["wall_clock_ordering_permitted"] is False


def test_readiness_does_not_claim_authenticated_standing():
    r = ns.readiness()
    assert r["structural_standing_is_authenticated_standing"] is False
    assert r["attestation_owner_state"] == "NOT_PROVEN"
    assert r["caller_supplied_identity_is_not_authenticated"] is True


# --- both modes resolve ------------------------------------------------------

def test_explicit_genesis_resolves_allow():
    d = ns.resolve(genesis())
    assert d["disposition"] == ns.ALLOW
    assert d["standing_mode"] == ns.ESTABLISH_GENESIS
    assert d["generation"] == 1
    assert d["predecessor"] is None


def test_genesis_may_omit_generation_because_it_is_always_one():
    request = genesis(); del request["generation"]
    assert ns.resolve(request)["generation"] == 1


def test_verified_continuity_resolves_allow_and_carries_its_predecessor():
    d = ns.resolve(existing())
    assert d["disposition"] == ns.ALLOW
    assert d["standing_mode"] == ns.VERIFY_EXISTING
    assert d["generation"] == 2
    assert d["predecessor"] == binding()


def test_an_allow_is_structural_and_says_so():
    d = ns.resolve(genesis())
    assert d["structural_standing_only"] is True
    assert d["structural_standing_is_authenticated_standing"] is False
    assert d["attestation_owner_state"] == "NOT_PROVEN"
    assert d["authority_effect"] == "NONE_STANDING_ONLY"


# --- the predecessor key is mandatory ---------------------------------------

def test_an_absent_predecessor_key_fails_closed_rather_than_reading_as_genesis():
    request = genesis(); del request["predecessor"]
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(request)
    assert raised.value.disposition == ns.FAIL_CLOSED
    assert "predecessor must be declared" in raised.value.reason


def test_genesis_declaring_a_predecessor_is_denied():
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(genesis(predecessor=binding()))
    assert raised.value.disposition == ns.DENY


def test_genesis_claiming_a_later_generation_is_denied():
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(genesis(generation=3))
    assert raised.value.disposition == ns.DENY


# --- a failed verification never becomes a genesis --------------------------

def test_verify_existing_without_a_predecessor_fails_closed():
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(existing(predecessor=None))
    assert raised.value.disposition == ns.FAIL_CLOSED


def test_verify_existing_at_generation_one_fails_closed():
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(existing(generation=1))
    assert raised.value.disposition == ns.FAIL_CLOSED


def test_a_predecessor_that_does_not_precede_fails_closed_not_reenrolls():
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(existing(generation=5, predecessor=binding(generation=1)))
    assert raised.value.disposition == ns.FAIL_CLOSED
    assert "less one" in raised.value.reason


@pytest.mark.parametrize("field", ["manifest_sha256", "result_sha256"])
def test_a_predecessor_reference_that_is_not_a_digest_fails_closed(field):
    b = binding(); b[field] = "not-a-digest"
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(existing(predecessor=b))
    assert raised.value.disposition == ns.FAIL_CLOSED


def test_an_epoch_below_one_is_not_an_earlier_observation():
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(existing(predecessor=binding(epoch=0)))
    assert "oscillator count" in raised.value.reason


def test_an_unknown_predecessor_field_fails_closed():
    b = binding(); b["observed_at"] = "2026-10-02T00:00:00Z"
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(existing(predecessor=b))
    assert "unknown predecessor fields" in raised.value.reason


def test_a_missing_predecessor_field_fails_closed():
    b = binding(); del b["result_sha256"]
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(existing(predecessor=b))
    assert "missing predecessor fields" in raised.value.reason


# --- malformed requests get a disposition, not an opaque error --------------

def test_an_unsupported_mode_is_denied_by_name():
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(genesis(mode="REENROLL"))
    assert raised.value.disposition == ns.DENY
    assert "REENROLL" in raised.value.reason


def test_a_missing_node_ref_fails_closed():
    request = genesis(); del request["node_ref"]
    with pytest.raises(ns.StandingRefused) as raised:
        ns.resolve(request)
    assert raised.value.disposition == ns.FAIL_CLOSED


def test_a_non_object_request_fails_closed():
    for payload in (None, [], "ESTABLISH_GENESIS", 7):
        with pytest.raises(ns.StandingRefused) as raised:
            ns.resolve(payload)
        assert raised.value.disposition == ns.FAIL_CLOSED


def test_a_refusal_renders_as_a_disposition_releasing_nothing():
    try:
        ns.resolve(genesis(mode="REENROLL"))
    except ns.StandingRefused as refused:
        body = ns.refusal(refused, mode="REENROLL")
    assert body["disposition"] == ns.DENY
    assert body["instructions_released"] is False
    assert body["silent_reenrollment_occurred"] is False
    assert body["authority_effect"] == "NONE_REFUSAL_ONLY"
    assert body["reason"]


def test_predecessor_field_set_is_read_off_the_owner_not_declared_locally() -> None:
    """The owner defines a predecessor. This boundary must not define a second one."""
    from stegverse.external_interlock_bootstrap import (
        canonical_sha256,
        successor_predecessor_binding,
    )

    body = {"generation": 4}
    manifest = {**body, "manifest_sha256": canonical_sha256(body)}
    owner_binding = successor_predecessor_binding(
        predecessor_manifest=manifest, predecessor_result={"ok": True}, heartbeat_epoch=32)

    assert tuple(owner_binding) == ns.PREDECESSOR_FIELDS

    # And a binding the owner itself produced must be admissible as a
    # predecessor, which is the only way the two shapes staying equal matters.
    disposition = ns.resolve({
        "mode": "VERIFY_EXISTING",
        "node_ref": "external-reviewer-node",
        "generation": 5,
        "predecessor": owner_binding,
    })
    assert disposition["disposition"] == "ALLOW"
    assert disposition["generation"] == 5
    assert disposition["declared_predecessor_lineage_recomputed"] is False


class HealthyNodeGrantsTypedIngressTests(unittest.TestCase):
    """A device registers, is told it is a healthy node, and gets its own instructions."""

    def setUp(self):
        from fastapi.testclient import TestClient
        from llm_adapter.combined_gateway import app
        self.client = TestClient(app)

    def register(self, **overrides):
        body = {"mode": "ESTABLISH_GENESIS", "node_ref": "evaluator-node", "predecessor": None}
        body.update(overrides)
        return self.client.post("/api/node-standing", json=body)

    def test_a_registered_node_is_told_it_is_healthy(self):
        """The whole point of the first step: did I reach a healthy node?"""
        body = self.register(node_class="CONSOLE").json()
        self.assertEqual(body["disposition"], "ALLOW")
        self.assertIs(body["healthy_node_established"], True)
        # Health is the node's own health surface, so "healthy" means here what
        # it means at /health rather than being a separate assertion about it.
        self.assertEqual(body["node_health"], self.client.get("/health").json())
        self.assertEqual(body["node_health"]["status"], "ok")

    def test_a_console_class_node_is_sent_to_the_sdk_builder_first(self):
        body = self.register(node_class="CONSOLE").json()
        self.assertEqual(body["node_class"], "CONSOLE")
        self.assertEqual(body["continuation_profile"], "EXTERNAL_FRAMEWORK_MANIFEST_CONTINUATION")
        profile = body["machine_readable_instructions"][body["continuation_profile"]]
        self.assertIn("BUILD_AND_VALIDATE_CANONICAL_MANIFEST_WITH_SDK", profile["steps"])
        self.assertEqual(profile["sdk_builder_api"], "stegverse.manifest_builder.build_manifest")
        self.assertEqual(profile["sdk_builder_cli"], "stegverse manifest build")
        self.assertEqual(profile["receiving_owner"], "llm_adapter.governed_manifest_ingress")

    def test_an_adapter_class_node_is_sent_to_validate_and_submit(self):
        body = self.register(node_class="LLM_ADAPTER").json()
        self.assertEqual(body["node_class"], "LLM_ADAPTER")
        self.assertEqual(body["continuation_profile"], "LLM_MACHINE_CONTINUATION")
        profile = body["machine_readable_instructions"][body["continuation_profile"]]
        self.assertIn("VALIDATE_CANONICAL_MANIFEST_WITH_SDK", profile["steps"])
        self.assertNotIn("BUILD_AND_VALIDATE_CANONICAL_MANIFEST_WITH_SDK", profile["steps"])
        self.assertEqual(profile["submission_api"],
                         "llm_adapter.governed_manifest_ingress.process_manifest")

    def test_only_this_caller_s_profile_is_returned(self):
        """Instructions for the class that registered, not a dump of every one."""
        for declared, expected, other in (
                ("CONSOLE", "EXTERNAL_FRAMEWORK_MANIFEST_CONTINUATION", "LLM_MACHINE_CONTINUATION"),
                ("LLM_ADAPTER", "LLM_MACHINE_CONTINUATION", "EXTERNAL_FRAMEWORK_MANIFEST_CONTINUATION")):
            with self.subTest(node_class=declared):
                body = self.register(node_class=declared).json()
                self.assertEqual(list(body["machine_readable_instructions"]), [expected])
                self.assertEqual(body["other_continuation_profiles"], [other])

    def test_an_undeclared_node_class_fails_closed(self):
        """Guessing which instructions someone needs is the defaulting this forbids."""
        response = self.register()
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail["disposition"], "FAIL_CLOSED")
        self.assertIn("node_class", detail["reason"])
        self.assertIs(detail["instructions_released"], False)

    def test_an_unrecognised_node_class_fails_closed(self):
        response = self.register(node_class="SOMETHING_ELSE")
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail["disposition"], "FAIL_CLOSED")
        self.assertIs(detail["instructions_released"], False)
        self.assertNotIn("machine_readable_instructions", detail)

    def test_declared_ingress_dimensions_are_recorded_and_not_believed(self):
        """`caller_editable_ingress_source_field` is forbidden as authoritative evidence."""
        declared = {"participant": "EXTERNAL_FRAMEWORK_OR_LLM",
                    "interaction_surface": "API_OR_MACHINE_CLIENT"}
        body = self.register(node_class="CONSOLE", ingress=declared).json()
        self.assertEqual(body["declared_ingress_dimensions"], declared)
        self.assertIs(body["ingress_classification_is_caller_declared"], True)
        self.assertIs(body["ingress_classification_is_authoritative"], False)
        self.assertIs(body["ingress_dimensions_select_processing"], False)

    def test_no_standing_means_no_instructions_at_all(self):
        response = self.client.post("/api/node-standing",
                                    json={"mode": "ESTABLISH_GENESIS", "node_ref": "x",
                                          "node_class": "LLM_ADAPTER"})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("machine_readable_instructions", response.json()["detail"])

    def test_readiness_tells_a_caller_what_to_declare(self):
        ready = self.client.get("/api/node-standing/readiness").json()
        self.assertEqual(ready["continuation_selector"], "node_class")
        self.assertIs(ready["continuation_selector_required"], True)
        self.assertEqual(sorted(ready["node_classes"]), ["CONSOLE", "LLM_ADAPTER"])
        self.assertIs(ready["ingress_classification_is_authoritative"], False)
