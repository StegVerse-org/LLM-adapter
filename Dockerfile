FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

RUN addgroup --system stegverse \
    && adduser --system --ingroup stegverse --home /app stegverse

COPY pyproject.toml README.md ./
COPY llm_adapter ./llm_adapter
COPY scripts/start_gateway.sh ./scripts/start_gateway.sh

RUN python -m pip install --upgrade pip \
    && python -m pip install '.[service]' \
    && chmod +x ./scripts/start_gateway.sh \
    && mkdir -p /var/lib/stegverse \
    && chown -R stegverse:stegverse /app /var/lib/stegverse

USER stegverse
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8080')+'/health', timeout=4)" || exit 1

ENTRYPOINT ["./scripts/start_gateway.sh"]
