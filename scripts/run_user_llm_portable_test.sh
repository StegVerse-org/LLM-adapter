#!/usr/bin/env sh
set -eu

: "${STEGVERSE_HIL_REVIEW_TOKEN:=local-review-token}"
: "${STEGVERSE_HIL_PUBLICATION_TOKEN:=local-publication-token}"
: "${PORT:=8000}"
export STEGVERSE_HIL_REVIEW_TOKEN STEGVERSE_HIL_PUBLICATION_TOKEN PORT

mkdir -p artifacts

docker compose up --build -d 2>&1 | tee artifacts/docker-compose-up.log

python - <<'PY'
import os
import time
import urllib.request

port = os.environ.get("PORT", "8000")
url = f"http://127.0.0.1:{port}/user-llm/healthz"
last = None
for _ in range(60):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status == 200:
                break
    except Exception as exc:
        last = exc
        time.sleep(1)
else:
    raise SystemExit(f"portable user-LLM service did not become healthy at {url}: {last}")
PY

STEGVERSE_USER_LLM_BASE_URL="http://127.0.0.1:${PORT}/user-llm" \
python scripts/user_llm_smoke_test.py
