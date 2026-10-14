from __future__ import annotations

import json
from typing import cast

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.exceptions import OutputShapeError
from multica_py.models.common import ActionResult
from multica_py.models.properties import PropertyValue, PropertyValueType
from multica_py.resources._base import BaseResource
from multica_py.types import MetadataValue

__all__ = ["IssuePropertyResource", "PropertyValue"]


class _PropertyValueWire(msgspec.Struct, frozen=True, kw_only=True):
    property_id: str
    name: str
    type: str
    value: object
    display: str = ""
    archived: bool = False


class IssuePropertyResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    @staticmethod
    def _decode_property_values(stdout: bytes, command: str) -> tuple[PropertyValue, ...]:
        rows = decode_json(stdout, list[_PropertyValueWire], command=command)
        return tuple(
            PropertyValue(
                property_id=row.property_id,
                name=row.name,
                type=row.type,
                value=_decode_property_value(row.type, row.value),
                display=row.display,
                archived=row.archived,
            )
            for row in rows
        )

    def list_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[tuple[PropertyValue, ...]]:
        validate_nonblank(issue_id)
        return self._property_values_command(
            ("issue", "property", "list", issue_id), options=options
        )

    def list(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> tuple[PropertyValue, ...]:
        return self.list_command(issue_id, options=options).run()

    def set_command(
        self,
        issue_id: str,
        *,
        name: str,
        value: str | tuple[str, ...],
        options: OperationOptions | None = None,
    ) -> Command[tuple[PropertyValue, ...]]:
        validate_nonblank(issue_id)
        validate_nonblank(name)
        encoded_value = _encode_property_value(value)
        return self._property_values_command(
            (
                "issue",
                "property",
                "set",
                issue_id,
                "--name",
                name,
                "--value",
                encoded_value,
            ),
            options=options,
        )

    def set(
        self,
        issue_id: str,
        *,
        name: str,
        value: str | tuple[str, ...],
        options: OperationOptions | None = None,
    ) -> tuple[PropertyValue, ...]:
        return self.set_command(issue_id, name=name, value=value, options=options).run()

    def unset_command(
        self,
        issue_id: str,
        *,
        name: str,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        validate_nonblank(issue_id)
        validate_nonblank(name)
        return self._action_command(
            (
                "issue",
                "property",
                "unset",
                issue_id,
                "--name",
                name,
                "--output",
                "json",
            ),
            options=options,
        )

    def unset(
        self,
        issue_id: str,
        *,
        name: str,
        options: OperationOptions | None = None,
    ) -> ActionResult[None]:
        return self.unset_command(issue_id, name=name, options=options).run()

    def _property_values_command(
        self, args: tuple[str, ...], *, options: OperationOptions | None
    ) -> Command[tuple[PropertyValue, ...]]:
        plan_args = (*args, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            return self._decode_property_values(stdout, command)

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("tuple[PropertyValue, ...]", results[0]),
            options=options,
        )


def _encode_property_value(value: str | tuple[str, ...]) -> str:
    if type(value) is str:
        return value
    if type(value) is not tuple:
        raise TypeError("value must be a string or tuple of strings")
    if not value:
        raise ValueError("value must contain at least one string")
    if any(type(item) is not str for item in value):
        raise TypeError("value tuple must contain only strings")
    if any(not item.strip() for item in value):
        raise ValueError("value tuple cannot contain blank strings")
    unique: list[str] = []
    for item in value:
        if item not in unique:
            unique.append(item)
    if len(unique) > 20:
        raise ValueError("value cannot contain more than 20 unique strings")
    return json.dumps(unique, ensure_ascii=False, separators=(",", ":"))


def _decode_property_value(property_type: str, value: object) -> PropertyValueType:
    if property_type in {"multi_text", "multi_url"}:
        if not isinstance(value, (list, tuple)) or any(type(item) is not str for item in value):
            raise OutputShapeError("list property value must be an array of strings")
        return tuple(cast("tuple[str, ...]", value))
    if value is None or type(value) in {str, int, float, bool}:
        return cast("MetadataValue", value)
    raise OutputShapeError("scalar property value must be a scalar")
