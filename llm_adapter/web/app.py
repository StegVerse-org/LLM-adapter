"""ASGI application, routing and request/response types on the standard library.

Replaces the subset of FastAPI/Starlette this repository uses, under the same
names: ``FastAPI``, ``APIRouter``, ``Request``, ``Response``, ``JSONResponse``,
``PlainTextResponse``, ``HTTPException``, the ``Header``/``Query``/``Cookie``/
``Form``/``File`` parameter markers with ``UploadFile``, ``app.middleware("http")``,
``add_middleware``, ``include_router``, ``mount``, ``CORSMiddleware`` and
``BaseHTTPMiddleware``.

Endpoint parameters are resolved from the signature the way FastAPI resolves
them: path parameters by name, ``Request`` by annotation, markers by kind, a
model or ``dict`` annotation from the JSON body, and any other plain parameter
from the query string. A parameter that is missing or invalid answers 422 with
``{"detail": [{"type", "loc", "msg", "input"}]}``. Sync endpoints run in a worker
thread; async endpoints are awaited. Standard library only.
"""
from __future__ import annotations

import asyncio
import dataclasses
import datetime
import enum
import functools
import http.cookies
import inspect
import io
import json
import re
import types
import typing
from collections.abc import Mapping
from email.parser import BytesParser
from email.policy import HTTP as _HTTP_POLICY
from pathlib import PurePath
from typing import Any, Awaitable, Callable, Iterable
from urllib.parse import parse_qsl

from .model import BaseModel, ValidationError, _coerce, _constrain, _Invalid, FieldInfo

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_MISSING = object()


# --------------------------------------------------------------------------- headers / url


class Headers(Mapping):
    """Case-insensitive, multi-valued header view (keys lower-cased)."""

    def __init__(self, raw: Iterable[tuple[bytes, bytes]] | Mapping[str, str] | None = None) -> None:
        items: list[tuple[str, str]] = []
        if isinstance(raw, Mapping):
            items = [(str(k).lower(), str(v)) for k, v in raw.items()]
        elif raw is not None:
            for key, value in raw:
                k = key.decode("latin-1") if isinstance(key, bytes) else str(key)
                v = value.decode("latin-1") if isinstance(value, bytes) else str(value)
                items.append((k.lower(), v))
        self._items = items

    def __getitem__(self, key: str) -> str:
        key = key.lower()
        for k, v in self._items:
            if k == key:
                return v
        raise KeyError(key)

    def __iter__(self):
        seen = []
        for k, _ in self._items:
            if k not in seen:
                seen.append(k)
        return iter(seen)

    def __len__(self) -> int:
        return len(set(k for k, _ in self._items))

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and any(k == key.lower() for k, _ in self._items)

    def getlist(self, key: str) -> list[str]:
        key = key.lower()
        return [v for k, v in self._items if k == key]

    def items(self):  # type: ignore[override]
        return list(self._items)

    def raw(self) -> list[tuple[bytes, bytes]]:
        return [(k.encode("latin-1"), v.encode("latin-1")) for k, v in self._items]

    def __repr__(self) -> str:
        return f"Headers({self._items!r})"


class MutableHeaders(Headers):
    def __setitem__(self, key: str, value: str) -> None:
        key = key.lower()
        self._items = [(k, v) for k, v in self._items if k != key]
        self._items.append((key, str(value)))

    def __delitem__(self, key: str) -> None:
        key = key.lower()
        self._items = [(k, v) for k, v in self._items if k != key]

    def setdefault(self, key: str, value: str) -> str:  # type: ignore[override]
        if key not in self:
            self[key] = value
        return self[key]

    def append(self, key: str, value: str) -> None:
        self._items.append((key.lower(), str(value)))

    def update(self, other: Mapping[str, str]) -> None:
        for k, v in other.items():
            self[k] = v

    def add_vary_header(self, vary: str) -> None:
        existing = self.get("vary")
        self["vary"] = f"{existing}, {vary}" if existing else vary


class QueryParams(Mapping):
    def __init__(self, query: str) -> None:
        self._items = parse_qsl(query, keep_blank_values=True)

    def __getitem__(self, key: str) -> str:
        for k, v in reversed(self._items):
            if k == key:
                return v
        raise KeyError(key)

    def __iter__(self):
        return iter(dict(self._items))

    def __len__(self) -> int:
        return len(dict(self._items))

    def getlist(self, key: str) -> list[str]:
        return [v for k, v in self._items if k == key]


