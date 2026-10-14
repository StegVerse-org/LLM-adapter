"""Declarative request models on the standard library.

Replaces the subset of pydantic v2 this repository uses: ``BaseModel`` with
annotated fields, ``Field`` (default, default_factory, min_length, max_length,
pattern), ``ConfigDict(extra=...)``, ``field_validator`` and
``model_validator(mode="after")``, ``model_dump()`` and ``model_validate()``.

Validation follows pydantic's lax mode for the annotations used here: ``str``
accepts only strings, ``bool`` accepts booleans and the usual true/false
spellings, ``int`` accepts integers, integral floats and integer strings;
containers, ``Literal``, ``Any``, unions and nested models are checked
recursively. A failure raises ``ValidationError`` carrying one entry per error.
"""
from __future__ import annotations

import re
import types
import typing
from copy import deepcopy
from typing import Any, Callable

_MISSING = object()


class ValidationError(ValueError):
    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self._errors = errors
        super().__init__("; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in errors))

    def errors(self) -> list[dict[str, Any]]:
        return [dict(e) for e in self._errors]


class _Invalid(Exception):
    def __init__(self, msg: str, kind: str = "value_error") -> None:
        super().__init__(msg)
        self.msg = msg
        self.kind = kind


class FieldInfo:
    def __init__(self, default: Any = _MISSING, *, default_factory: Callable[[], Any] | None = None,
                 min_length: int | None = None, max_length: int | None = None,
                 pattern: str | None = None, alias: str | None = None, **_: Any) -> None:
        self.default = default
        self.default_factory = default_factory
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern is not None else None
        self.alias = alias

    def required(self) -> bool:
        return self.default is _MISSING and self.default_factory is None

    def make_default(self) -> Any:
        if self.default_factory is not None:
            return self.default_factory()
        return deepcopy(self.default)


def Field(default: Any = _MISSING, **kwargs: Any) -> Any:  # noqa: N802 - pydantic-compatible name
    if default is Ellipsis:
        default = _MISSING
    return FieldInfo(default, **kwargs)


def ConfigDict(**kwargs: Any) -> dict[str, Any]:  # noqa: N802 - pydantic-compatible name
    return dict(kwargs)


def field_validator(*fields: str, mode: str = "after") -> Callable[[Any], Any]:
    def decorate(func: Any) -> Any:
        target = func.__func__ if isinstance(func, (classmethod, staticmethod)) else func
        target.__model_field_validator__ = fields
        return func
    return decorate


def model_validator(*, mode: str = "after") -> Callable[[Any], Any]:
    if mode != "after":
        raise ValueError("only mode='after' model validators are supported")

    def decorate(func: Any) -> Any:
        func.__model_validator__ = mode
        return func
    return decorate


def _coerce(value: Any, annotation: Any) -> Any:
    if annotation is Any or annotation is object:
        return value
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is typing.Union or (types.UnionType is not None and origin is types.UnionType):
        if value is None and type(None) in args:
            return None
        failures = []
        for option in args:
            if option is type(None):
                continue
            try:
                return _coerce(value, option)
            except _Invalid as exc:
                failures.append(exc.msg)
        raise _Invalid("; ".join(failures) or "value does not match any allowed type")
    if origin is typing.Literal:
        for option in args:
            if value == option and type(value) is type(option):
                return option
        raise _Invalid("value must be one of " + ", ".join(repr(a) for a in args), "literal_error")
    if origin in (list, typing.List):
        if not isinstance(value, (list, tuple)):
            raise _Invalid("value must be a list", "list_type")
        item = args[0] if args else Any
        return [_coerce(v, item) for v in value]
    if origin in (dict, typing.Dict):
        if not isinstance(value, dict):
            raise _Invalid("value must be an object", "dict_type")
        key_type, value_type = args if args else (Any, Any)
        return {_coerce(k, key_type): _coerce(v, value_type) for k, v in value.items()}
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        if isinstance(value, annotation):
            return value
        if not isinstance(value, dict):
            raise _Invalid("value must be an object", "model_type")
        return annotation.model_validate(value)
    if annotation is str:
        if isinstance(value, str):
            return value
        raise _Invalid("value must be a string", "string_type")
    if annotation is bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        if isinstance(value, str) and value.strip().lower() in ("true", "1", "yes", "on", "t", "y"):
            return True
        if isinstance(value, str) and value.strip().lower() in ("false", "0", "no", "off", "f", "n"):
            return False
        raise _Invalid("value must be a boolean", "bool_type")
    if annotation is int:
        if isinstance(value, bool):
            raise _Invalid("value must be an integer", "int_type")
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str) and re.fullmatch(r"\s*[+-]?\d+\s*", value):
            return int(value)
        raise _Invalid("value must be an integer", "int_type")
    if annotation is float:
        if isinstance(value, bool):
            raise _Invalid("value must be a number", "float_type")
        if isinstance(value, (int, float)):
            return float(value)
        raise _Invalid("value must be a number", "float_type")
    if isinstance(annotation, type):
        if isinstance(value, annotation):
            return value
        raise _Invalid(f"value must be {annotation.__name__}", "is_instance_of")
    return value


def _constrain(value: Any, info: FieldInfo) -> None:
    if value is None:
        return
    if info.min_length is not None and hasattr(value, "__len__") and len(value) < info.min_length:
        raise _Invalid(f"length must be at least {info.min_length}", "too_short")
    if info.max_length is not None and hasattr(value, "__len__") and len(value) > info.max_length:
        raise _Invalid(f"length must be at most {info.max_length}", "too_long")
    if info.pattern is not None and isinstance(value, str) and not info.pattern.search(value):
        raise _Invalid(f"value must match pattern {info.pattern.pattern!r}", "string_pattern_mismatch")


