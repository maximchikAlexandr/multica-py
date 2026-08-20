from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command, _Step
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.models.common import Page
from multica_py.models.workspaces import McpServer
from multica_py.resources._base import BaseResource
from multica_py.resources.workspace_mcp import WorkspaceMcpResource

__all__ = ["AgentMcpResource"]


class AgentMcpResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list_command(
        self, agent_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[McpServer]]:
        validate_nonblank(agent_id)
        return self._mcp_page_command(("agent", "mcp", "list", agent_id), options=options)

    def list(self, agent_id: str, *, options: OperationOptions | None = None) -> Page[McpServer]:
        return self.list_command(agent_id, options=options).run()

    def add_command(
        self,
        agent_id: str,
        server_id: str,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Page[McpServer]]:
        validate_nonblank(agent_id)
        validate_nonblank(server_id)
        return self._mcp_page_command(("agent", "mcp", "add", agent_id, server_id), options=options)

    def add(
        self,
        agent_id: str,
        server_id: str,
        *,
        options: OperationOptions | None = None,
    ) -> Page[McpServer]:
        return self.add_command(agent_id, server_id, options=options).run()

    def enable_command(
        self,
        agent_id: str,
        server_id: str,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Page[McpServer]]:
        validate_nonblank(agent_id)
        validate_nonblank(server_id)
        return self._mcp_page_command(
            ("agent", "mcp", "enable", agent_id, server_id), options=options
        )

    def enable(
        self,
        agent_id: str,
        server_id: str,
        *,
        options: OperationOptions | None = None,
    ) -> Page[McpServer]:
        return self.enable_command(agent_id, server_id, options=options).run()

    def disable_command(
        self,
        agent_id: str,
        server_id: str,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Page[McpServer]]:
        validate_nonblank(agent_id)
        validate_nonblank(server_id)
        return self._mcp_page_command(
            ("agent", "mcp", "disable", agent_id, server_id), options=options
        )

    def disable(
        self,
        agent_id: str,
        server_id: str,
        *,
        options: OperationOptions | None = None,
    ) -> Page[McpServer]:
        return self.disable_command(agent_id, server_id, options=options).run()

    def remove_command(
        self,
        agent_id: str,
        server_id: str,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Page[McpServer]]:
        validate_nonblank(agent_id)
        validate_nonblank(server_id)
        return self._mcp_page_command(
            ("agent", "mcp", "remove", agent_id, server_id), options=options
        )

    def remove(
        self,
        agent_id: str,
        server_id: str,
        *,
        options: OperationOptions | None = None,
    ) -> Page[McpServer]:
        return self.remove_command(agent_id, server_id, options=options).run()

    def _mcp_page_command(
        self, args: tuple[str, ...], *, options: OperationOptions | None
    ) -> Command[Page[McpServer]]:
        plan_args = (*args, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            return WorkspaceMcpResource._decode_mcp_servers(stdout, command)

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("Page[McpServer]", results[0]),
            options=options,
        )
