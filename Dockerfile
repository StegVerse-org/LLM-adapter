FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN addgroup --system stegverse && adduser --system --ingroup stegverse stegverse

COPY pyproject.toml README.md ./
COPY llm_adapter ./llm_adapter
RUN python -m pip install --upgrade pip && python -m pip install '.[service]'

USER stegverse
EXPOSE 8000

CMD ["sh", "-c", "uvicorn llm_adapter.combined_gateway:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
