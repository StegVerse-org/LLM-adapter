"""Deployment entrypoint exposing the combined gateway and bounded user-LLM test surface."""

from __future__ import annotations

from llm_adapter.attachment_intake import router as attachment_router
from llm_adapter.combined_gateway import app
from llm_adapter.math_solver_gateway import router as math_solver_router
from llm_adapter.user_llm_service import create_app
from llm_adapter.service_gateway_composed import (
    coinbase_skap_ingress,
    coinbase_skap_readiness,
)

app.include_router(math_solver_router)
app.include_router(attachment_router)
app.mount("/user-llm", create_app())

# Reuse the validated Service Gateway Coinbase SKAP handlers on the actual
# deployed gateway entrypoint. These routes stage ciphertext only and retain
# TV/TVC as credential authority.
app.add_api_route(
    "/api/coinbase/skap/readiness",
    coinbase_skap_readiness,
    methods=["GET"],
)
app.add_api_route(
    "/api/coinbase/skap/ingress",
    coinbase_skap_ingress,
    methods=["POST"],
    status_code=202,
)
