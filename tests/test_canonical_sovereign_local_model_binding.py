#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path

from llm_adapter.http_provider_clients import StegVerseLocalHTTPProviderClient
from llm_adapter.provider_request import build_provider_request


def wait_health(base: str, proc: subprocess.Popen[str]) -> dict:
    deadline=time.time()+8
    while time.time()<deadline:
        if proc.poll() is not None: raise RuntimeError(f'canonical model runtime exited:{proc.returncode}')
        try:
            with urllib.request.urlopen(base+'/health',timeout=.5) as r:
                if r.status==200: return json.loads(r.read())
        except Exception: pass
        time.sleep(.1)
    raise RuntimeError('canonical local model runtime readiness timeout')

def main() -> int:
    root=Path(os.environ['MICRO_NODE_RUNTIME_DIR']).resolve()
    port=int(os.environ.get('CANONICAL_LOCAL_MODEL_PORT','11435'))
    base=f'http://127.0.0.1:{port}'
    proc=subprocess.Popen([sys.executable,str(root/'tools/run_sovereign_model.py'),'--host','127.0.0.1','--port',str(port)],cwd=root,text=True)
    try:
        health=wait_health(base,proc)
        assert health['state']=='READY' and health['third_party_inference_required'] is False
        request=build_provider_request(provider='stegverse-local',model=health['model'],messages=[{'role':'user','content':'governed sovereign inference proof'}],metadata={'binding_test':'canonical-micro-node-model'})
        response=StegVerseLocalHTTPProviderClient(base_url=base+'/v1/chat/completions',timeout_seconds=5).complete(request)
        assert response.output.strip()
        assert response.metadata['sovereign_endpoint'] is True
        assert response.metadata['third_party_execution_platform_required'] is False
        assert response.metadata['provider_credential_required'] is False
        print(json.dumps({'result':'PASS','model':health['model'],'model_hash':health['model_hash'],'request_hash':request.request_hash,'output':response.output,'provider_metadata':response.metadata},sort_keys=True))
        return 0
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()
if __name__=='__main__': raise SystemExit(main())
