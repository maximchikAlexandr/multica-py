from __future__ import annotations

import os
from typing import cast

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.models.common import Page
from multica_py.models.workspaces import McpServer
from multica_py.resources._base import BaseResource, _validate_optional_string
from multica_py.sentinels import Unset, UnsetType

__all__ = ["WorkspaceMcpResource"]


class _McpServerWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    transport: str
    enabled: bool | None = None


def _mcp_server_from_wire(row: _McpServerWire) -> McpServer:
    return McpServer(id=row.id, name=row.name, transport=row.transport, enabled=row.enabled)


class WorkspaceMcpResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    @staticmethod
    def _decode_mcp_servers(stdout: bytes, command: str) -> Page[McpServer]:
        try:
            rows = decode_json(stdout, list[_McpServerWire], command=command)
            items = tuple(_mcp_server_from_wire(row) for row in rows)
            return Page(items=items, total=len(items))
        except msgspec.ValidationError:
            row = decode_json(stdout, _McpServerWire, command=command)
            item = _mcp_server_from_wire(row)
            return Page(items=(item,), total=1)

    def list_command(self, *, options: OperationOptions | None = None) -> Command[Page[McpServer]]:
        return self._mcp_page_command(("workspace", "mcp", "list"), options=options)

    def list(self, *, options: OperationOptions | None = None) -> Page[McpServer]:
        return self.list_command(options=options).run()

    def add_command(
        self,
        server_name: str,
        *,
        server_config_file: str | os.PathLike[str] | None = None,
        server_config_stdin: bytes | None = None,
        server_config: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Page[McpServer]]:
        validate_nonblank(server_name)
        channels = _config_channels(
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
        )
        if channels != 1:
            raise ValueError(
                "exactly one of server_config_file, server_config_stdin, or server_config is required"
            )
        args = ["workspace", "mcp", "add", server_name]
        args = _append_config_args(
            args,
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
        )
        return self._mcp_page_command(tuple(args), stdin=server_config_stdin, options=options)

    def add(
        self,
        server_name: str,
        *,
        server_config_file: str | os.PathLike[str] | None = None,
        server_config_stdin: bytes | None = None,
        server_config: str | None = None,
        options: OperationOptions | None = None,
    ) -> Page[McpServer]:
        return self.add_command(
            server_name,
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
            options=options,
        ).run()

    def update_command(
        self,
        server_id: str,
        *,
        name: str | UnsetType = Unset,
        server_config_file: str | os.PathLike[str] | None = None,
        server_config_stdin: bytes | None = None,
        server_config: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Page[McpServer]]:
        validate_nonblank(server_id)
        channels = _config_channels(
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
        )
        if channels > 1:
            raise ValueError(
                "only one of server_config_file, server_config_stdin, or server_config may be set"
            )
        args = ["workspace", "mcp", "update", server_id]
        if name is not Unset:
            _validate_optional_string(name, "name")
            args.extend(["--name", name])
        args = _append_config_args(
            args,
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
        )
        return self._mcp_page_command(tuple(args), stdin=server_config_stdin, options=options)

    def update(
        self,
        server_id: str,
        *,
        name: str | UnsetType = Unset,
        server_config_file: str | os.PathLike[str] | None = None,
        server_config_stdin: bytes | None = None,
        server_config: str | None = None,
        options: OperationOptions | None = None,
    ) -> Page[McpServer]:
        return self.update_command(
            server_id,
            name=name,
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
            options=options,
        ).run()

    def remove_command(
        self, server_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[McpServer]]:
        validate_nonblank(server_id)
        return self._mcp_page_command(("workspace", "mcp", "remove", server_id), options=options)

    def remove(self, server_id: str, *, options: OperationOptions | None = None) -> Page[McpServer]:
        return self.remove_command(server_id, options=options).run()

    def _mcp_page_command(
        self,
        args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        options: OperationOptions | None,
    ) -> Command[Page[McpServer]]:
        plan_args = (*args, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            return self._decode_mcp_servers(stdout, command)

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode, stdin=stdin),),
            finalize=lambda results: cast("Page[McpServer]", results[0]),
            options=options,
        )


def _config_channels(
    *,
    server_config_file: str | os.PathLike[str] | None,
    server_config_stdin: bytes | None,
    server_config: str | None,
) -> int:
    if server_config_stdin is not None and not isinstance(server_config_stdin, bytes):
        raise TypeError("server_config_stdin must be bytes or None")
    return sum(
        (
            server_config_file is not None,
            server_config_stdin is not None,
            server_config is not None,
        )
    )


def _append_config_args(
    args: list[str],
    *,
    server_config_file: str | os.PathLike[str] | None,
    server_config_stdin: bytes | None,
    server_config: str | None,
) -> list[str]:
    if server_config_stdin is not None:
        args.append("--server-config-stdin")
    elif server_config_file is not None:
        args.extend(["--server-config-file", os.fspath(server_config_file)])
    elif server_config is not None:
        args.extend(["--server-config", server_config])
    return args
