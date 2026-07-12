from __future__ import annotations

from typing import TypeVar

import msgspec

from multica_py.exceptions import EncodingError, JsonOutputError, OutputShapeError

T = TypeVar("T")


def decode_json(data: bytes | str, model_type: type[T], *, command: str = "") -> T:
    if isinstance(data, str):
        data = data.encode("utf-8")
    try:
        return msgspec.json.decode(data, type=model_type, strict=True)
    except msgspec.ValidationError as e:
        msg = f"Output shape error: {e}"
        if command:
            msg += f" [command: {command}]"
        raise OutputShapeError(msg) from e
    except msgspec.DecodeError as e:
        msg = f"JSON decode error: {e}"
        if command:
            msg += f" [command: {command}]"
        raise JsonOutputError(msg) from e


def decode_text(data: bytes | str, *, command: str = "") -> str:
    if isinstance(data, bytes):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as e:
            msg = f"Text decode error: {e}"
            if command:
                msg += f" [command: {command}]"
            raise EncodingError(msg) from e
    return data
