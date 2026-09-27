from __future__ import annotations

import pathlib
from typing import cast

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py.config import OperationOptions
from multica_py.exceptions import OutputShapeError
from multica_py.models.common import ActionResult
from multica_py.models.system import RuntimeProfile, RuntimeProfiles
from multica_py.resources._base import BaseResource

__all__ = ["RuntimeProfile", "RuntimeProfileResource", "RuntimeProfiles"]


def _decode_profile(stdout: bytes, command: str) -> RuntimeProfile:
    return decode_json(stdout, RuntimeProfile, command=command)


def _decode_profiles(stdout: bytes, command: str) -> RuntimeProfiles:
    values: object
    if stdout.lstrip().startswith(b"["):
        values = decode_json(stdout, list[dict[str, object]], command=command)
    else:
        raw = decode_json(stdout, dict[str, object], command=command)
        values = raw.get("profiles", raw.get("items", ()))
    if not isinstance(values, list):
        raise OutputShapeError(f"Runtime profile output must contain a list [command: {command}]")
    try:
        profiles = tuple(
            msgspec.convert(value, type=RuntimeProfile, strict=True) for value in values
        )
    except (msgspec.ValidationError, msgspec.DecodeError) as error:
        raise OutputShapeError(f"Invalid runtime profile output [command: {command}]") from error
    return RuntimeProfiles(items=profiles)


class RuntimeProfileResource(BaseResource):
    def list_command(self, *, options: OperationOptions | None = None) -> Command[RuntimeProfiles]:
        return self._plan(
            steps=(
                _Step(
                    ("runtime", "profile", "list", "--output", "json"),
                    "run_bytes",
                    decode=_decode_profiles,
                    minimum_cli_version="0.5.3",
                ),
            ),
            finalize=lambda results: cast("RuntimeProfiles", results[0]),
            options=options,
        )

    def list(self, *, options: OperationOptions | None = None) -> RuntimeProfiles:
        return self.list_command(options=options).run()

    def create_command(
        self,
        *,
        runtime_type: str | None = None,
        protocol_family: str | None = None,
        command_name: str,
        display_name: str,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[RuntimeProfile]:
        if runtime_type is None and protocol_family is None:
            raise ValueError("runtime_type or protocol_family is required")
        validate_nonblank(command_name)
        validate_nonblank(display_name)
        args = ["runtime", "profile", "create"]
        for flag, value in (
            ("--runtime-type", runtime_type),
            ("--protocol-family", protocol_family),
            ("--command-name", command_name),
            ("--display-name", display_name),
            ("--description", description),
        ):
            if value is not None:
                args.extend((flag, value))
        return self._plan_profile_command(tuple(args), options=options)

    def create(
        self,
        *,
        runtime_type: str | None = None,
        protocol_family: str | None = None,
        command_name: str,
        display_name: str,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> RuntimeProfile:
        return self.create_command(
            runtime_type=runtime_type,
            protocol_family=protocol_family,
            command_name=command_name,
            display_name=display_name,
            description=description,
            options=options,
        ).run()

    def update_command(
        self,
        profile_id: str,
        *,
        display_name: str | None = None,
        command_name: str | None = None,
        description: str | None = None,
        enabled: bool | None = None,
        options: OperationOptions | None = None,
    ) -> Command[RuntimeProfile]:
        validate_nonblank(profile_id)
        if all(value is None for value in (display_name, command_name, description, enabled)):
            raise ValueError("at least one runtime profile field is required")
        args = ["runtime", "profile", "update", profile_id]
        for flag, value in (
            ("--display-name", display_name),
            ("--command-name", command_name),
            ("--description", description),
        ):
            if value is not None:
                args.extend((flag, value))
        if enabled is not None:
            args.append(f"--enabled={'true' if enabled else 'false'}")
        return self._plan_profile_command(tuple(args), options=options)

    def update(
        self,
        profile_id: str,
        *,
        display_name: str | None = None,
        command_name: str | None = None,
        description: str | None = None,
        enabled: bool | None = None,
        options: OperationOptions | None = None,
    ) -> RuntimeProfile:
        return self.update_command(
            profile_id,
            display_name=display_name,
            command_name=command_name,
            description=description,
            enabled=enabled,
            options=options,
        ).run()

    def delete_command(
        self, profile_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(profile_id)
        return self._action_command(("runtime", "profile", "delete", profile_id), options=options)

    def delete(
        self, profile_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(profile_id, options=options).run()

    def set_path_command(
        self,
        profile_id: str,
        path: pathlib.Path,
        *,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        validate_nonblank(profile_id)
        if not path.is_absolute():
            raise ValueError("path must be absolute")
        return self._action_command(
            ("runtime", "profile", "set-path", profile_id, "--path", str(path)),
            options=options,
        )

    def set_path(
        self,
        profile_id: str,
        path: pathlib.Path,
        *,
        options: OperationOptions | None = None,
    ) -> ActionResult[None]:
        return self.set_path_command(profile_id, path, options=options).run()

    def unset_path_command(
        self, profile_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(profile_id)
        return self._action_command(
            ("runtime", "profile", "unset-path", profile_id), options=options
        )

    def unset_path(
        self, profile_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.unset_path_command(profile_id, options=options).run()

    def _plan_profile_command(
        self, args: tuple[str, ...], *, options: OperationOptions | None
    ) -> Command[RuntimeProfile]:
        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_bytes", decode=_decode_profile),),
            finalize=lambda results: cast("RuntimeProfile", results[0]),
            options=options,
            minimum_cli_version="0.5.3",
        )
