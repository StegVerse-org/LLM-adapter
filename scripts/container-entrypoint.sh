#!/bin/sh
set -eu

DATA_DIR="${STEGVERSE_DATA_DIR:-/var/lib/stegverse}"
PORT="${PORT:-8000}"

mkdir -p "$DATA_DIR"

export STEGVERSE_TRANSITION_DB="${STEGVERSE_TRANSITION_DB:-$DATA_DIR/stegverse-ecosystem-chat.db}"
export STEGVERSE_EXTERNAL_REVIEW_DB="${STEGVERSE_EXTERNAL_REVIEW_DB:-$DATA_DIR/stegverse-external-review.db}"
export STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS="${STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS:-true}"

python -m llm_adapter.custody_worker

exec uvicorn llm_adapter.combined_gateway:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips='*'