class URL:
    def __init__(self, scope: Scope) -> None:
        self.scheme = str(scope.get("scheme") or "http")
        self.path = str(scope.get("root_path", "") or "") + str(scope.get("path") or "/")
        self.query = (scope.get("query_string") or b"").decode("latin-1")
        host = None
        for key, value in scope.get("headers") or []:
            if key.lower() == b"host":
                host = value.decode("latin-1")
                break
        if host is None:
            server = scope.get("server")
            host = f"{server[0]}:{server[1]}" if server else "localhost"
        self.netloc = host
        self.hostname = host.rsplit(":", 1)[0] if ":" in host and not host.endswith("]") else host
        self.port = int(host.rsplit(":", 1)[1]) if ":" in host and host.rsplit(":", 1)[1].isdigit() else None

    def __str__(self) -> str:
        return f"{self.scheme}://{self.netloc}{self.path}" + (f"?{self.query}" if self.query else "")

    def __repr__(self) -> str:
        return f"URL({str(self)!r})"


@dataclasses.dataclass(frozen=True)
class Address:
    host: str
    port: int


# --------------------------------------------------------------------------- request


class UploadFile:
    def __init__(self, file: io.BytesIO, *, filename: str | None = None, headers: Headers | None = None) -> None:
        self.file = file
        self.filename = filename
        self.headers = headers or Headers()
        self.content_type = self.headers.get("content-type")
        self.size = len(file.getbuffer())

    async def read(self, size: int = -1) -> bytes:
        return self.file.read(size)

    async def seek(self, offset: int) -> None:
        self.file.seek(offset)

    async def write(self, data: bytes) -> None:
        self.file.write(data)

    async def close(self) -> None:
        self.file.close()


class FormData(Mapping):
    def __init__(self, items: list[tuple[str, Any]]) -> None:
        self._items = items

    def __getitem__(self, key: str) -> Any:
        for k, v in reversed(self._items):
            if k == key:
                return v
        raise KeyError(key)

    def __iter__(self):
        return iter(dict(self._items))

    def __len__(self) -> int:
        return len(dict(self._items))

    def getlist(self, key: str) -> list[Any]:
        return [v for k, v in self._items if k == key]


def _parse_form(content_type: str, body: bytes) -> FormData:
    media = content_type.split(";", 1)[0].strip().lower()
    if media == "application/x-www-form-urlencoded":
        return FormData(parse_qsl(body.decode("utf-8"), keep_blank_values=True))
    if media != "multipart/form-data":
        return FormData([])
    message = BytesParser(policy=_HTTP_POLICY).parsebytes(
        b"Content-Type: " + content_type.encode("latin-1") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body)
    items: list[tuple[str, Any]] = []
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if name is None:
            continue
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if filename is not None:
            headers = Headers([(k.lower().encode(), str(v).encode("latin-1", "replace")) for k, v in part.items()])
            items.append((name, UploadFile(io.BytesIO(payload), filename=filename, headers=headers)))
        else:
            charset = part.get_content_charset() or "utf-8"
            items.append((name, payload.decode(charset, errors="replace")))
    return FormData(items)


class Request:
    def __init__(self, scope: Scope, receive: Receive | None = None) -> None:
        self.scope = scope
        self._receive = receive
        self._body: bytes | None = None
        self._form: FormData | None = None
        self.headers = Headers(scope.get("headers") or [])
        self.method = str(scope.get("method") or "GET").upper()
        self.url = URL(scope)
        self.query_params = QueryParams(self.url.query)
        self.path_params: dict[str, Any] = scope.get("path_params") or {}
        client = scope.get("client")
        self.client = Address(str(client[0]), int(client[1])) if client else None
        state = scope.setdefault("state", {})
        self.state = types.SimpleNamespace(**state) if isinstance(state, dict) else state

    @property
    def cookies(self) -> dict[str, str]:
        jar = http.cookies.SimpleCookie()
        for header in self.headers.getlist("cookie"):
            try:
                jar.load(header)
            except http.cookies.CookieError:
                continue
        return {k: m.value for k, m in jar.items()}

    @property
    def app(self) -> Any:
        return self.scope.get("app")

    @property
    def base_url(self) -> str:
        """Scheme, host and mount root of this request, ending in ``/``."""
        return f"{self.url.scheme}://{self.url.netloc}{self.scope.get('root_path', '') or ''}/"

    async def body(self) -> bytes:
        if self._body is None:
            if self._receive is None:
                self._body = b""
            else:
                chunks = []
                while True:
                    message = await self._receive()
                    if message.get("type") == "http.disconnect":
                        break
                    chunks.append(message.get("body", b""))
                    if not message.get("more_body"):
                        break
                self._body = b"".join(chunks)
        return self._body

    async def json(self) -> Any:
        return json.loads(await self.body())

    async def form(self) -> FormData:
        if self._form is None:
            self._form = _parse_form(self.headers.get("content-type", ""), await self.body())
        return self._form


