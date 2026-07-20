#!/bin/sh
set -eu

python -m llm_adapter.custody_worker

exec uvicorn llm_adapter.combined_gateway:app \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
