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