# --------------------------------------------------------------------------- responses


def jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return jsonable(value.model_dump())
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return jsonable(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(jsonable(k)): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [jsonable(v) for v in value]
    if isinstance(value, enum.Enum):
        return jsonable(value.value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, PurePath):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return jsonable(value.model_dump())
    return value


class Response:
    media_type: str | None = None
    charset = "utf-8"

    def __init__(self, content: Any = None, status_code: int = 200, headers: Mapping[str, str] | None = None,
                 media_type: str | None = None, background: Any = None) -> None:
        self.status_code = status_code
        if media_type is not None:
            self.media_type = media_type
        self.background = background
        self.body = self.render(content)
        self.headers = MutableHeaders(headers or {})
        self._init_headers()

    def render(self, content: Any) -> bytes:
        if content is None:
            return b""
        if isinstance(content, (bytes, bytearray, memoryview)):
            return bytes(content)
        return str(content).encode(self.charset)

    def _init_headers(self) -> None:
        populate_length = self.body is not None and not (self.status_code < 200 or self.status_code in (204, 304))
        if populate_length and "content-length" not in self.headers:
            self.headers["content-length"] = str(len(self.body))
        if self.media_type is not None and "content-type" not in self.headers:
            content_type = self.media_type
            if content_type.startswith("text/") and "charset=" not in content_type.lower():
                content_type += f"; charset={self.charset}"
            self.headers["content-type"] = content_type

    @property
    def body_iterator(self):
        async def iterate():
            yield self.body
        return iterate()

    def set_cookie(self, key: str, value: str = "", max_age: int | None = None, path: str = "/",
                   secure: bool = False, httponly: bool = False, samesite: str | None = "lax") -> None:
        cookie = http.cookies.SimpleCookie()
        cookie[key] = value
        morsel = cookie[key]
        if max_age is not None:
            morsel["max-age"] = max_age
        morsel["path"] = path
        if secure:
            morsel["secure"] = True
        if httponly:
            morsel["httponly"] = True
        if samesite:
            morsel["samesite"] = samesite
        self.headers.append("set-cookie", morsel.OutputString())

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await send({"type": "http.response.start", "status": self.status_code, "headers": self.headers.raw()})
        await send({"type": "http.response.body", "body": b"" if scope.get("method") == "HEAD" else self.body})
        if self.background is not None:
            result = self.background()
            if inspect.isawaitable(result):
                await result


class JSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(content, ensure_ascii=False, allow_nan=False, indent=None,
                          separators=(",", ":")).encode("utf-8")


class PlainTextResponse(Response):
    media_type = "text/plain"


class HTMLResponse(Response):
    media_type = "text/html"


class RedirectResponse(Response):
    def __init__(self, url: str, status_code: int = 307, headers: Mapping[str, str] | None = None) -> None:
        super().__init__(content=b"", status_code=status_code, headers=headers)
        self.headers["location"] = url


class _CapturedResponse(Response):
    """The response a middleware's ``call_next`` hands back (already rendered)."""

    def __init__(self, status_code: int, headers: list[tuple[bytes, bytes]], body: bytes) -> None:
        self.status_code = status_code
        self.background = None
        self.body = body
        self.headers = MutableHeaders(headers)
        self.media_type = (self.headers.get("content-type") or "").split(";")[0] or None


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any = None, headers: Mapping[str, str] | None = None) -> None:
        if detail is None:
            from http import HTTPStatus
            try:
                detail = HTTPStatus(status_code).phrase
            except ValueError:
                detail = ""
        super().__init__(status_code, detail)
        self.status_code = status_code
        self.detail = detail
        self.headers = dict(headers) if headers else None


