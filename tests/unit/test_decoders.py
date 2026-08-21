from __future__ import annotations

import msgspec
import pytest

from multica_py._internal.decoders import decode_json, decode_text
from multica_py.exceptions import EncodingError, JsonOutputError, OutputShapeError


class SimpleModel(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    value: int | None = None


def test_decode_valid_json():
    result = decode_json(b'{"name": "test", "value": 42}', SimpleModel)
    assert result.name == "test"
    assert result.value == 42


def test_decode_additive_unknown_fields():
    result = decode_json(b'{"name": "test", "unknown": "ignored"}', SimpleModel)
    assert result.name == "test"
    assert result.value is None


def test_decode_missing_required_field():
    with pytest.raises(OutputShapeError):
        decode_json(b'{"value": 42}', SimpleModel)


def test_decode_malformed_json():
    with pytest.raises(JsonOutputError):
        decode_json(b"not json", SimpleModel)


def test_decode_empty_output():
    with pytest.raises((JsonOutputError, OutputShapeError)):
        decode_json(b"", SimpleModel)


def test_decode_text():
    result = decode_text(b"hello world")
    assert result == "hello world"


def test_decode_text_invalid_utf8_raises_encoding_error():
    with pytest.raises(EncodingError, match="bad command"):
        decode_text(b"\xff", command="bad command")
