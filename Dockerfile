FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    STEGVERSE_DATA_DIR=/var/lib/stegverse

WORKDIR /app

RUN addgroup --system stegverse \
    && adduser --system --ingroup stegverse stegverse \
    && mkdir -p /var/lib/stegverse \
    && chown -R stegverse:stegverse /var/lib/stegverse /app

COPY pyproject.toml README.md ./
COPY llm_adapter ./llm_adapter
RUN python -m pip install --upgrade pip \
    && python -m pip install '.[service]'

COPY scripts/container-entrypoint.sh /usr/local/bin/stegverse-entrypoint
RUN chmod 0755 /usr/local/bin/stegverse-entrypoint

USER stegverse
EXPOSE 8000
VOLUME ["/var/lib/stegverse"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'), timeout=3)"

ENTRYPOINT ["/usr/local/bin/stegverse-entrypoint"]