class RequestValidationError(Exception):
    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__(errors)
        self._errors = errors

    def errors(self) -> list[dict[str, Any]]:
        return self._errors


# --------------------------------------------------------------------------- parameters


class _Param:
    kind = "query"

    def __init__(self, default: Any = _MISSING, *, alias: str | None = None, min_length: int | None = None,
                 max_length: int | None = None, pattern: str | None = None, convert_underscores: bool = True,
                 **_: Any) -> None:
        self.default = _MISSING if default is Ellipsis else default
        self.alias = alias
        self.info = FieldInfo(min_length=min_length, max_length=max_length, pattern=pattern)
        self.convert_underscores = convert_underscores


class _Header(_Param):
    kind = "header"


class _Query(_Param):
    kind = "query"


class _Cookie(_Param):
    kind = "cookie"


class _Form(_Param):
    kind = "form"


class _File(_Form):
    kind = "file"


class _Body(_Param):
    kind = "body"


def Header(default: Any = _MISSING, **kwargs: Any) -> Any:  # noqa: N802
    return _Header(default, **kwargs)


def Query(default: Any = _MISSING, **kwargs: Any) -> Any:  # noqa: N802
    return _Query(default, **kwargs)


def Cookie(default: Any = _MISSING, **kwargs: Any) -> Any:  # noqa: N802
    return _Cookie(default, **kwargs)


def Form(default: Any = _MISSING, **kwargs: Any) -> Any:  # noqa: N802
    return _Form(default, **kwargs)


def File(default: Any = _MISSING, **kwargs: Any) -> Any:  # noqa: N802
    return _File(default, **kwargs)


def Body(default: Any = _MISSING, **kwargs: Any) -> Any:  # noqa: N802
    return _Body(default, **kwargs)


def _is_model(annotation: Any) -> bool:
    return isinstance(annotation, type) and issubclass(annotation, BaseModel)


def _unwrap_optional(annotation: Any) -> Any:
    origin = typing.get_origin(annotation)
    if origin is typing.Union or origin is types.UnionType:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _is_body_type(annotation: Any) -> bool:
    base = _unwrap_optional(annotation)
    return _is_model(base) or base is dict or typing.get_origin(base) in (dict, list) or base is list


@dataclasses.dataclass
class _Spec:
    name: str
    kind: str
    annotation: Any
    default: Any
    alias: str | None = None
    info: FieldInfo | None = None


def _signature_specs(endpoint: Callable[..., Any], path_names: set[str]) -> list[_Spec]:
    try:
        hints = typing.get_type_hints(endpoint)
    except Exception:
        hints = {}
    specs = []
    for name, param in inspect.signature(endpoint).parameters.items():
        annotation = hints.get(name, Any if param.annotation is inspect.Parameter.empty else param.annotation)
        default = param.default
        if annotation is Request or (isinstance(annotation, type) and issubclass(annotation, Request)):
            specs.append(_Spec(name, "request", annotation, _MISSING))
        elif isinstance(default, _Param):
            specs.append(_Spec(name, default.kind, annotation, default.default, default.alias, default.info))
        elif name in path_names:
            specs.append(_Spec(name, "path", annotation, _MISSING))
        elif _is_body_type(annotation):
            specs.append(_Spec(name, "body", annotation,
                               _MISSING if default is inspect.Parameter.empty else default))
        else:
            specs.append(_Spec(name, "query", annotation,
                               _MISSING if default is inspect.Parameter.empty else default))
    return specs


def _validate_value(spec: _Spec, raw: Any) -> Any:
    annotation = spec.annotation
    if annotation is UploadFile or _unwrap_optional(annotation) is UploadFile:
        if not isinstance(raw, UploadFile):
            raise _Invalid("Expected UploadFile", "value_error")
        return raw
    if _is_model(_unwrap_optional(annotation)) and isinstance(raw, dict):
        return _unwrap_optional(annotation).model_validate(raw)
    value = _coerce(raw, annotation)
    if spec.info is not None:
        _constrain(value, spec.info)
    return value


