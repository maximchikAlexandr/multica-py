from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class PropertyInputCase:
    id: str
    property_type: str | None
    value: object
    error_type: type[Exception]
    message: str


@dataclass(frozen=True)
class AcceptedPropertyInputCase:
    id: str
    property_type: str
    value: object
    encoded: str


@dataclass(frozen=True)
class MalformedScalarPropertyCase:
    id: str
    property_type: str
    value: object
    message: str


PROPERTY_INVALID_CASES = (
    PropertyInputCase("empty", "multi_text", (), ValueError, "at least one string"),
    PropertyInputCase(
        "too-many-unique",
        "multi_text",
        tuple(f"value-{index}" for index in range(21)),
        ValueError,
        "more than 20 unique strings",
    ),
    PropertyInputCase("blank", "multi_text", ("",), ValueError, "blank strings"),
    PropertyInputCase("null", "multi_text", None, TypeError, "cannot be null"),
    PropertyInputCase(
        "non-string-item", "multi_text", ["ok", 1], TypeError, "tuple must contain only strings"
    ),
    PropertyInputCase(
        "unsupported-discriminator", "text", "value", ValueError, "must be multi_text"
    ),
    PropertyInputCase("scalar-non-string", "multi_text", 1, TypeError, "sequence of strings"),
    PropertyInputCase(
        "scalar-non-string-without-discriminator", None, 1, TypeError, "value must be a string"
    ),
    PropertyInputCase(
        "malformed-json", "multi_text", '["ok",', ValueError, "JSON value is invalid"
    ),
    PropertyInputCase("text-too-long", "multi_text", ("a" * 2001,), ValueError, "2000 characters"),
    PropertyInputCase("url-scheme", "multi_url", ("not-a-url",), ValueError, r"HTTP\(S\) URLs"),
    PropertyInputCase(
        "url-too-long",
        "multi_url",
        ("https://" + "a" * 2041,),
        ValueError,
        "2048 characters",
    ),
    PropertyInputCase(
        "sequence-without-discriminator", None, ["alpha"], TypeError, "property_type is required"
    ),
)

PROPERTY_ACCEPTED_CASES = (
    AcceptedPropertyInputCase(
        "max-count",
        "multi_text",
        tuple(f"value-{index}" for index in range(20)),
        "[" + ",".join(f'"value-{index}"' for index in range(20)) + "]",
    ),
    AcceptedPropertyInputCase(
        "deduplicated-list",
        "multi_text",
        ["alpha", "beta", "alpha"],
        '["alpha","beta"]',
    ),
    AcceptedPropertyInputCase(
        "text-element-at-limit",
        "multi_text",
        ("a" * 2000,),
        json.dumps(["a" * 2000], separators=(",", ":")),
    ),
    AcceptedPropertyInputCase(
        "url-element-at-limit",
        "multi_url",
        ("https://" + "a" * (2048 - len("https://")),),
        json.dumps(["https://" + "a" * (2048 - len("https://"))], separators=(",", ":")),
    ),
)

MALFORMED_SCALAR_PROPERTY_CASES = (
    MalformedScalarPropertyCase(
        "scalar-nonscalar",
        "select",
        {"nested": "value"},
        "scalar property value must be a scalar",
    ),
)
