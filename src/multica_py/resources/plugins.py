from __future__ import annotations

import os
from typing import cast

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _PluginDigestWire,
    _PluginWire,
    plugin_digest_from_wire,
    plugin_from_wire,
)
from multica_py.config import ClientConfig, OperationOptions
from multica_py.models.common import ActionResult, Page
from multica_py.models.plugins import Plugin, PluginDigest
from multica_py.resources._base import BaseResource, _validate_optional_string
from multica_py.sentinels import Unset, UnsetType
from multica_py.types import JsonValue

__all__ = ["Plugin", "PluginDigest", "PluginResource"]


class PluginResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    @staticmethod
    def _decode_plugins(stdout: bytes, command: str) -> Page[Plugin]:
        try:
            rows = decode_json(stdout, list[_PluginWire], command=command)
            items = tuple(plugin_from_wire(row) for row in rows)
            return Page(items=items, total=len(items))
        except msgspec.ValidationError:
            row = decode_json(stdout, _PluginWire, command=command)
            item = plugin_from_wire(row)
            return Page(items=(item,), total=1)

    @staticmethod
    def _decode_plugin_digest(stdout: bytes, command: str) -> PluginDigest:
        row = decode_json(stdout, _PluginDigestWire, command=command)
        return plugin_digest_from_wire(row)

    def list_command(self, *, options: OperationOptions | None = None) -> Command[Page[Plugin]]:
        return self._plugins_page_command(("plugin", "list"), options=options)

    def list(self, *, options: OperationOptions | None = None) -> Page[Plugin]:
        return self.list_command(options=options).run()

    def status_command(
        self, plugin_key_or_id: str | None = None, *, options: OperationOptions | None = None
    ) -> Command[Page[Plugin]]:
        args: tuple[str, ...] = ("plugin", "status")
        if plugin_key_or_id is not None:
            validate_nonblank(plugin_key_or_id)
            args = (*args, plugin_key_or_id)
        return self._plugins_page_command(args, options=options)

    def status(
        self, plugin_key_or_id: str | None = None, *, options: OperationOptions | None = None
    ) -> Page[Plugin]:
        return self.status_command(plugin_key_or_id, options=options).run()

    def validate_command(
        self, source: str | os.PathLike[str], *, options: OperationOptions | None = None
    ) -> Command[PluginDigest]:
        validate_nonblank(str(source))
        return self._plugin_digest_command(
            ("plugin", "validate", os.fspath(source)), options=options
        )

    def validate(
        self, source: str | os.PathLike[str], *, options: OperationOptions | None = None
    ) -> PluginDigest:
        return self.validate_command(source, options=options).run()

    def pack_command(
        self,
        directory: str | os.PathLike[str],
        *,
        output: str | os.PathLike[str],
        options: OperationOptions | None = None,
    ) -> Command[PluginDigest]:
        validate_nonblank(str(directory))
        validate_nonblank(str(output))
        return self._plugin_digest_command(
            (
                "plugin",
                "pack",
                os.fspath(directory),
                "--output",
                os.fspath(output),
                "--format",
                "json",
            ),
            options=options,
        )

    def pack(
        self,
        directory: str | os.PathLike[str],
        *,
        output: str | os.PathLike[str],
        options: OperationOptions | None = None,
    ) -> PluginDigest:
        return self.pack_command(directory, output=output, options=options).run()

    def init_command(
        self,
        directory: str | os.PathLike[str],
        *,
        key: str | UnsetType = Unset,
        name: str | UnsetType = Unset,
        publisher: str | UnsetType = Unset,
        contribution: str | UnsetType = Unset,
        endpoint_host: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        validate_nonblank(str(directory))
        args = ["plugin", "init", os.fspath(directory), "--output", "json"]
        for flag, value in (
            ("--key", key),
            ("--name", name),
            ("--publisher", publisher),
            ("--contribution", contribution),
            ("--endpoint-host", endpoint_host),
        ):
            if value is not Unset:
                _validate_optional_string(value, flag.removeprefix("--").replace("-", "_"))
                args.extend([flag, str(value)])
        return self._action_command(tuple(args), options=options)

    def init(
        self,
        directory: str | os.PathLike[str],
        *,
        key: str | UnsetType = Unset,
        name: str | UnsetType = Unset,
        publisher: str | UnsetType = Unset,
        contribution: str | UnsetType = Unset,
        endpoint_host: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> ActionResult[None]:
        return self.init_command(
            directory,
            key=key,
            name=name,
            publisher=publisher,
            contribution=contribution,
            endpoint_host=endpoint_host,
            options=options,
        ).run()

    def install_command(
        self,
        source: str | os.PathLike[str],
        *,
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Plugin]:
        validate_nonblank(str(source))
        args = ["plugin", "install", os.fspath(source), "--output", "json"]
        if workspace is not Unset:
            validate_nonblank(workspace)
            args.extend(["--workspace", workspace])
        return self._plugin_model_command(tuple(args), options=options)

    def install(
        self,
        source: str | os.PathLike[str],
        *,
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Plugin:
        return self.install_command(source, workspace=workspace, options=options).run()

    def configure_remote_mcp_command(
        self,
        installation_id: str,
        contribution_key: str,
        *,
        endpoint: str,
        credential_file: str | os.PathLike[str] | None = None,
        credential_stdin: bytes | None = None,
        auth_type: str | UnsetType = Unset,
        auth_header: str | UnsetType = Unset,
        failure_policy: str | UnsetType = Unset,
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[dict[str, JsonValue]]:
        validate_nonblank(installation_id)
        validate_nonblank(contribution_key)
        validate_nonblank(endpoint)
        if credential_stdin is not None and not isinstance(credential_stdin, bytes):
            raise TypeError("credential_stdin must be bytes or None")
        if credential_stdin is not None and credential_file is not None:
            raise ValueError("credential_file and credential_stdin are mutually exclusive")
        args = [
            "plugin",
            "remote-mcp",
            "configure",
            installation_id,
            contribution_key,
            "--endpoint",
            endpoint,
            "--output",
            "json",
        ]
        if credential_stdin is not None:
            args.append("--credential-stdin")
        elif credential_file is not None:
            args.extend(["--credential-file", os.fspath(credential_file)])
        for flag, value in (
            ("--auth-type", auth_type),
            ("--auth-header", auth_header),
            ("--failure-policy", failure_policy),
            ("--workspace", workspace),
        ):
            if value is not Unset:
                _validate_optional_string(value, flag.removeprefix("--").replace("-", "_"))
                args.extend([flag, str(value)])
        return self._remote_mcp_command(tuple(args), stdin=credential_stdin, options=options)

    def configure_remote_mcp(
        self,
        installation_id: str,
        contribution_key: str,
        *,
        endpoint: str,
        credential_file: str | os.PathLike[str] | None = None,
        credential_stdin: bytes | None = None,
        auth_type: str | UnsetType = Unset,
        auth_header: str | UnsetType = Unset,
        failure_policy: str | UnsetType = Unset,
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> dict[str, JsonValue]:
        return self.configure_remote_mcp_command(
            installation_id,
            contribution_key,
            endpoint=endpoint,
            credential_file=credential_file,
            credential_stdin=credential_stdin,
            auth_type=auth_type,
            auth_header=auth_header,
            failure_policy=failure_policy,
            workspace=workspace,
            options=options,
        ).run()

    def test_remote_mcp_command(
        self,
        installation_id: str,
        contribution_key: str,
        *,
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[dict[str, JsonValue]]:
        validate_nonblank(installation_id)
        validate_nonblank(contribution_key)
        args = [
            "plugin",
            "remote-mcp",
            "test",
            installation_id,
            contribution_key,
            "--output",
            "json",
        ]
        if workspace is not Unset:
            validate_nonblank(workspace)
            args.extend(["--workspace", workspace])
        return self._remote_mcp_command(tuple(args), options=options)

    def test_remote_mcp(
        self,
        installation_id: str,
        contribution_key: str,
        *,
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> dict[str, JsonValue]:
        return self.test_remote_mcp_command(
            installation_id, contribution_key, workspace=workspace, options=options
        ).run()

    def approve_remote_mcp_command(
        self,
        installation_id: str,
        contribution_key: str,
        *,
        tools: tuple[str, ...],
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[dict[str, JsonValue]]:
        validate_nonblank(installation_id)
        validate_nonblank(contribution_key)
        if not tools:
            raise ValueError("tools must contain at least one tool name")
        args = [
            "plugin",
            "remote-mcp",
            "approve",
            installation_id,
            contribution_key,
            "--output",
            "json",
        ]
        for tool in tools:
            validate_nonblank(tool)
            args.extend(["--tool", tool])
        if workspace is not Unset:
            validate_nonblank(workspace)
            args.extend(["--workspace", workspace])
        return self._remote_mcp_command(tuple(args), options=options)

    def approve_remote_mcp(
        self,
        installation_id: str,
        contribution_key: str,
        *,
        tools: tuple[str, ...],
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> dict[str, JsonValue]:
        return self.approve_remote_mcp_command(
            installation_id,
            contribution_key,
            tools=tools,
            workspace=workspace,
            options=options,
        ).run()

    def revoke_remote_mcp_command(
        self,
        installation_id: str,
        contribution_key: str,
        *,
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[dict[str, JsonValue]]:
        validate_nonblank(installation_id)
        validate_nonblank(contribution_key)
        args = [
            "plugin",
            "remote-mcp",
            "revoke",
            installation_id,
            contribution_key,
            "--output",
            "json",
        ]
        if workspace is not Unset:
            validate_nonblank(workspace)
            args.extend(["--workspace", workspace])
        return self._remote_mcp_command(tuple(args), options=options)

    def revoke_remote_mcp(
        self,
        installation_id: str,
        contribution_key: str,
        *,
        workspace: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> dict[str, JsonValue]:
        return self.revoke_remote_mcp_command(
            installation_id, contribution_key, workspace=workspace, options=options
        ).run()

    def _plugins_page_command(
        self, args: tuple[str, ...], *, options: OperationOptions | None
    ) -> Command[Page[Plugin]]:
        plan_args = (*args, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            return self._decode_plugins(stdout, command)

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("Page[Plugin]", results[0]),
            options=options,
        )

    def _plugin_digest_command(
        self, args: tuple[str, ...], *, options: OperationOptions | None
    ) -> Command[PluginDigest]:
        plan_args = (
            args
            if "--format" in args or args[-2:] == ("--output", "json")
            else (*args, "--output", "json")
        )

        def decode(stdout: bytes, command: str) -> object:
            return self._decode_plugin_digest(stdout, command)

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("PluginDigest", results[0]),
            options=options,
        )

    def _plugin_model_command(
        self, args: tuple[str, ...], *, options: OperationOptions | None
    ) -> Command[Plugin]:
        plan_args = args if args[-2:] == ("--output", "json") else (*args, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            return decode_json(stdout, Plugin, command=command)

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("Plugin", results[0]),
            options=options,
        )

    def _remote_mcp_command(
        self,
        args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        options: OperationOptions | None = None,
    ) -> Command[dict[str, JsonValue]]:
        def decode(stdout: bytes, command: str) -> object:
            return decode_json(stdout, dict[str, object], command=command)

        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode, stdin=stdin),),
            finalize=lambda results: cast("dict[str, JsonValue]", results[0]),
            options=options,
            capture_output_label="plugin.remote_mcp",
        )
