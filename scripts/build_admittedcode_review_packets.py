#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "examples/end_to_end/admittedcode_review"


def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def source_binding(path: pathlib.Path):
    obj = json.loads(path.read_text())
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "expected_outcome": obj["expected_outcome"],
        "sha256": hashlib.sha256(canonical_bytes(obj)).hexdigest(),
    }, obj


def build_packet(source_path: pathlib.Path, packet_id: str, *, admitted: bool):
    binding, source = source_binding(source_path)
    purpose = "informational_query" if admitted else "repository_mutation_candidate"
    pressure = 2 if admitted else 6
    transition_id = "fixture:transition-simple-query" if admitted else "fixture:transition-action-commit"
    return {
        "schema": "stegverse.admittedcode.review_packet.v1",
        "packet_id": packet_id,
        "source_system": "StegVerse-org/LLM-adapter",
        "source_refs": [binding["path"]],
        "source_binding": binding,
        "source_claim": {
            "description": source["description"],
            "query": source["query"],
        },
        "request": {
            "provider": "fixture-provider",
            "model": "fixture-model-v1",
            "purpose": purpose,
            "output_schema": "stegverse.demo.response.v1",
            "estimated_cost_microdollars": 500,
            "gcat_bcat": {"g": 5, "c": 5, "a": pressure, "t": 5},
        },
        "consent": {"purpose": purpose, "user_approved": True},
        "budget": {"max_microdollars": 1000},
        "evidence_refs": [f"fixture-source-sha256:{binding['sha256']}"],
        "continuity_refs": [transition_id],
        "authority_effect": "NONE",
    }


def write(path: pathlib.Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main():
    allow = build_packet(ROOT / "examples/end_to_end/simple_query.json", "stegverse-demo-allow-001", admitted=True)
    deny = build_packet(ROOT / "examples/end_to_end/action_commit_candidate.json", "stegverse-demo-deny-001", admitted=False)
    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / "review_packet.allow.json", allow)
    write(OUT / "review_packet.deny.json", deny)
    print("PASS built admittedcode review packets: 2/2")

if __name__ == "__main__":
    main()
