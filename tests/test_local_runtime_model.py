#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from llm_adapter.local_model_runtime import complete, ensure_local_runtime
from scripts.build_local_reference_model import build

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    weights, manifest = build()
    committed_weights = json.loads((ROOT/'models/stegverse-local-reference-v1/weights.json').read_text())
    committed_manifest = json.loads((ROOT/'models/stegverse-local-reference-v1/manifest.json').read_text())
    assert weights == committed_weights, 'committed weights are not reproducible from corpus'
    assert manifest == committed_manifest, 'committed manifest is not reproducible from corpus'
    first = complete('governed inference', max_tokens=12)
    second = complete('governed inference', max_tokens=12)
    assert first == second
    assert first['output']
    assert first['authority_attached'] is False and first['execution_authority'] is False
    discovery, launched = ensure_local_runtime()
    try:
        assert discovery['state'] in {'DISCOVERED','LAUNCHED_AND_DISCOVERED'}
        assert discovery['identity']['protocol'] == 'stegverse.local-runtime.v1'
        assert discovery['identity']['model_id'] == 'stegverse-local-reference-v1'
    finally:
        if launched is not None: launched.stop()
    print(json.dumps({'result':'PASS','model_id':manifest['model_id'],'weights_sha256':manifest['weights_sha256']}))
    return 0
if __name__ == '__main__': raise SystemExit(main())
