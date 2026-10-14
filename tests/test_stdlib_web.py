"""The standard-library web layer that replaces FastAPI, Starlette, pydantic, uvicorn and httpx (LLMA-368)."""
from __future__ import annotations

import asyncio
import json
import socket
import threading
import unittest
import urllib.request
from typing import Any, Literal, Optional

from llm_adapter.web import (
    APIRouter, BaseHTTPMiddleware, CORSMiddleware, Cookie, FastAPI, File, Form, Header, HTTPException, Query,
    Request, Response, UploadFile,
)
from llm_adapter.web import server as web_server
from llm_adapter.web.model import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from llm_adapter.web.testclient import TestClient


class Inner(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ref: str = Field(min_length=1, max_length=8)


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=16)
    digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{4}$")
    kind: Literal["A", "B"] = "A"
    flag: bool = False
    tags: list[str] = Field(default_factory=list, max_length=2)
    counts: dict[str, int] = Field(default_factory=dict)
    inner: Optional[Inner] = None

    @field_validator("name")
    @classmethod
    def no_spaces(cls, value: str) -> str:
        if " " in value:
            raise ValueError("name must not contain spaces")
        return value

    @model_validator(mode="after")
    def b_requires_flag(self) -> "Payload":
        if self.kind == "B" and not self.flag:
            raise ValueError("kind B requires flag")
        return self


class ModelTests(unittest.TestCase):
    def test_valid_payload_dumps_with_defaults(self) -> None:
        value = Payload.model_validate({"name": "x", "counts": {"a": "2"}, "inner": {"ref": "r"}})
        self.assertEqual(value.model_dump(), {"name": "x", "digest": None, "kind": "A", "flag": False,
                                              "tags": [], "counts": {"a": 2}, "inner": {"ref": "r"}})

    def test_every_constraint_is_enforced(self) -> None:
        bad = [
            {"name": ""}, {"name": "x" * 17}, {"name": "a b"}, {"name": 5}, {"name": "x", "digest": "zzzz"},
            {"name": "x", "kind": "C"}, {"name": "x", "tags": ["a", "b", "c"]}, {"name": "x", "extra": 1},
            {"name": "x", "kind": "B"}, {"name": "x", "inner": {"ref": "r", "more": 1}}, {},
        ]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                Payload.model_validate(data)

    def test_extra_allow_keeps_unknown_fields(self) -> None:
        class Open(BaseModel):
            model_config = ConfigDict(extra="allow")
            a: str

        self.assertEqual(Open.model_validate({"a": "1", "b": 2}).model_dump(), {"a": "1", "b": 2})


