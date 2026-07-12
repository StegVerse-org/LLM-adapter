"""Combined governed gateway application for Ecosystem Chat and External Chat."""
from __future__ import annotations

import os

from fastapi.middleware.cors import CORSMiddleware

from llm_adapter.ecosystem_chat_gateway import app
from llm_adapter.external_chat_api import router as external_chat_router
from llm_adapter.external_review_api import router as external_review_router

app.include_router(external_chat_router)
app.include_router(external_review_router)

# Outer CORS boundary for authenticated cooperative-review submissions. Provider,
# custody, reviewer, and submitter credentials are never exposed by the service.
allowed_origins = [
    value.strip()
    for value in os.getenv(
        "STEGVERSE_ALLOWED_ORIGINS",
        "https://stegverse-labs.github.io,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-SteGVerse-Session"],
)
