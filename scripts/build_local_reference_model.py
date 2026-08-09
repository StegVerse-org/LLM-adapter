#!/usr/bin/env python3
"""Build the repository-owned deterministic StegVerse local reference model."""
from __future__ import annotations
import hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models/stegverse-local-reference-v1"
CORPUS = MODEL_DIR / "corpus.txt"
WEIGHTS = MODEL_DIR / "weights.json"
MANIFEST = MODEL_DIR / "manifest.json"
TOKEN_RE = re.compile(r"[a-z0-9_-]+|[.!?]", re.I)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def build() -> tuple[dict, dict]:
    raw = CORPUS.read_bytes()
    text = raw.decode("utf-8")
    transitions: dict[str, Counter[str]] = defaultdict(Counter)
    starts: Counter[str] = Counter()
    for line in text.splitlines():
        tokens = [x.lower() for x in TOKEN_RE.findall(line)]
        if not tokens: continue
        starts[tokens[0]] += 1
        for a, b in zip(tokens, tokens[1:]): transitions[a][b] += 1
        transitions[tokens[-1]]["<eos>"] += 1
    weights = {
        "schema_version": "stegverse.local-language-model.weights.v1",
        "model_id": "stegverse-local-reference-v1",
        "algorithm": "deterministic-bigram-argmax",
        "starts": dict(sorted(starts.items())),
        "transitions": {k: dict(sorted(v.items())) for k, v in sorted(transitions.items())},
    }
    weights_bytes = (json.dumps(weights, indent=2, sort_keys=True) + "\n").encode()
    manifest = {
        "schema_version": "stegverse.local-language-model.manifest.v1",
        "model_id": "stegverse-local-reference-v1",
        "model_class": "repository_trained_count_language_model",
        "foundation_model": False,
        "training_method": "deterministic bigram counts over repository-owned corpus",
        "training_corpus_sha256": digest(raw),
        "weights_sha256": digest(weights_bytes),
        "runtime_protocol": "stegverse.local-runtime.v1",
        "network_required_for_training": False,
        "network_required_for_inference": False,
        "authority_attached": False,
    }
    return weights, manifest

def main() -> int:
    weights, manifest = build()
    WEIGHTS.write_text(json.dumps(weights, indent=2, sort_keys=True) + "\n")
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"model_id": manifest["model_id"], "weights_sha256": manifest["weights_sha256"]}))
    return 0
if __name__ == "__main__": raise SystemExit(main())
