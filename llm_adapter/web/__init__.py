"""Standard-library web layer: ASGI app and routing, request models, test client and HTTP server.

Replaces FastAPI, Starlette, pydantic, uvicorn and httpx for this repository.
"""
from .app import (  # noqa: F401
    APIRouter, BaseHTTPMiddleware, Body, CORSMiddleware, Cookie, FastAPI, File, Form, HTMLResponse,
    HTTPException, Header, JSONResponse, PlainTextResponse, Query, RedirectResponse, Request,
    RequestValidationError, Response, UploadFile,
)
from .model import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator  # noqa: F401
