from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import _PropertyDefinitionWire, property_definition_from_wire
from multica_py.config import ClientConfig, OperationOptions
from multica_py.models.common import Page
from multica_py.models.properties import PropertyDefinition
from multica_py.resources._base import BaseResource, _validate_optional_string
from multica_py.sentinels import Unset, UnsetType

__all__ = ["PropertyDefinition", "PropertyResource"]

_ACTOR_TYPES = frozenset({"actor", "multi_actor"})


class PropertyResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    @staticmethod
    def _decode_property_definitions(stdout: bytes, command: str) -> Page[PropertyDefinition]:
        rows = decode_json(stdout, list[_PropertyDefinitionWire], command=command)
        items = tuple(property_definition_from_wire(row) for row in rows)
        return Page(items=items, total=len(items))

    def list_command(
        self, *, include_archived: bool = False, options: OperationOptions | None = None
    ) -> Command[Page[PropertyDefinition]]:
        args: list[str] = ["property", "list"]
        if include_archived:
            args.append("--include-archived")
        return self._property_definitions_page_command(tuple(args), options=options)

    def list(
        self, *, include_archived: bool = False, options: OperationOptions | None = None
    ) -> Page[PropertyDefinition]:
        return self.list_command(include_archived=include_archived, options=options).run()

    def get_command(
        self, property_ref: str, *, options: OperationOptions | None = None
    ) -> Command[PropertyDefinition]:
        validate_nonblank(property_ref)
        return self._property_definition_command(("property", "get", property_ref), options=options)

    def get(
        self, property_ref: str, *, options: OperationOptions | None = None
    ) -> PropertyDefinition:
        return self.get_command(property_ref, options=options).run()

    def create_command(
        self,
        *,
        name: str,
        property_type: str,
        description: str | UnsetType = Unset,
        icon: str | UnsetType = Unset,
        options_values: tuple[str, ...] | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[PropertyDefinition]:
        validate_nonblank(name)
        validate_nonblank(property_type)
        if options_values is not Unset and property_type in _ACTOR_TYPES:
            raise ValueError("options_values are not supported for actor property types")
        args = ["property", "create", "--name", name, "--type", property_type]
        if description is not Unset:
            _validate_optional_string(description, "description")
            args.extend(["--description", description])
        if icon is not Unset:
            _validate_optional_string(icon, "icon")
            args.extend(["--icon", icon])
        if options_values is not Unset:
            for option in options_values:
                validate_nonblank(option)
                args.extend(["--option", option])
        return self._property_definition_command(tuple(args), options=options)

    def create(
        self,
        *,
        name: str,
        property_type: str,
        description: str | UnsetType = Unset,
        icon: str | UnsetType = Unset,
        options_values: tuple[str, ...] | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> PropertyDefinition:
        return self.create_command(
            name=name,
            property_type=property_type,
            description=description,
            icon=icon,
            options_values=options_values,
            options=options,
        ).run()

    def update_command(
        self,
        property_ref: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        icon: str | UnsetType = Unset,
        options_values: tuple[str, ...] | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[PropertyDefinition]:
        validate_nonblank(property_ref)
        args = ["property", "update", property_ref]
        if name is not Unset:
            validate_nonblank(name)
            args.extend(["--name", name])
        if description is not Unset:
            args.extend(["--description", "" if description is None else description])
        if icon is not Unset:
            _validate_optional_string(icon, "icon")
            args.extend(["--icon", icon])
        if options_values is not Unset:
            for option in options_values:
                validate_nonblank(option)
                args.extend(["--option", option])
        return self._property_definition_command(tuple(args), options=options)

    def update(
        self,
        property_ref: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        icon: str | UnsetType = Unset,
        options_values: tuple[str, ...] | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> PropertyDefinition:
        return self.update_command(
            property_ref,
            name=name,
            description=description,
            icon=icon,
            options_values=options_values,
            options=options,
        ).run()

    def archive_command(
        self, property_ref: str, *, options: OperationOptions | None = None
    ) -> Command[PropertyDefinition]:
        validate_nonblank(property_ref)
        return self._property_definition_command(
            ("property", "archive", property_ref), options=options
        )

    def archive(
        self, property_ref: str, *, options: OperationOptions | None = None
    ) -> PropertyDefinition:
        return self.archive_command(property_ref, options=options).run()

    def unarchive_command(
        self, property_ref: str, *, options: OperationOptions | None = None
    ) -> Command[PropertyDefinition]:
        validate_nonblank(property_ref)
        return self._property_definition_command(
            ("property", "unarchive", property_ref), options=options
        )

    def unarchive(
        self, property_ref: str, *, options: OperationOptions | None = None
    ) -> PropertyDefinition:
        return self.unarchive_command(property_ref, options=options).run()

    def _property_definitions_page_command(
        self, args: tuple[str, ...], *, options: OperationOptions | None
    ) -> Command[Page[PropertyDefinition]]:
        plan_args = (*args, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            return self._decode_property_definitions(stdout, command)

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("Page[PropertyDefinition]", results[0]),
            options=options,
        )

    def _property_definition_command(
        self, args: tuple[str, ...], *, options: OperationOptions | None
    ) -> Command[PropertyDefinition]:
        plan_args = (*args, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            row = decode_json(stdout, _PropertyDefinitionWire, command=command)
            return property_definition_from_wire(row)

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("PropertyDefinition", results[0]),
            options=options,
        )
