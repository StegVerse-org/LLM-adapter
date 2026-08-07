import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_admittedcode_review_packets import build_packet


def _load(rel):
    return json.loads((ROOT / rel).read_text())


def test_allow_packet_is_derived_from_canonical_simple_query_fixture():
    expected = build_packet(
        ROOT / "examples/end_to_end/simple_query.json",
        "stegverse-demo-allow-001",
        admitted=True,
    )
    actual = _load("examples/end_to_end/admittedcode_review/review_packet.allow.json")
    assert actual == expected
    assert actual["source_binding"]["expected_outcome"] == "ALLOW"
    assert actual["request"]["gcat_bcat"]["a"] <= min(
        actual["request"]["gcat_bcat"]["g"],
        actual["request"]["gcat_bcat"]["c"],
        actual["request"]["gcat_bcat"]["t"],
    )


def test_deny_packet_is_derived_from_canonical_action_candidate_fixture():
    expected = build_packet(
        ROOT / "examples/end_to_end/action_commit_candidate.json",
        "stegverse-demo-deny-001",
        admitted=False,
    )
    actual = _load("examples/end_to_end/admittedcode_review/review_packet.deny.json")
    assert actual == expected
    assert actual["source_binding"]["expected_outcome"] == "QUARANTINE"
    assert actual["request"]["gcat_bcat"]["a"] > min(
        actual["request"]["gcat_bcat"]["g"],
        actual["request"]["gcat_bcat"]["c"],
        actual["request"]["gcat_bcat"]["t"],
    )


def test_packets_remain_non_authorizing_and_secret_free():
    for rel in (
        "examples/end_to_end/admittedcode_review/review_packet.allow.json",
        "examples/end_to_end/admittedcode_review/review_packet.deny.json",
    ):
        packet = _load(rel)
        assert packet["authority_effect"] == "NONE"
        blob = json.dumps(packet).lower()
        for forbidden in ("api_key", "client_secret", "bearer "):
            assert forbidden not in blob
