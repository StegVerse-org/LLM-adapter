"""Standard-library JSON Schema (draft 2020-12) validation.

The same validator StegVerse-Labs/StegHealth uses (tools/stdlib_json_schema.py,
StegHealth#115), carried here so LLM-adapter's schema tests need no third-party
``jsonschema`` package. It covers the keyword subset the schemas in
``schemas/`` use, with the call shape the tests rely on:
``Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(x)``
yielding errors that carry ``message``, ``path`` and ``absolute_path``.

A schema that uses a validation keyword outside the supported set is refused
when the validator is built, so an unsupported constraint can never pass
silently. Annotation keywords (title, description, $id, ...) are ignored.
"""
from __future__ import annotations

import json
import math
import re
from collections import deque
from datetime import date, datetime
from typing import Any, Iterator

ANNOTATION_KEYWORDS = frozenset({
    "$schema", "$id", "$comment", "$anchor", "title", "description", "default",
    "examples", "deprecated", "readOnly", "writeOnly", "$defs", "definitions",
    "else",  # evaluated together with "if"
    "then",
})
VALIDATION_KEYWORDS = frozenset({
    "type", "const", "enum", "minLength", "maxLength", "pattern", "format",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "properties", "patternProperties", "additionalProperties", "required",
    "minProperties", "maxProperties", "propertyNames", "dependentRequired",
    "items", "prefixItems", "minItems", "maxItems", "uniqueItems", "contains",
    "minContains", "maxContains", "allOf", "anyOf", "oneOf", "not", "if", "$ref",
})

_RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$"
)


class SchemaError(ValueError):
    """The schema uses a construct this validator does not implement."""


class ValidationError(ValueError):
    def __init__(self, message: str, path: tuple[Any, ...]) -> None:
        super().__init__(message)
        self.message = message
        self.path = deque(path)
        self.absolute_path = deque(path)


class FormatChecker:
    """Checks the ``date`` and ``date-time`` formats; other formats are annotations."""

    def conforms(self, value: Any, fmt: str) -> bool:
        if not isinstance(value, str):
            return True
        if fmt == "date":
            try:
                date.fromisoformat(value)
            except ValueError:
                return False
            return len(value) == 10
        if fmt == "date-time":
            if not _RFC3339.match(value):
                return False
            try:
                datetime.fromisoformat(value.replace("z", "Z").replace("Z", "+00:00").replace("t", "T"))
            except ValueError:
                return False
            return True
        return True


def _canonical(value: Any) -> str:
    """JSON equality: 1 == 1.0, but True is not 1."""
    def tag(v: Any) -> Any:
        if isinstance(v, bool):
            return ["b", v]
        if isinstance(v, (int, float)):
            return ["n", float(v)]
        if isinstance(v, list):
            return ["a", [tag(x) for x in v]]
        if isinstance(v, dict):
            return ["o", {k: tag(x) for k, x in v.items()}]
        return ["s", v]
    return json.dumps(tag(value), sort_keys=True, separators=(",", ":"))


def _is_type(value: Any, name: str) -> bool:
    if name == "null":
        return value is None
    if name == "boolean":
        return isinstance(value, bool)
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "string":
        return isinstance(value, str)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "integer":
        if isinstance(value, bool):
            return False
        return isinstance(value, int) or (isinstance(value, float) and value.is_integer())
    raise SchemaError(f"unknown type {name!r}")


