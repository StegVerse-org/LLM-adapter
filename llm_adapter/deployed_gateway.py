"""Deployment entrypoint exposing the combined gateway and bounded user-LLM test surface."""

from __future__ import annotations

from llm_adapter.combined_gateway import app
from llm_adapter.user_llm_service import create_app

app.mount("/user-llm", create_app())
