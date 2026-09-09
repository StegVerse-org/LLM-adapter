"""Deployment entrypoint exposing the combined gateway and bounded user-LLM test surface."""

from __future__ import annotations

import logging

from llm_adapter.attachment_intake import router as attachment_router
from llm_adapter.combined_gateway import app
from llm_adapter.math_solver_gateway import router as math_solver_router
from llm_adapter.user_llm_service import create_app
from llm_adapter.service_gateway_composed import (
    coinbase_skap_ingress,
    coinbase_skap_readiness,
)
from llm_adapter.service_gateway_http01 import http01_challenge_response
from llm_adapter.service_gateway_evaluator_intr import router as evaluator_intr_router
from llm_adapter.service_gateway_hil_intr import router as hil_intr_router
from llm_adapter.service_gateway_sv002_observation import router as sv002_observation_router
from llm_adapter.service_gateway_personal_origin import personal_origin_middleware
from llm_adapter.query_safe_access_log import QuerySecretSafeAccessLogMiddleware

# Render launches this module with Uvicorn directly rather than through
# runtime_gateway.main(). Uvicorn configures its loggers before importing the app,
# so disabling the request-target access logger here prevents its default
# `"GET /path?query HTTP/1.1"` record from persisting callback query material.
# The Gateway-owned path-only logger below remains enabled separately.
logging.getLogger("uvicorn.access").disabled = True

app.include_router(math_solver_router)
app.include_router(attachment_router)
app.include_router(evaluator_intr_router)
app.include_router(hil_intr_router)
app.include_router(sv002_observation_router)
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

# Serve only TVC-projected public ACME HTTP-01 key-authorization bytes.
# This route has no mutation, signing, CA, credential, or provider authority.
app.add_api_route(
    "/.well-known/acme-challenge/{token}",
    http01_challenge_response,
    methods=["GET"],
)

# Isolate the dedicated stegverse.me virtual origin from the rest of the shared
# Gateway API surface. The middleware only serves the verified public bundle;
# all other personal-origin paths fail closed.
app.middleware("http")(personal_origin_middleware)

# Wrap the fully composed production entrypoint after all routers/middleware are
# installed. This logger records only method + canonical path + status and never
# reads query_string/raw_path/headers/body. Deployed observation is still required
# before the public callback can be represented as query-safe at runtime.
app = QuerySecretSafeAccessLogMiddleware(app)