class Draft202012Validator:
    def __init__(self, schema: Any, format_checker: FormatChecker | None = None) -> None:
        self.schema = schema
        self.format_checker = format_checker
        self._check_schema(schema)

    # -- schema vetting -------------------------------------------------
    def _check_schema(self, schema: Any) -> None:
        if isinstance(schema, bool):
            return
        if not isinstance(schema, dict):
            raise SchemaError("schema must be an object or boolean")
        unknown = set(schema) - VALIDATION_KEYWORDS - ANNOTATION_KEYWORDS
        if unknown:
            raise SchemaError("unsupported schema keyword(s): " + ", ".join(sorted(unknown)))
        ref = schema.get("$ref")
        if ref is not None:
            self._resolve(ref)
        for key in ("properties", "patternProperties", "$defs", "definitions"):
            for sub in (schema.get(key) or {}).values():
                self._check_schema(sub)
        for key in ("additionalProperties", "items", "contains", "not", "if", "then", "else", "propertyNames"):
            if key in schema:
                self._check_schema(schema[key])
        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            for sub in schema.get(key) or []:
                self._check_schema(sub)

    def _resolve(self, ref: str) -> Any:
        if not isinstance(ref, str) or not ref.startswith("#"):
            raise SchemaError(f"only local $ref is supported: {ref!r}")
        node: Any = self.schema
        for part in [p for p in ref[1:].split("/") if p]:
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or part not in node:
                raise SchemaError(f"unresolvable $ref {ref!r}")
            node = node[part]
        return node

    # -- validation -----------------------------------------------------
    def is_valid(self, instance: Any) -> bool:
        return next(self.iter_errors(instance), None) is None

    def validate(self, instance: Any) -> None:
        for error in self.iter_errors(instance):
            raise error

    def iter_errors(self, instance: Any) -> Iterator[ValidationError]:
        yield from self._errors(instance, self.schema, ())

    def _errors(self, value: Any, schema: Any, path: tuple[Any, ...]) -> Iterator[ValidationError]:
        if schema is True:
            return
        if schema is False:
            yield ValidationError("False schema does not allow " + repr(value), path)
            return

        if "$ref" in schema:
            yield from self._errors(value, self._resolve(schema["$ref"]), path)

        if "type" in schema:
            types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
            if not any(_is_type(value, t) for t in types):
                yield ValidationError(f"{value!r} is not of type {', '.join(repr(t) for t in types)}", path)
                return

        if "const" in schema and _canonical(value) != _canonical(schema["const"]):
            yield ValidationError(f"{schema['const']!r} was expected", path)
        if "enum" in schema and _canonical(value) not in {_canonical(v) for v in schema["enum"]}:
            yield ValidationError(f"{value!r} is not one of {schema['enum']!r}", path)

        if isinstance(value, str):
            if "minLength" in schema and len(value) < schema["minLength"]:
                yield ValidationError(f"{value!r} is too short", path)
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                yield ValidationError(f"{value!r} is too long", path)
            if "pattern" in schema and not re.search(schema["pattern"], value):
                yield ValidationError(f"{value!r} does not match {schema['pattern']!r}", path)
            if "format" in schema and self.format_checker is not None \
                    and not self.format_checker.conforms(value, schema["format"]):
                yield ValidationError(f"{value!r} is not a {schema['format']!r}", path)

        if _is_type(value, "number"):
            if "minimum" in schema and value < schema["minimum"]:
                yield ValidationError(f"{value!r} is less than the minimum of {schema['minimum']!r}", path)
            if "maximum" in schema and value > schema["maximum"]:
                yield ValidationError(f"{value!r} is greater than the maximum of {schema['maximum']!r}", path)
            if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
                yield ValidationError(f"{value!r} is less than or equal to the minimum of {schema['exclusiveMinimum']!r}", path)
            if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
                yield ValidationError(f"{value!r} is greater than or equal to the maximum of {schema['exclusiveMaximum']!r}", path)
            if "multipleOf" in schema:
                quotient = value / schema["multipleOf"]
                if not (math.isfinite(quotient) and float(quotient).is_integer()):
                    yield ValidationError(f"{value!r} is not a multiple of {schema['multipleOf']!r}", path)

        if isinstance(value, dict):
            yield from self._object_errors(value, schema, path)
        if isinstance(value, list):
            yield from self._array_errors(value, schema, path)

        for sub in schema.get("allOf", []):
            yield from self._errors(value, sub, path)
        if "anyOf" in schema and not any(self._valid(value, sub, path) for sub in schema["anyOf"]):
            yield ValidationError(f"{value!r} is not valid under any of the given schemas", path)
        if "oneOf" in schema:
            matched = sum(1 for sub in schema["oneOf"] if self._valid(value, sub, path))
            if matched != 1:
                yield ValidationError(f"{value!r} is valid under {matched} of the given schemas, expected exactly one", path)
        if "not" in schema and self._valid(value, schema["not"], path):
            yield ValidationError(f"{value!r} should not be valid under {schema['not']!r}", path)
        if "if" in schema:
            branch = "then" if self._valid(value, schema["if"], path) else "else"
            if branch in schema:
                yield from self._errors(value, schema[branch], path)

    def _valid(self, value: Any, schema: Any, path: tuple[Any, ...]) -> bool:
        return next(self._errors(value, schema, path), None) is None

    def _object_errors(self, value: dict, schema: dict, path: tuple[Any, ...]) -> Iterator[ValidationError]:
        for name in schema.get("required", []):
            if name not in value:
                yield ValidationError(f"{name!r} is a required property", path)
        for name, needed in (schema.get("dependentRequired") or {}).items():
            if name in value:
                for other in needed:
                    if other not in value:
                        yield ValidationError(f"{other!r} is a dependency of {name!r}", path)
        if "minProperties" in schema and len(value) < schema["minProperties"]:
            yield ValidationError(f"{value!r} does not have enough properties", path)
        if "maxProperties" in schema and len(value) > schema["maxProperties"]:
            yield ValidationError(f"{value!r} has too many properties", path)
        properties = schema.get("properties", {})
        patterns = schema.get("patternProperties", {})
        extras = []
        for key, item in value.items():
            if "propertyNames" in schema:
                for error in self._errors(key, schema["propertyNames"], path):
                    yield ValidationError(f"{key!r} is not a valid property name: {error.message}", path)
            covered = False
            if key in properties:
                covered = True
                yield from self._errors(item, properties[key], path + (key,))
            for pattern, sub in patterns.items():
                if re.search(pattern, key):
                    covered = True
                    yield from self._errors(item, sub, path + (key,))
            if not covered:
                extras.append(key)
        additional = schema.get("additionalProperties", True)
        if additional is False and extras:
            listed = ", ".join(repr(k) for k in sorted(extras))
            yield ValidationError(f"Additional properties are not allowed ({listed} {'was' if len(extras) == 1 else 'were'} unexpected)", path)
        elif isinstance(additional, dict):
            for key in extras:
                yield from self._errors(value[key], additional, path + (key,))

    def _array_errors(self, value: list, schema: dict, path: tuple[Any, ...]) -> Iterator[ValidationError]:
        if "minItems" in schema and len(value) < schema["minItems"]:
            yield ValidationError(f"{value!r} should be non-empty" if schema["minItems"] == 1 else f"{value!r} is too short", path)
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            yield ValidationError(f"{value!r} is too long", path)
        if schema.get("uniqueItems"):
            seen = set()
            for item in value:
                key = _canonical(item)
                if key in seen:
                    yield ValidationError(f"{value!r} has non-unique elements", path)
                    break
                seen.add(key)
        prefix = schema.get("prefixItems", [])
        for index, sub in enumerate(prefix[:len(value)]):
            yield from self._errors(value[index], sub, path + (index,))
        if "items" in schema:
            for index in range(len(prefix), len(value)):
                yield from self._errors(value[index], schema["items"], path + (index,))
        if "contains" in schema:
            count = sum(1 for index, item in enumerate(value) if self._valid(item, schema["contains"], path + (index,)))
            low = schema.get("minContains", 1)
            high = schema.get("maxContains")
            if count < low:
                yield ValidationError(f"{value!r} does not contain items matching the given schema", path)
            if high is not None and count > high:
                yield ValidationError(f"{value!r} contains too many items matching the given schema", path)


def validate(instance: Any, schema: Any, format_checker: FormatChecker | None = None) -> None:
    """Raise the first ``ValidationError`` for ``instance``, as ``jsonschema.validate`` does."""
    for error in Draft202012Validator(schema, format_checker=format_checker).iter_errors(instance):
        raise error


__all__ = ["Draft202012Validator", "FormatChecker", "ValidationError", "SchemaError", "validate"]
