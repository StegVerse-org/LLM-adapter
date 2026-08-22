"""Deployment entrypoint exposing the combined gateway and bounded user-LLM test surface."""

from __future__ import annotations

from llm_adapter.attachment_intake import router as attachment_router
from llm_adapter.combined_gateway import app
from llm_adapter.math_solver_gateway import router as math_solver_router
from llm_adapter.user_llm_service import create_app

app.include_router(math_solver_router)
app.include_router(attachment_router)
app.mount("/user-llm", create_app())
