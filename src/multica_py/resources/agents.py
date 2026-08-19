from __future__ import annotations

import pathlib
from collections.abc import Callable
from typing import TYPE_CHECKING

import msgspec

from multica_py._generated.approved_sdk import AGENT_AVATAR_BINDING, validate_nonblank
from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.agents import Agent
from multica_py.models.agents import AgentSkill, AgentTask
from multica_py.models.common import ActionResult, Page
from multica_py.models.workspaces import McpServer
from multica_py.resources._base import BaseResource, _page_items, _validate_optional_string
from multica_py.resources.agent_mcp import AgentMcpResource
from multica_py.resources.agent_skills import AgentSkillResource
from multica_py.sentinels import Unset, UnsetType

if TYPE_CHECKING:
    from multica_py.client import MulticaClient

__all__ = ["Agent", "AgentResource"]


class AgentResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.skills = AgentSkillResource(transport, config)
        self.mcp = AgentMcpResource(transport, config)

    def _set_client(self, client: MulticaClient) -> None:
        super()._set_client(client)
        self.skills._set_client(client)
        self.mcp._set_client(client)

    def _mcp_servers_relation_command(self, agent_id: str) -> Command[tuple[McpServer, ...]]:
        return self.mcp.list_command(agent_id)._map(_page_items)

    def _skills_relation_command(self, agent_id: str) -> Command[tuple[AgentSkill, ...]]:
        return self.skills.list_command(agent_id)._map(lambda page: tuple(page.items))

    def _tasks_relation_command(self, agent_id: str) -> Command[tuple[AgentTask, ...]]:
        return self.tasks_command(agent_id)._map(lambda page: tuple(page.items))

    def _set_skills_command(
        self,
        agent_id: str,
        skill_ids: tuple[str, ...],
        *,
        invalidate: Callable[[ActionResult[None]], ActionResult[None]],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        return self.skills.set_command(agent_id, skill_ids, options=options)._map(invalidate)

    def list_command(self, *, options: OperationOptions | None = None) -> Command[Page[Agent]]:
        return self._decoded_page_command(("agent", "list"), Agent, options=options)._map(
            lambda page: Page(
                items=tuple(agent._with_client(self._client) for agent in page.items),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(self, *, options: OperationOptions | None = None) -> Page[Agent]:
        return self.list_command(options=options).run()

    def get_command(
        self, agent_id: str, *, options: OperationOptions | None = None
    ) -> Command[Agent]:
        validate_nonblank(agent_id)
        return self._decoded_command(("agent", "get", agent_id), Agent, options=options)._map(
            lambda agent: agent._with_client(self._client)
        )

    def get(self, agent_id: str, *, options: OperationOptions | None = None) -> Agent:
        return self.get_command(agent_id, options=options).run()

    def copy_command(
        self,
        source_agent_id: str,
        *,
        name: str | UnsetType = Unset,
        runtime_id: str | UnsetType = Unset,
        description: str | UnsetType = Unset,
        instructions: str | UnsetType = Unset,
        model: str | UnsetType = Unset,
        thinking_level: str | UnsetType = Unset,
        service_tier: str | UnsetType = Unset,
        custom_args: tuple[str, ...] | UnsetType = Unset,
        max_concurrent_tasks: int | UnsetType = Unset,
        permission_mode: str | UnsetType = Unset,
        public_to_workspace: bool | UnsetType = Unset,
        public_to_member_ids: tuple[str, ...] | UnsetType = Unset,
        copy_skills: bool = True,
        options: OperationOptions | None = None,
    ) -> Command[Agent]:
        validate_nonblank(source_agent_id)
        if name is not Unset:
            validate_nonblank(name)

        for field_name, value in (
            ("runtime_id", runtime_id),
            ("description", description),
            ("instructions", instructions),
            ("model", model),
            ("thinking_level", thinking_level),
            ("service_tier", service_tier),
            ("permission_mode", permission_mode),
        ):
            if value is not Unset and not isinstance(value, str):
                raise ValueError(f"{field_name} must be a string")

        if custom_args is not Unset:
            if not isinstance(custom_args, tuple) or not all(
                isinstance(value, str) for value in custom_args
            ):
                raise ValueError("custom_args must be a tuple of strings")

        if max_concurrent_tasks is not Unset and (
            not isinstance(max_concurrent_tasks, int)
            or isinstance(max_concurrent_tasks, bool)
            or not 1 <= max_concurrent_tasks <= 50
        ):
            raise ValueError("max_concurrent_tasks must be between 1 and 50")

        if public_to_workspace is not Unset and not isinstance(public_to_workspace, bool):
            raise ValueError("public_to_workspace must be a boolean")

        if public_to_member_ids is not Unset:
            if not isinstance(public_to_member_ids, tuple) or not public_to_member_ids:
                raise ValueError("public_to_member_ids must be a non-empty tuple")
            for member_id in public_to_member_ids:
                validate_nonblank(member_id)

        if not isinstance(copy_skills, bool):
            raise ValueError("copy_skills must be a boolean")

        args = ["agent", "copy", source_agent_id]
        for flag, value in (
            ("--name", name),
            ("--runtime-id", runtime_id),
            ("--description", description),
            ("--instructions", instructions),
            ("--model", model),
            ("--thinking-level", thinking_level),
            ("--service-tier", service_tier),
        ):
            if value is not Unset:
                args.extend((flag, value))
            elif flag == "--model" and runtime_id is not Unset:
                args.extend((flag, ""))
        if custom_args is not Unset:
            args.extend(("--custom-args", msgspec.json.encode(custom_args).decode()))
        if max_concurrent_tasks is not Unset:
            args.extend(("--max-concurrent-tasks", str(max_concurrent_tasks)))
        if permission_mode is not Unset:
            args.extend(("--permission-mode", permission_mode))
        if public_to_workspace is not Unset:
            if public_to_workspace:
                args.append("--public-to-workspace")
            else:
                args.append("--public-to-workspace=false")
        if public_to_member_ids is not Unset:
            for member_id in public_to_member_ids:
                args.extend(("--public-to-member", member_id))
        if not copy_skills:
            args.append("--no-skills")

        return self._decoded_command(tuple(args), Agent, options=options)._map(
            lambda agent: agent._with_client(self._client)
        )

    def copy(
        self,
        source_agent_id: str,
        *,
        name: str | UnsetType = Unset,
        runtime_id: str | UnsetType = Unset,
        description: str | UnsetType = Unset,
        instructions: str | UnsetType = Unset,
        model: str | UnsetType = Unset,
        thinking_level: str | UnsetType = Unset,
        service_tier: str | UnsetType = Unset,
        custom_args: tuple[str, ...] | UnsetType = Unset,
        max_concurrent_tasks: int | UnsetType = Unset,
        permission_mode: str | UnsetType = Unset,
        public_to_workspace: bool | UnsetType = Unset,
        public_to_member_ids: tuple[str, ...] | UnsetType = Unset,
        copy_skills: bool = True,
        options: OperationOptions | None = None,
    ) -> Agent:
        return self.copy_command(
            source_agent_id,
            name=name,
            runtime_id=runtime_id,
            description=description,
            instructions=instructions,
            model=model,
            thinking_level=thinking_level,
            service_tier=service_tier,
            custom_args=custom_args,
            max_concurrent_tasks=max_concurrent_tasks,
            permission_mode=permission_mode,
            public_to_workspace=public_to_workspace,
            public_to_member_ids=public_to_member_ids,
            copy_skills=copy_skills,
            options=options,
        ).run()

    def create_command(
        self,
        *,
        name: str,
        description: str | None = None,
        runtime_id: str | None = None,
        model: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Agent]:
        validate_nonblank(name)
        _validate_optional_string(description, "description")
        _validate_optional_string(runtime_id, "runtime_id")
        _validate_optional_string(model, "model")
        args = ["agent", "create", "--name", name]
        if description is not None:
            args.extend(["--description", description])
        if runtime_id is not None:
            args.extend(["--runtime-id", runtime_id])
        if model is not None:
            args.extend(["--model", model])
        return self._decoded_command(tuple(args), Agent, options=options)._map(
            lambda agent: agent._with_client(self._client)
        )

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        runtime_id: str | None = None,
        model: str | None = None,
        options: OperationOptions | None = None,
    ) -> Agent:
        return self.create_command(
            name=name,
            description=description,
            runtime_id=runtime_id,
            model=model,
            options=options,
        ).run()

    def update_command(
        self,
        agent_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Agent]:
        validate_nonblank(agent_id)
        if name is None:
            raise TypeError("name must be non-null")
        _validate_optional_string(name, "name")
        _validate_optional_string(description, "description")
        if name is Unset and description is Unset:
            return self._decoded_command(("agent", "get", agent_id), Agent, options=options)._map(
                lambda agent: agent._with_client(self._client)
            )
        args = ["agent", "update", agent_id]
        if name is not Unset:
            args.extend(["--name", name])
        if description is not Unset:
            args.extend(["--description", "" if description is None else description])
        return self._decoded_command(tuple(args), Agent, options=options)._map(
            lambda agent: agent._with_client(self._client)
        )

    def update(
        self,
        agent_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Agent:
        return self.update_command(
            agent_id, name=name, description=description, options=options
        ).run()

    def archive_command(
        self, agent_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(agent_id)
        return self._action_command(("agent", "archive", agent_id), options=options)

    def archive(
        self, agent_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.archive_command(agent_id, options=options).run()

    def restore_command(
        self, agent_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(agent_id)
        return self._action_command(("agent", "restore", agent_id), options=options)

    def restore(
        self, agent_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.restore_command(agent_id, options=options).run()

    def tasks_command(
        self, agent_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[AgentTask]]:
        validate_nonblank(agent_id)
        return self._decoded_page_command(("agent", "tasks", agent_id), AgentTask, options=options)

    def tasks(self, agent_id: str, *, options: OperationOptions | None = None) -> Page[AgentTask]:
        return self.tasks_command(agent_id, options=options).run()

    def avatar_command(
        self, agent_id: str, file: pathlib.Path, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        _ = AGENT_AVATAR_BINDING
        validate_nonblank(agent_id)
        path = file.resolve()
        if not path.is_file():
            raise ValueError(f"file must be an existing local file: {file}")
        return self._action_command(
            ("agent", "avatar", agent_id, "--file", str(path)), options=options
        )

    def avatar(
        self, agent_id: str, file: pathlib.Path, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.avatar_command(agent_id, file, options=options).run()