def build_app() -> FastAPI:
    app = FastAPI(title="t")
    router = APIRouter(prefix="/api")

    @router.post("/items", status_code=202)
    def create(payload: Payload) -> dict[str, Any]:
        return {"received": payload.model_dump()}

    @router.get("/items/{item_id}")
    async def read(item_id: str, request: Request, verbose: bool = False,
                   x_token: str | None = Header(default=None), session: str | None = Cookie(default=None),
                   q: str = Query("d", min_length=1, max_length=3)) -> dict[str, Any]:
        if item_id == "missing":
            raise HTTPException(status_code=404, detail="item_not_found", headers={"Cache-Control": "no-store"})
        return {"id": item_id, "verbose": verbose, "token": x_token, "session": session, "q": q,
                "path": request.url.path}

    @router.post("/upload")
    async def upload(artifact: UploadFile = File(...), note: str = Form(...), keep: bool = Form(False)) -> dict[str, Any]:
        data = await artifact.read()
        return {"name": artifact.filename, "type": artifact.content_type, "size": len(data), "note": note, "keep": keep}

    @router.post("/raw")
    async def raw(request: Request) -> Response:
        return Response(content=await request.body(), media_type="application/octet-stream")

    app.include_router(router)

    sub = FastAPI()

    @sub.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"state": "OK"}

    app.mount("/sub", sub)

    @app.middleware("http")
    async def stamp(request: Request, call_next):
        response = await call_next(request)
        body = b"".join([chunk async for chunk in response.body_iterator])
        headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
        headers["x-stamped"] = "1"
        return Response(content=body, status_code=response.status_code, headers=headers, media_type=response.media_type)

    class Refuse(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path == "/api/refused":
                return Response(status_code=403)
            return await call_next(request)

    app.add_middleware(Refuse)
    app.add_middleware(CORSMiddleware, allow_origins=["https://site.example"], allow_methods=["GET", "POST"],
                       allow_headers=["X-Token"])
    return app


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(build_app())

    def test_body_model_and_status_code(self) -> None:
        ok = self.client.post("/api/items", json={"name": "n"})
        self.assertEqual(ok.status_code, 202)
        self.assertEqual(ok.json()["received"]["name"], "n")
        self.assertEqual(ok.headers["x-stamped"], "1")

    def test_invalid_or_missing_body_is_422_with_located_errors(self) -> None:
        bad = self.client.post("/api/items", json={"name": "n", "extra": 1})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()["detail"][0]["loc"], ["body", "extra"])
        self.assertEqual(self.client.post("/api/items", content=b"{", headers={"content-type": "application/json"}).status_code, 422)
        self.assertEqual(self.client.post("/api/items").status_code, 422)

    def test_path_query_header_cookie_parameters(self) -> None:
        out = self.client.get("/api/items/abc?verbose=true&q=xy", headers={"X-Token": "t"}, cookies={"session": "s"}).json()
        self.assertEqual(out, {"id": "abc", "verbose": True, "token": "t", "session": "s", "q": "xy", "path": "/api/items/abc"})
        self.assertEqual(self.client.get("/api/items/abc?q=toolong").status_code, 422)

    def test_http_exception_carries_detail_and_headers(self) -> None:
        missing = self.client.get("/api/items/missing")
        self.assertEqual((missing.status_code, missing.json()), (404, {"detail": "item_not_found"}))
        self.assertEqual(missing.headers["cache-control"], "no-store")

    def test_not_found_and_method_not_allowed(self) -> None:
        self.assertEqual(self.client.get("/nope").json(), {"detail": "Not Found"})
        wrong = self.client.delete("/api/items/abc")
        self.assertEqual(wrong.status_code, 405)
        self.assertEqual(wrong.headers["allow"], "GET")

    def test_multipart_upload_and_form_fields(self) -> None:
        out = self.client.post("/api/upload", data={"note": "hello", "keep": "true"},
                               files={"artifact": ("a.png", b"\x89PNG\r\n", "image/png")}).json()
        self.assertEqual(out, {"name": "a.png", "type": "image/png", "size": 6, "note": "hello", "keep": True})
        self.assertEqual(self.client.post("/api/upload", data={"note": "x"}).status_code, 422)

    def test_raw_body_mount_and_slash_redirect(self) -> None:
        self.assertEqual(self.client.post("/api/raw", content=b"\x00\x01").content, b"\x00\x01")
        self.assertEqual(self.client.get("/sub/healthz").json(), {"state": "OK"})
        redirected = TestClient(build_app(), follow_redirects=False).get("/sub/healthz/")
        self.assertEqual(redirected.status_code, 307)
        self.assertEqual(self.client.get("/sub/healthz/").json(), {"state": "OK"})

    def test_middleware_order_and_cors(self) -> None:
        self.assertEqual(self.client.get("/api/refused").status_code, 403)
        simple = self.client.get("/api/items/a", headers={"Origin": "https://site.example"})
        self.assertEqual(simple.headers["access-control-allow-origin"], "https://site.example")
        self.assertNotIn("access-control-allow-origin",
                         self.client.get("/api/items/a", headers={"Origin": "https://evil.example"}).headers)
        preflight = self.client.options("/api/items", headers={"Origin": "https://site.example",
                                                                "Access-Control-Request-Method": "POST",
                                                                "Access-Control-Request-Headers": "x-token"})
        self.assertEqual((preflight.status_code, preflight.text), (200, "OK"))
        refused = self.client.options("/api/items", headers={"Origin": "https://site.example",
                                                             "Access-Control-Request-Method": "DELETE"})
        self.assertEqual((refused.status_code, refused.text), (400, "Disallowed CORS method"))

    def test_server_exception_is_raised_to_the_test_client(self) -> None:
        app = FastAPI()

        @app.get("/boom")
        def boom() -> None:
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            TestClient(app).get("/boom")
        self.assertEqual(TestClient(app, raise_server_exceptions=False).get("/boom").status_code, 500)


class ServerTests(unittest.TestCase):
    def test_server_answers_one_real_request_over_a_socket(self) -> None:
        app = FastAPI()

        @app.post("/echo")
        async def echo(request: Request) -> dict[str, Any]:
            return {"body": (await request.body()).decode(), "query": request.url.query}

        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        loop = asyncio.new_event_loop()
        def serve() -> None:
            try:
                loop.run_until_complete(asyncio.wait_for(web_server.serve(app, "127.0.0.1", port), timeout=10))
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        body = None
        for _ in range(50):
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{port}/echo?a=1", data=b"hi", method="POST")
                with urllib.request.urlopen(req, timeout=2) as response:
                    body = json.load(response)
                    self.assertEqual(response.headers["connection"], "close")
                break
            except (ConnectionError, OSError):
                threading.Event().wait(0.05)
        self.assertEqual(body, {"body": "hi", "query": "a=1"})
        loop.call_soon_threadsafe(lambda: [t.cancel() for t in asyncio.all_tasks(loop)])
        thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
