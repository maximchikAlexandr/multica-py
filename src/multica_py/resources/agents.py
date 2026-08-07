from __future__ import annotations

import datetime
import pathlib
from typing import cast, overload

import msgspec

from multica_py._generated.approved_sdk import AGENT_AVATAR_BINDING, validate_nonblank
from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models._bound import _BoundEntity
from multica_py.models.agents import (
    AgentCreateRequest,
    AgentSkill,
    AgentTask,
    AgentUpdateRequest,
)
from multica_py.models.issues import IssueSummary
from multica_py.models.relations import LazyCollection, OffsetLazyCollection, OffsetPage
from multica_py.resources._base import BaseResource, _resolve_request
from multica_py.resources.agent_skills import AgentSkillResource
from multica_py.sentinels import Unset, UnsetType

__all__ = ["Agent", "AgentResource"]


class Agent(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    description: str | None = None
    skill_refs: tuple[AgentSkill, ...] = msgspec.field(default_factory=tuple, name="skills")
    archived_at: datetime.datetime | None = None

    _skills: LazyCollection[AgentSkill] | None = msgspec.field(default=None, name="_skills")
    _tasks: LazyCollection[AgentTask] | None = msgspec.field(default=None, name="_tasks")
    _issues: OffsetLazyCollection[IssueSummary] | None = msgspec.field(default=None, name="_issues")

    _PUBLIC_FIELDS = ("id", "name", "description", "skill_refs", "archived_at")

    @property
    def skills(self) -> LazyCollection[AgentSkill]:
        if self._skills is None:
            client = self._require_client(
                entity_type="Agent", entity_id=self.id, relation_name="skills"
            )
            aid = self.id
            skills = client.agents.skills
            self._set_runtime(
                "_skills",
                LazyCollection(
                    lambda: skills.list(aid),
                    command_loader=lambda: skills.list_command(aid),
                ),
            )
        return self._skills  # type: ignore[return-value]

    @property
    def tasks(self) -> LazyCollection[AgentTask]:
        if self._tasks is None:
            client = self._require_client(
                entity_type="Agent", entity_id=self.id, relation_name="tasks"
            )
            aid = self.id
            agents = client.agents
            self._set_runtime(
                "_tasks",
                LazyCollection(
                    lambda: agents.tasks(aid),
                    command_loader=lambda: agents.tasks_command(aid),
                ),
            )
        return self._tasks  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._require_client(
                entity_type="Agent", entity_id=self.id, relation_name="issues"
            )
            aid = self.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:
                from multica_py.models.issues import IssueListFilter
                from multica_py.resources.issues import _issue_summary_offset_page

                return _issue_summary_offset_page(
                    client.issues,
                    IssueListFilter(assignee_id=aid, limit=limit, offset=offset),
                )

            def page_command_loader(
                limit: int | None, offset: int
            ) -> Command[OffsetPage[IssueSummary]]:
                from multica_py.models.issues import IssueListFilter
                from multica_py.resources.issues import _issue_summary_offset_page_command

                return _issue_summary_offset_page_command(
                    client.issues,
                    IssueListFilter(assignee_id=aid, limit=limit, offset=offset),
                )

            self._set_runtime(
                "_issues",
                OffsetLazyCollection(
                    page_loader,
                    default_limit=50,
                    page_command_loader=page_command_loader,
                ),
            )
        return self._issues  # type: ignore[return-value]

    def _invalidate_skills(self) -> None:
        if self._skills is not None:
            self._skills.invalidate()

    def set_skills(self, skill_ids: tuple[str, ...]) -> None:
        """Set the agent's assigned skills and invalidate cached skills cache."""
        self.set_skills_command(skill_ids).run()

    def set_skills_command(self, skill_ids: tuple[str, ...]) -> Command[None]:
        """Build a lazy command to set skills and invalidate the cache on success."""
        client = self._require_client(
            entity_type="Agent", entity_id=self.id, relation_name="set_skills"
        )
        return client.agents.skills.set_command(self.id, skill_ids)._map(
            lambda result: self._invalidate_skills()
        )


class AgentResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.skills = AgentSkillResource(transport, config)

    def list_command(self) -> Command[tuple[Agent, ...]]:
        return self._decoded_list_command(("agent", "list"), Agent)._map(
            lambda items: tuple(agent._with_client(self._client) for agent in items)
        )

    def list(self) -> tuple[Agent, ...]:
        return self.list_command().run()

    def get_command(self, agent_id: str) -> Command[Agent]:
        validate_nonblank(agent_id)
        return self._decoded_command(("agent", "get", agent_id), Agent)._map(
            lambda agent: agent._with_client(self._client)
        )

    def get(self, agent_id: str) -> Agent:
        return self.get_command(agent_id).run()

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

        return self._decoded_command(tuple(args), Agent)._map(
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
        ).run()

    @overload
    def create_command(self, request: AgentCreateRequest, /) -> Command[Agent]: ...
    @overload
    def create_command(
        self,
        *,
        name: str,
        description: str | None = None,
        runtime_id: str | None = None,
        model: str | None = None,
    ) -> Command[Agent]: ...

    def create_command(  # type: ignore[misc]
        self, request: AgentCreateRequest | None = None, /, **kwargs: object
    ) -> Command[Agent]:
        req = _resolve_request(request, kwargs, AgentCreateRequest)
        validate_nonblank(req.name)
        args = ["agent", "create", "--name", req.name]
        if req.description is not None:
            args.extend(["--description", req.description])
        if req.runtime_id is not None:
            args.extend(["--runtime-id", req.runtime_id])
        if req.model is not None:
            args.extend(["--model", req.model])
        return self._decoded_command(tuple(args), Agent)._map(
            lambda agent: agent._with_client(self._client)
        )

    @overload
    def create(self, request: AgentCreateRequest, /) -> Agent: ...
    @overload
    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        runtime_id: str | None = None,
        model: str | None = None,
    ) -> Agent: ...

    def create(self, request: AgentCreateRequest | None = None, /, **kwargs: object) -> Agent:  # type: ignore[misc]
        return self.create_command(cast("AgentCreateRequest", request), **kwargs).run()

    @overload
    def update_command(self, agent_id: str, request: AgentUpdateRequest, /) -> Command[Agent]: ...
    @overload
    def update_command(
        self, agent_id: str, *, name: str | None = None, description: str | None = None
    ) -> Command[Agent]: ...

    def update_command(  # type: ignore[misc]
        self, agent_id: str, request: AgentUpdateRequest | None = None, /, **kwargs: object
    ) -> Command[Agent]:
        validate_nonblank(agent_id)
        req = _resolve_request(request, kwargs, AgentUpdateRequest)
        args = ["agent", "update", agent_id]
        if req.name is not None:
            args.extend(["--name", req.name])
        if req.description is not None:
            args.extend(["--description", req.description])
        return self._decoded_command(tuple(args), Agent)._map(
            lambda agent: agent._with_client(self._client)
        )

    @overload
    def update(self, agent_id: str, request: AgentUpdateRequest, /) -> Agent: ...
    @overload
    def update(
        self, agent_id: str, *, name: str | None = None, description: str | None = None
    ) -> Agent: ...

    def update(  # type: ignore[misc]
        self, agent_id: str, request: AgentUpdateRequest | None = None, /, **kwargs: object
    ) -> Agent:
        return self.update_command(agent_id, cast("AgentUpdateRequest", request), **kwargs).run()

    def archive_command(self, agent_id: str) -> Command[None]:
        validate_nonblank(agent_id)
        return self._none_command(("agent", "archive", agent_id))

    def archive(self, agent_id: str) -> None:
        self.archive_command(agent_id).run()

    def restore_command(self, agent_id: str) -> Command[None]:
        validate_nonblank(agent_id)
        return self._none_command(("agent", "restore", agent_id))

    def restore(self, agent_id: str) -> None:
        self.restore_command(agent_id).run()

    def tasks_command(self, agent_id: str) -> Command[tuple[AgentTask, ...]]:
        validate_nonblank(agent_id)
        return self._decoded_list_command(("agent", "tasks", agent_id), AgentTask)

    def tasks(self, agent_id: str) -> tuple[AgentTask, ...]:
        return self.tasks_command(agent_id).run()

    def avatar_command(self, agent_id: str, file: pathlib.Path) -> Command[None]:
        _ = AGENT_AVATAR_BINDING
        validate_nonblank(agent_id)
        path = file.resolve()
        if not path.is_file():
            raise ValueError(f"file must be an existing local file: {file}")
        return self._none_command(("agent", "avatar", agent_id, "--file", str(path)))

    def avatar(self, agent_id: str, file: pathlib.Path) -> None:
        self.avatar_command(agent_id, file).run()