class BaseModel:
    model_config: dict[str, Any] = {}
    __model_fields__: dict[str, tuple[Any, FieldInfo]] = {}
    __model_field_validators__: list[tuple[tuple[str, ...], Callable[..., Any]]] = []
    __model_validators__: list[Callable[..., Any]] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__model_resolved__ = False

    @classmethod
    def _resolve(cls) -> None:
        if cls.__dict__.get("__model_resolved__"):
            return
        # Each class's annotations resolve against its own module's globals.
        hints = typing.get_type_hints(cls)
        fields: dict[str, tuple[Any, FieldInfo]] = {}
        for klass in reversed(cls.__mro__):
            for name in getattr(klass, "__annotations__", {}):
                if name.startswith("_") or name == "model_config" or name not in hints:
                    continue
                if typing.get_origin(hints[name]) is typing.ClassVar:
                    continue
                raw = klass.__dict__.get(name, _MISSING)
                info = raw if isinstance(raw, FieldInfo) else FieldInfo(raw)
                fields[name] = (hints[name], info)
        field_validators = []
        model_validators = []
        for klass in reversed(cls.__mro__):
            for attr in klass.__dict__.values():
                func = attr.__func__ if isinstance(attr, (classmethod, staticmethod)) else attr
                if getattr(func, "__model_field_validator__", None):
                    field_validators.append((func.__model_field_validator__, attr))
                if getattr(func, "__model_validator__", None):
                    model_validators.append(func)
        cls.__model_fields__ = fields
        cls.__model_field_validators__ = field_validators
        cls.__model_validators__ = model_validators
        cls.__model_resolved__ = True

    def __init__(self, **data: Any) -> None:
        cls = type(self)
        cls._resolve()
        errors: list[dict[str, Any]] = []
        extra = (cls.model_config or {}).get("extra", "ignore")
        values: dict[str, Any] = {}
        for name, (annotation, info) in cls.__model_fields__.items():
            key = info.alias or name
            if key in data:
                raw = data[key]
            elif info.required():
                errors.append({"type": "missing", "loc": (name,), "msg": "Field required", "input": data})
                continue
            else:
                values[name] = info.make_default()
                continue
            try:
                value = _coerce(raw, annotation)
                _constrain(value, info)
                for names, validator in cls.__model_field_validators__:
                    if name in names:
                        if isinstance(validator, staticmethod):
                            value = validator.__func__(value)
                        else:
                            func = validator.__func__ if isinstance(validator, classmethod) else validator
                            value = func(cls, value)
                values[name] = value
            except _Invalid as exc:
                errors.append({"type": exc.kind, "loc": (name,), "msg": exc.msg, "input": raw})
            except ValidationError as exc:
                for err in exc.errors():
                    errors.append({**err, "loc": (name, *err["loc"])})
            except (ValueError, AssertionError) as exc:
                errors.append({"type": "value_error", "loc": (name,), "msg": f"Value error, {exc}", "input": raw})
        known = {info.alias or name for name, (_, info) in cls.__model_fields__.items()}
        extras = {k: v for k, v in data.items() if k not in known}
        if extras and extra == "forbid":
            for key, value in extras.items():
                errors.append({"type": "extra_forbidden", "loc": (key,), "msg": "Extra inputs are not permitted", "input": value})
        if errors:
            raise ValidationError(errors)
        object.__setattr__(self, "__model_extra__", dict(extras) if extra == "allow" else {})
        for name, value in values.items():
            object.__setattr__(self, name, value)
        if extra == "allow":
            for key, value in extras.items():
                object.__setattr__(self, key, value)
        for validator in cls.__model_validators__:
            try:
                result = validator(self)
            except (ValueError, AssertionError) as exc:
                raise ValidationError([{"type": "value_error", "loc": (), "msg": f"Value error, {exc}", "input": data}]) from exc
            if result is not None and result is not self:
                raise TypeError("model validators must return self")

    @classmethod
    def model_validate(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise ValidationError([{"type": "model_type", "loc": (), "msg": "Input should be an object", "input": data}])
        return cls(**data)

    def model_dump(self, *, mode: str = "python", include: set[str] | None = None,
                   exclude: set[str] | None = None, exclude_none: bool = False) -> dict[str, Any]:
        type(self)._resolve()
        out = {name: _dump(getattr(self, name)) for name in type(self).__model_fields__}
        out.update({k: _dump(v) for k, v in getattr(self, "__model_extra__", {}).items()})
        if include is not None:
            out = {k: v for k, v in out.items() if k in include}
        if exclude:
            out = {k: v for k, v in out.items() if k not in exclude}
        if exclude_none:
            out = {k: v for k, v in out.items() if v is not None}
        return out

    @property
    def model_extra(self) -> dict[str, Any]:
        return dict(getattr(self, "__model_extra__", {}))

    def __eq__(self, other: Any) -> bool:
        return type(other) is type(self) and other.model_dump() == self.model_dump()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join(f'{k}={v!r}' for k, v in self.model_dump().items())})"


def _dump(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, list):
        return [_dump(v) for v in value]
    if isinstance(value, dict):
        return {k: _dump(v) for k, v in value.items()}
    return value


__all__ = ["BaseModel", "ConfigDict", "Field", "FieldInfo", "ValidationError", "field_validator", "model_validator"]
