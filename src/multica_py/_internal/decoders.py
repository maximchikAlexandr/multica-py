from __future__ import annotations

from typing import TypeVar, cast

import msgspec

from multica_py.exceptions import EncodingError, JsonOutputError, OutputShapeError

T = TypeVar("T")


def _decode_with_private_autopilot_wire(
    data: bytes, model_type: object, *, command: str = ""
) -> object | None:
    """Decode public AutopilotRun shapes through the private recursive wire.

    ``JsonValue`` is intentionally a closed public annotation, but msgspec's
    runtime schema compiler does not support the recursive alias.  Keep that
    implementation detail at this boundary instead of weakening the public
    model annotations.
    """
    from multica_py._internal.wire_models import (
        _autopilot_list_page_from_wire,
        _autopilot_run_from_wire,
        _AutopilotListWire,
        _AutopilotRunListPageWire,
        _AutopilotRunWire,
    )
    from multica_py.models.autopilots import AutopilotListPage, AutopilotRunListPage
    from multica_py.resources.autopilots import Autopilot, AutopilotRun

    if model_type == AutopilotListPage[Autopilot]:
        wire_page = decode_json(data, _AutopilotListWire, command=command)
        return _autopilot_list_page_from_wire(wire_page)

    if model_type is AutopilotRun:
        wire_run = decode_json(data, _AutopilotRunWire, command=command)
        return _autopilot_run_from_wire(wire_run)

    if model_type == AutopilotRunListPage[AutopilotRun]:
        run_wire_page = decode_json(data, _AutopilotRunListPageWire, command=command)
        return AutopilotRunListPage(
            items=tuple(_autopilot_run_from_wire(run) for run in run_wire_page.runs),
            total=run_wire_page.total,
        )
    return None


def decode_json(data: bytes | str, model_type: type[T], *, command: str = "") -> T:
    if isinstance(data, str):
        data = data.encode("utf-8")
    try:
        private_decoded = _decode_with_private_autopilot_wire(data, model_type, command=command)
        if private_decoded is None:
            decoded = msgspec.json.decode(data, type=model_type, strict=True)
        else:
            decoded = cast("T", private_decoded)
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
    return decoded


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