async def _resolve_arguments(request: Request, specs: list[_Spec]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    form: FormData | None = None
    body_specs = [s for s in specs if s.kind == "body"]
    json_body: Any = _MISSING
    if body_specs:
        raw = await request.body()
        if raw:
            try:
                json_body = json.loads(raw)
            except (ValueError, UnicodeDecodeError) as exc:
                raise RequestValidationError([{"type": "json_invalid", "loc": ("body", 0),
                                               "msg": "JSON decode error", "input": {}, "ctx": {"error": str(exc)}}])
    for spec in specs:
        if spec.kind == "request":
            kwargs[spec.name] = request
            continue
        if spec.kind == "path":
            raw_value: Any = request.path_params.get(spec.name, _MISSING)
            loc = ("path", spec.name)
        elif spec.kind == "header":
            key = spec.alias or spec.name.replace("_", "-")
            raw_value = request.headers.get(key, _MISSING)
            loc = ("header", key.lower())
        elif spec.kind == "cookie":
            key = spec.alias or spec.name
            raw_value = request.cookies.get(key, _MISSING)
            loc = ("cookie", key)
        elif spec.kind == "query":
            key = spec.alias or spec.name
            raw_value = request.query_params.get(key, _MISSING)
            loc = ("query", key)
        elif spec.kind in ("form", "file"):
            if form is None:
                form = await request.form()
            key = spec.alias or spec.name
            raw_value = form.get(key, _MISSING)
            if spec.kind == "form" and isinstance(raw_value, UploadFile):
                raw_value = _MISSING
            loc = ("body", key)
        else:  # body
            if len(body_specs) == 1 and not spec.alias:
                raw_value = json_body
            else:
                raw_value = json_body.get(spec.alias or spec.name, _MISSING) if isinstance(json_body, dict) else _MISSING
            loc = ("body",) if len(body_specs) == 1 else ("body", spec.alias or spec.name)
        if raw_value is _MISSING or (raw_value == "" and spec.kind in ("form",) and spec.default is not _MISSING):
            if spec.default is _MISSING:
                errors.append({"type": "missing", "loc": loc, "msg": "Field required", "input": None})
            else:
                kwargs[spec.name] = spec.default
            continue
        try:
            kwargs[spec.name] = _validate_value(spec, raw_value)
        except _Invalid as exc:
            errors.append({"type": exc.kind, "loc": loc, "msg": exc.msg, "input": raw_value})
        except ValidationError as exc:
            for err in exc.errors():
                errors.append({**err, "loc": (*loc, *err["loc"])})
    if errors:
        raise RequestValidationError(errors)
    return kwargs


# --------------------------------------------------------------------------- routing


_PARAM = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)(?::(path|str|int))?\}")


def _compile_path(path: str) -> tuple[re.Pattern[str], set[str], dict[str, str]]:
    pattern = "^"
    index = 0
    names: set[str] = set()
    convertors: dict[str, str] = {}
    for match in _PARAM.finditer(path):
        pattern += re.escape(path[index:match.start()])
        name, conv = match.group(1), match.group(2) or "str"
        names.add(name)
        convertors[name] = conv
        pattern += {"path": f"(?P<{name}>.*)", "int": f"(?P<{name}>[0-9]+)"}.get(conv, f"(?P<{name}>[^/]+)")
        index = match.end()
    pattern += re.escape(path[index:]) + "$"
    return re.compile(pattern), names, convertors


class APIRoute:
    def __init__(self, path: str, endpoint: Callable[..., Any], *, methods: Iterable[str],
                 status_code: int | None = None, name: str | None = None,
                 response_class: type[Response] = JSONResponse, **_: Any) -> None:
        self.path = path
        self.endpoint = endpoint
        self.methods = {m.upper() for m in methods}
        self.status_code = status_code
        self.name = name or getattr(endpoint, "__name__", "endpoint")
        self.response_class = response_class
        self.regex, self.param_names, self.convertors = _compile_path(path)
        self._specs: list[_Spec] | None = None

    def match(self, path: str) -> dict[str, Any] | None:
        found = self.regex.match(path)
        if not found:
            return None
        params: dict[str, Any] = {}
        for key, value in found.groupdict().items():
            params[key] = int(value) if self.convertors.get(key) == "int" else value
        return params

    async def handle(self, request: Request) -> Response:
        if self._specs is None:
            self._specs = _signature_specs(self.endpoint, self.param_names)
        kwargs = await _resolve_arguments(request, self._specs)
        if inspect.iscoroutinefunction(self.endpoint):
            result = await self.endpoint(**kwargs)
        else:
            result = await asyncio.to_thread(functools.partial(self.endpoint, **kwargs))
        if isinstance(result, Response):
            return result
        return self.response_class(content=jsonable(result), status_code=self.status_code or 200)


