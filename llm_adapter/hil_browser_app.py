"""Receiver-hosted browser submission surface for governed HIL intake."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse


def create_hil_browser_app() -> FastAPI:
    app = FastAPI(title="StegVerse HIL Submission Surface", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return PAGE

    return app


PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>StegVerse HIL Submission</title>
<style>
:root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#151515;background:#f4f5f7}
body{margin:0;padding:24px}.card{max-width:760px;margin:auto;background:white;border:1px solid #d8dce3;border-radius:14px;padding:24px;box-shadow:0 8px 28px #0001}
h1{margin-top:0}.row{margin:14px 0}label{display:block;font-weight:650;margin-bottom:6px}input,select,button,textarea{box-sizing:border-box;width:100%;font:inherit;padding:11px;border:1px solid #b9bec8;border-radius:8px}
.check{display:flex;gap:10px;align-items:flex-start}.check input{width:auto;margin-top:4px}.check label{font-weight:500}.primary{background:#111;color:white;border:0;font-weight:700;cursor:pointer}.primary:disabled{opacity:.55;cursor:wait}
.status{padding:12px;border-radius:8px;background:#eef2f7;white-space:pre-wrap}.ok{background:#e8f7ed}.bad{background:#fdecec}pre{overflow:auto;background:#111;color:#eee;padding:14px;border-radius:8px;min-height:80px}
.small{font-size:.9rem;color:#555}
</style>
</head>
<body><main class="card">
<h1>StegVerse HIL Submission</h1>
<p>Choose the response PDF. This page reads the receiver contract, calculates the SHA-256, creates the provenance manifest, submits the packet, and returns the receipt.</p>
<div class="row"><label for="pdf">Response PDF</label><input id="pdf" type="file" accept="application/pdf,.pdf" required></div>
<div class="row"><label for="participant">Participant identifier</label><input id="participant" value="local-controlled-test-001"></div>
<div class="row"><label for="consent">Publication consent</label><select id="consent"><option value="not_provided">Not provided</option><option value="private">Private</option><option value="anonymous">Anonymous</option><option value="public">Public</option></select></div>
<div class="row check"><input id="unedited" type="checkbox"><label for="unedited">I declare that the model response PDF is unedited.</label></div>
<div class="row check"><input id="authority" type="checkbox"><label for="authority">I acknowledge authority for the participant consent selection.</label></div>
<div class="row"><button id="submit" class="primary">Build manifest and submit</button></div>
<div id="status" class="status">Ready. No shell commands or manual hashes are required.</div>
<div class="row"><label>Receiver result</label><pre id="result">No submission yet.</pre></div>
<p class="small">This surface does not grant review, publication, custody, Master-Records append, or execution authority. Receiver-side validation remains authoritative.</p>
</main>
<script>
const $ = id => document.getElementById(id);
const hex = buffer => [...new Uint8Array(buffer)].map(x=>x.toString(16).padStart(2,'0')).join('');
function setStatus(text, cls=''){ $('status').className='status '+cls; $('status').textContent=text; }
function download(name, object){ const blob=new Blob([JSON.stringify(object,null,2)+'\n'],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000); }
$('submit').addEventListener('click', async () => {
  const button=$('submit'); const file=$('pdf').files[0];
  if(!file){ setStatus('Choose a PDF first.','bad'); return; }
  button.disabled=true; $('result').textContent='Working...';
  try{
    setStatus('Reading receiver readiness...');
    const readyResponse=await fetch('/api/hil/readiness',{headers:{Accept:'application/json'}});
    const readiness=await readyResponse.json();
    if(!readyResponse.ok || readiness.state!=='READY') throw new Error('Receiver is not READY: '+JSON.stringify(readiness));
    setStatus('Calculating PDF SHA-256...');
    const responseSha=hex(await crypto.subtle.digest('SHA-256',await file.arrayBuffer()));
    const manifest={
      schema_version:readiness.provenance_manifest_schema,
      primary_version:readiness.primary_version,
      primary_sha256:readiness.primary_sha256,
      protocol_version:readiness.protocol_version,
      prompt_version:readiness.prompt_version,
      prompt_sha256:readiness.prompt_sha256,
      response_sha256:responseSha,
      producer_signature:{state:'UNAVAILABLE',scheme:null,value:null,key_id:null}
    };
    const form=new FormData();
    form.append('response_pdf',file,file.name);
    form.append('provenance_manifest',new Blob([JSON.stringify(manifest,null,2)+'\n'],{type:'application/json'}),'hil-provenance-manifest.json');
    form.append('participant_identifier',$('participant').value||'not_provided');
    form.append('publication_consent',$('consent').value);
    form.append('primary_sha256',manifest.primary_sha256);
    form.append('prompt_sha256',manifest.prompt_sha256);
    form.append('model_response_declared_unedited',String($('unedited').checked));
    form.append('participant_consent_authority_acknowledged',String($('authority').checked));
    setStatus('Submitting governed packet...');
    const response=await fetch('/api/hil/submissions',{method:'POST',body:form,headers:{Accept:'application/json'}});
    const text=await response.text(); let payload; try{payload=JSON.parse(text)}catch{payload={raw:text}};
    $('result').textContent=JSON.stringify(payload,null,2);
    if(!response.ok) throw new Error('Submission rejected with HTTP '+response.status+': '+JSON.stringify(payload));
    setStatus('Submission accepted. Manifest and receipt are ready to save.','ok');
    const stem=file.name.replace(/\.pdf$/i,'');
    download(stem+'.hil-provenance.json',manifest);
    download(stem+'.hil-receipt.json',payload);
  }catch(error){ setStatus(String(error.message||error),'bad'); }
  finally{ button.disabled=false; }
});
</script></body></html>'''
