#!/usr/bin/env sh
set -eu

: "${STEGVERSE_HIL_REVIEW_TOKEN:=local-review-token}"
: "${STEGVERSE_HIL_PUBLICATION_TOKEN:=local-publication-token}"
export STEGVERSE_HIL_REVIEW_TOKEN STEGVERSE_HIL_PUBLICATION_TOKEN

docker compose up --build -d

python - <<'PY'
import time
import urllib.request

url = "http://127.0.0.1:8000/user-llm/healthz"
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
    raise SystemExit(f"portable user-LLM service did not become healthy: {last}")
PY

STEGVERSE_USER_LLM_BASE_URL=http://127.0.0.1:8000/user-llm \
python scripts/user_llm_smoke_test.py