class Mount:
    def __init__(self, path: str, app: ASGIApp, name: str | None = None) -> None:
        self.path = path.rstrip("/")
        self.app = app
        self.name = name

    def matches(self, path: str) -> bool:
        return path.startswith(self.path + "/")


class APIRouter:
    def __init__(self, *, prefix: str = "", tags: Any = None, routes: list[Any] | None = None, **_: Any) -> None:
        self.prefix = prefix.rstrip("/")
        self.tags = tags
        self.routes: list[Any] = list(routes or [])

    def add_api_route(self, path: str, endpoint: Callable[..., Any], *, methods: Iterable[str] = ("GET",),
                      **kwargs: Any) -> None:
        self.routes.append(APIRoute(self.prefix + path, endpoint, methods=methods, **kwargs))

    def api_route(self, path: str, *, methods: Iterable[str] = ("GET",), **kwargs: Any) -> Callable[[Any], Any]:
        def decorate(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(path, func, methods=methods, **kwargs)
            return func
        return decorate

    def get(self, path: str, **kwargs: Any):
        return self.api_route(path, methods=("GET",), **kwargs)

    def post(self, path: str, **kwargs: Any):
        return self.api_route(path, methods=("POST",), **kwargs)

    def put(self, path: str, **kwargs: Any):
        return self.api_route(path, methods=("PUT",), **kwargs)

    def delete(self, path: str, **kwargs: Any):
        return self.api_route(path, methods=("DELETE",), **kwargs)

    def patch(self, path: str, **kwargs: Any):
        return self.api_route(path, methods=("PATCH",), **kwargs)

    def options(self, path: str, **kwargs: Any):
        return self.api_route(path, methods=("OPTIONS",), **kwargs)

    def include_router(self, router: "APIRouter", *, prefix: str = "", **_: Any) -> None:
        prefix = prefix.rstrip("/")
        for route in router.routes:
            if isinstance(route, APIRoute):
                self.routes.append(APIRoute(prefix + route.path, route.endpoint, methods=route.methods,
                                            status_code=route.status_code, name=route.name,
                                            response_class=route.response_class))
            else:
                self.routes.append(route)


def _error_response(exc: Exception) -> Response:
    if isinstance(exc, HTTPException):
        if exc.status_code in (204, 304) or exc.status_code < 200:
            return Response(status_code=exc.status_code, headers=exc.headers)
        return JSONResponse({"detail": jsonable(exc.detail)}, status_code=exc.status_code, headers=exc.headers)
    if isinstance(exc, RequestValidationError):
        return JSONResponse({"detail": jsonable(exc.errors())}, status_code=422)
    raise exc


class FastAPI(APIRouter):
    """ASGI application: routes, mounts and a middleware stack."""

    def __init__(self, *, title: str = "", version: str = "", redirect_slashes: bool = True, **kwargs: Any) -> None:
        super().__init__(**{k: v for k, v in kwargs.items() if k in ("routes",)})
        self.title = title
        self.version = version
        self.redirect_slashes = redirect_slashes
        self.state = types.SimpleNamespace()
        self.user_middleware: list[tuple[type, dict[str, Any]]] = []
        self._stack: ASGIApp | None = None

    @property
    def router(self) -> "FastAPI":
        return self

    def mount(self, path: str, app: ASGIApp, name: str | None = None) -> None:
        self.routes.append(Mount(path, app, name))
        self._stack = None

    def add_middleware(self, middleware_class: type, **options: Any) -> None:
        self.user_middleware.insert(0, (middleware_class, options))
        self._stack = None

    def middleware(self, middleware_type: str) -> Callable[[Any], Any]:
        if middleware_type != "http":
            raise ValueError("only http middleware is supported")

        def decorate(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_middleware(BaseHTTPMiddleware, dispatch=func)
            return func
        return decorate

    def _build(self) -> ASGIApp:
        app: ASGIApp = self._route
        for cls, options in reversed(self.user_middleware):
            app = cls(app, **options)
        return app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        scope.setdefault("app", self)
        if self._stack is None:
            self._stack = self._build()
        await self._stack(scope, receive, send)

    def _find(self, path: str, method: str) -> tuple[Any, dict[str, Any], bool]:
        allowed = False
        for route in self.routes:
            if isinstance(route, Mount):
                if route.matches(path):
                    return route, {}, True
                continue
            params = route.match(path)
            if params is None:
                continue
            if method in route.methods:
                return route, params, True
            allowed = True
        return None, {}, allowed

    def _allowed_methods(self, path: str) -> list[str]:
        methods: set[str] = set()
        for route in self.routes:
            if isinstance(route, APIRoute) and route.match(path) is not None:
                methods |= route.methods
        return sorted(methods)

    async def _route(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return
        path = scope.get("path") or "/"
        method = str(scope.get("method") or "GET").upper()
        route, params, path_matched = self._find(path, method)
        if isinstance(route, Mount):
            child = dict(scope)
            child["root_path"] = str(scope.get("root_path", "") or "") + route.path
            child["path"] = path[len(route.path):] or "/"
            child.pop("app", None)
            await route.app(child, receive, send)
            return
        if route is None:
            if path_matched:
                response: Response = JSONResponse({"detail": "Method Not Allowed"}, status_code=405,
                                                  headers={"allow": ", ".join(self._allowed_methods(path))})
            else:
                response = self._redirect_slash(scope, path, method) or JSONResponse({"detail": "Not Found"}, status_code=404)
            await response(scope, receive, send)
            return
        scope["path_params"] = params
        request = Request(scope, receive)
        try:
            response = await route.handle(request)
        except (HTTPException, RequestValidationError) as exc:
            response = _error_response(exc)
        await response(scope, receive, send)

    def _redirect_slash(self, scope: Scope, path: str, method: str) -> Response | None:
        if not self.redirect_slashes or path == "/":
            return None
        other = path[:-1] if path.endswith("/") else path + "/"
        found, _, matched = self._find(other, method)
        if found is None and not matched:
            return None
        url = URL({**scope, "path": other, "root_path": scope.get("root_path", "")})
        return RedirectResponse(str(url), status_code=307)


# --------------------------------------------------------------------------- middleware


class BaseHTTPMiddleware:
    def __init__(self, app: ASGIApp, dispatch: Callable[..., Awaitable[Response]] | None = None) -> None:
        self.app = app
        self.dispatch_func = dispatch if dispatch is not None else self.dispatch

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        raise NotImplementedError

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive)

        async def call_next(forwarded: Request) -> Response:
            inner_receive = forwarded._receive or receive
            if forwarded._body is not None:
                cached = forwarded._body

                async def inner_receive() -> dict[str, Any]:  # type: ignore[no-redef]
                    return {"type": "http.request", "body": cached, "more_body": False}
            status = 500
            headers: list[tuple[bytes, bytes]] = []
            chunks: list[bytes] = []

            async def capture(message: dict[str, Any]) -> None:
                nonlocal status, headers
                if message["type"] == "http.response.start":
                    status = int(message["status"])
                    headers = list(message.get("headers") or [])
                elif message["type"] == "http.response.body":
                    chunks.append(message.get("body", b""))

            await self.app(forwarded.scope, inner_receive, capture)
            return _CapturedResponse(status, headers, b"".join(chunks))

        response = await self.dispatch_func(request, call_next)
        await response(scope, receive, send)


SAFELISTED_HEADERS = {"Accept", "Accept-Language", "Content-Language", "Content-Type"}
ALL_METHODS = ("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT")


class CORSMiddleware:
    def __init__(self, app: ASGIApp, allow_origins: Iterable[str] = (), allow_methods: Iterable[str] = ("GET",),
                 allow_headers: Iterable[str] = (), allow_credentials: bool = False,
                 allow_origin_regex: str | None = None, expose_headers: Iterable[str] = (),
                 max_age: int = 600) -> None:
        allow_origins = list(allow_origins)
        allow_methods = list(allow_methods)
        allow_headers = list(allow_headers)
        if "*" in allow_methods:
            allow_methods = list(ALL_METHODS)
        self.app = app
        self.allow_all_origins = "*" in allow_origins
        self.allow_all_headers = "*" in allow_headers
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods
        self.allow_headers = [h.lower() for h in sorted(SAFELISTED_HEADERS | set(allow_headers))]
        self.allow_origin_regex = re.compile(allow_origin_regex) if allow_origin_regex else None
        self.allow_credentials = allow_credentials
        self.simple_headers: dict[str, str] = {}
        if self.allow_all_origins:
            self.simple_headers["access-control-allow-origin"] = "*"
        if allow_credentials:
            self.simple_headers["access-control-allow-credentials"] = "true"
        expose = list(expose_headers)
        if expose:
            self.simple_headers["access-control-expose-headers"] = ", ".join(expose)
        self.preflight_explicit_allow_origin = not self.allow_all_origins or allow_credentials
        self.preflight_headers: dict[str, str] = {}
        if self.preflight_explicit_allow_origin:
            self.preflight_headers["vary"] = "Origin"
        else:
            self.preflight_headers["access-control-allow-origin"] = "*"
        self.preflight_headers["access-control-allow-methods"] = ", ".join(allow_methods)
        self.preflight_headers["access-control-max-age"] = str(max_age)
        allowed = sorted(SAFELISTED_HEADERS | set(allow_headers))
        if allowed and not self.allow_all_headers:
            self.preflight_headers["access-control-allow-headers"] = ", ".join(allowed)
        if allow_credentials:
            self.preflight_headers["access-control-allow-credentials"] = "true"

    def is_allowed_origin(self, origin: str) -> bool:
        if self.allow_all_origins:
            return True
        if self.allow_origin_regex is not None and self.allow_origin_regex.fullmatch(origin):
            return True
        return origin in self.allow_origins

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = Headers(scope.get("headers") or [])
        origin = headers.get("origin")
        if origin is None:
            await self.app(scope, receive, send)
            return
        if scope.get("method") == "OPTIONS" and "access-control-request-method" in headers:
            await self._preflight(headers, origin)(scope, receive, send)
            return
        await self._simple(scope, receive, send, headers, origin)

    def _preflight(self, request_headers: Headers, origin: str) -> Response:
        requested_method = request_headers["access-control-request-method"]
        requested_headers = request_headers.get("access-control-request-headers")
        headers = dict(self.preflight_headers)
        failures = []
        if self.is_allowed_origin(origin):
            if self.preflight_explicit_allow_origin:
                headers["access-control-allow-origin"] = origin
        else:
            failures.append("origin")
        if requested_method not in self.allow_methods:
            failures.append("method")
        if self.allow_all_headers and requested_headers is not None:
            headers["access-control-allow-headers"] = requested_headers
        elif requested_headers is not None:
            for header in [h.lower() for h in requested_headers.split(",")]:
                if header.strip() not in self.allow_headers:
                    failures.append("headers")
                    break
        if failures:
            return PlainTextResponse("Disallowed CORS " + ", ".join(failures), status_code=400, headers=headers)
        return PlainTextResponse("OK", status_code=200, headers=headers)

    async def _simple(self, scope: Scope, receive: Receive, send: Send, request_headers: Headers, origin: str) -> None:
        async def send_with_cors(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(message.get("headers") or [])
                headers.update(self.simple_headers)
                has_cookie = "cookie" in request_headers
                if (self.allow_all_origins and has_cookie) or (not self.allow_all_origins and self.is_allowed_origin(origin)):
                    headers["access-control-allow-origin"] = origin
                    headers.add_vary_header("Origin")
                message = {**message, "headers": headers.raw()}
            await send(message)

        await self.app(scope, receive, send_with_cors)


__all__ = [
    "APIRoute", "APIRouter", "Address", "BaseHTTPMiddleware", "Body", "CORSMiddleware", "Cookie", "FastAPI",
    "File", "Form", "FormData", "HTMLResponse", "HTTPException", "Header", "Headers", "JSONResponse", "Mount",
    "MutableHeaders", "PlainTextResponse", "Query", "RedirectResponse", "Request", "RequestValidationError",
    "Response", "URL", "UploadFile", "jsonable",
]
