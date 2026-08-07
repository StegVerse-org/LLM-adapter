#!/usr/bin/env python3
from __future__ import annotations
import json, pathlib, sys

REQUIRED_TOP = {"schema","packet_id","source_system","source_refs","request","consent","budget","evidence_refs","continuity_refs","authority_effect"}
REQUIRED_REQ = {"provider","model","purpose","output_schema","estimated_cost_microdollars","gcat_bcat"}


def validate(path: pathlib.Path):
    p = json.loads(path.read_text())
    missing = sorted(REQUIRED_TOP - set(p))
    if missing: raise ValueError(f"missing top-level fields: {missing}")
    if p["schema"] != "stegverse.admittedcode.review_packet.v1": raise ValueError("unexpected schema")
    if p["source_system"] != "StegVerse-org/LLM-adapter": raise ValueError("unexpected source system")
    if p["authority_effect"] != "NONE": raise ValueError("review packet must not grant authority")
    req_missing = sorted(REQUIRED_REQ - set(p["request"]))
    if req_missing: raise ValueError(f"missing request fields: {req_missing}")
    g = p["request"]["gcat_bcat"]
    if set(g) != {"g","c","a","t"}: raise ValueError("gcat_bcat requires g,c,a,t")
    blob = path.read_text().lower()
    for forbidden in ("api_key", "authorization", "bearer ", "client_secret"):
        if forbidden in blob: raise ValueError(f"secret-bearing field/token forbidden: {forbidden}")
    return p


def main():
    root = pathlib.Path(__file__).resolve().parents[1]
    paths = [root / "examples/end_to_end/admittedcode_review/review_packet.allow.json", root / "examples/end_to_end/admittedcode_review/review_packet.deny.json"]
    packets = [validate(p) for p in paths]
    assert packets[0]["consent"]["user_approved"] is True
    assert packets[1]["consent"]["user_approved"] is False
    print("PASS admittedcode review fixtures: 2/2")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
