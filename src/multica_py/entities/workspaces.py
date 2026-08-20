from __future__ import annotations

import os
from typing import TYPE_CHECKING, TypeVar

import msgspec

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.entities._base import _BoundEntity
from multica_py.entities.agents import Agent
from multica_py.entities.autopilots import Autopilot
from multica_py.entities.issues import Issue
from multica_py.entities.labels import Label
from multica_py.entities.projects import Project
from multica_py.entities.skills import Skill
from multica_py.entities.squads import Squad
from multica_py.models.autopilots import AutopilotListPage
from multica_py.models.common import ActionResult, Page
from multica_py.models.plugins import Plugin
from multica_py.models.properties import PropertyDefinition
from multica_py.models.relations import (
    LazyCollection,
    OffsetLazyCollection,
    OffsetPage,
    RelationMetadata,
    _RelationLoad,
)
from multica_py.models.system import RepositoryRecord, RuntimeDefinition
from multica_py.models.workspaces import McpServer
from multica_py.sentinels import Unset, UnsetType

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


S = TypeVar("S")


def _page_items(value: Page[S] | tuple[S, ...]) -> tuple[S, ...]:
    return value.items if isinstance(value, Page) else value


class WorkspaceMember(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    role: str | None = None
    user_id: str | None = None
    email: str | None = None

    _issues: OffsetLazyCollection[Issue] | None = msgspec.field(default=None, name="_issues")

    @property
    def issues(self) -> OffsetLazyCollection[Issue]:
        if self._issues is None:
            client = self._require_client(
                entity_type="WorkspaceMember", entity_id=self.id, relation_name="issues"
            )
            mid = self.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[Issue]:
                return client.workspaces._issues_page(mid, limit, offset)

            def page_command_loader(limit: int | None, offset: int) -> Command[OffsetPage[Issue]]:
                return client.workspaces._issues_page_command(mid, limit, offset)

            self._set_runtime(
                "_issues",
                OffsetLazyCollection(
                    page_loader,
                    default_limit=50,
                    page_command_loader=page_command_loader,
                ),
            )
        return self._issues  # type: ignore[return-value]


class Workspace(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    description: str | None = None

    _members: LazyCollection[WorkspaceMember] | None = msgspec.field(default=None, name="_members")
    _agents: LazyCollection[Agent] | None = msgspec.field(default=None, name="_agents")
    _skills: LazyCollection[Skill] | None = msgspec.field(default=None, name="_skills")
    _projects: LazyCollection[Project] | None = msgspec.field(default=None, name="_projects")
    _labels: LazyCollection[Label] | None = msgspec.field(default=None, name="_labels")
    _repositories: LazyCollection[RepositoryRecord] | None = msgspec.field(
        default=None, name="_repositories"
    )
    _runtimes: LazyCollection[RuntimeDefinition] | None = msgspec.field(
        default=None, name="_runtimes"
    )
    _squads: LazyCollection[Squad] | None = msgspec.field(default=None, name="_squads")
    _issues: OffsetLazyCollection[Issue] | None = msgspec.field(default=None, name="_issues")
    _autopilots: LazyCollection[Autopilot] | None = msgspec.field(default=None, name="_autopilots")
    _mcp_servers: LazyCollection[McpServer] | None = msgspec.field(
        default=None, name="_mcp_servers"
    )
    _plugins: LazyCollection[Plugin] | None = msgspec.field(default=None, name="_plugins")
    _properties: LazyCollection[PropertyDefinition] | None = msgspec.field(
        default=None, name="_properties"
    )

    def _check_client(self, relation_name: str) -> MulticaClient:
        return self._require_client(
            entity_type="Workspace", entity_id=self.id, relation_name=relation_name
        ).with_workspace(self.id)

    @property
    def members(self) -> LazyCollection[WorkspaceMember]:
        if self._members is None:
            client = self._check_client("members")
            wid = self.id

            def members_command_loader() -> Command[tuple[WorkspaceMember, ...]]:
                return client.workspaces._members_relation_command(wid)

            self._set_runtime(
                "_members",
                LazyCollection[WorkspaceMember](
                    lambda: _page_items(client.workspaces.members(wid)),
                    command_loader=members_command_loader,
                ),
            )
        return self._members  # type: ignore[return-value]

    @property
    def agents(self) -> LazyCollection[Agent]:
        if self._agents is None:
            client = self._check_client("agents")

            self._set_runtime(
                "_agents",
                LazyCollection[Agent](
                    lambda: _page_items(client.agents.list()),
                    command_loader=client.workspaces._agents_relation_command,
                ),
            )
        return self._agents  # type: ignore[return-value]

    @property
    def skills(self) -> LazyCollection[Skill]:
        if self._skills is None:
            client = self._check_client("skills")

            self._set_runtime(
                "_skills",
                LazyCollection[Skill](
                    lambda: _page_items(client.skills.list()),
                    command_loader=client.workspaces._skills_relation_command,
                ),
            )
        return self._skills  # type: ignore[return-value]

    @property
    def projects(self) -> LazyCollection[Project]:
        if self._projects is None:
            client = self._check_client("projects")
            self._set_runtime(
                "_projects",
                LazyCollection[Project](
                    lambda: _page_items(client.projects.list()),
                    command_loader=client.workspaces._projects_relation_command,
                ),
            )
        return self._projects  # type: ignore[return-value]

    @property
    def labels(self) -> LazyCollection[Label]:
        if self._labels is None:
            client = self._check_client("labels")

            self._set_runtime(
                "_labels",
                LazyCollection[Label](
                    lambda: _page_items(client.labels.list()),
                    command_loader=client.workspaces._labels_relation_command,
                ),
            )
        return self._labels  # type: ignore[return-value]

    @property
    def repositories(self) -> LazyCollection[RepositoryRecord]:
        if self._repositories is None:
            client = self._check_client("repositories")

            self._set_runtime(
                "_repositories",
                LazyCollection[RepositoryRecord](
                    lambda: _page_items(client.repositories.list()),
                    command_loader=client.workspaces._repositories_relation_command,
                ),
            )
        return self._repositories  # type: ignore[return-value]

    @property
    def runtimes(self) -> LazyCollection[RuntimeDefinition]:
        if self._runtimes is None:
            client = self._check_client("runtimes")

            self._set_runtime(
                "_runtimes",
                LazyCollection[RuntimeDefinition](
                    lambda: _page_items(client.runtimes.list()),
                    command_loader=client.workspaces._runtimes_relation_command,
                ),
            )
        return self._runtimes  # type: ignore[return-value]

    @property
    def squads(self) -> LazyCollection[Squad]:
        if self._squads is None:
            client = self._check_client("squads")

            self._set_runtime(
                "_squads",
                LazyCollection[Squad](
                    lambda: _page_items(client.squads.list()),
                    command_loader=client.workspaces._squads_relation_command,
                ),
            )
        return self._squads  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[Issue]:
        if self._issues is None:
            client = self._check_client("issues")

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[Issue]:
                return client.workspaces._issues_page(None, limit, offset)

            def page_command_loader(limit: int | None, offset: int) -> Command[OffsetPage[Issue]]:
                return client.workspaces._issues_page_command(None, limit, offset)

            self._set_runtime(
                "_issues",
                OffsetLazyCollection(
                    page_loader,
                    default_limit=50,
                    page_command_loader=page_command_loader,
                ),
            )
        return self._issues  # type: ignore[return-value]

    @property
    def autopilots(self) -> LazyCollection[Autopilot]:
        if self._autopilots is None:
            client = self._check_client("autopilots")

            def loader() -> _RelationLoad[Autopilot]:
                page: AutopilotListPage[Autopilot] = client.autopilots.list()
                return _RelationLoad(
                    page.autopilots,
                    RelationMetadata(total=page.total),
                )

            _autopilots = LazyCollection(
                loader,
                metadata=RelationMetadata(total=None),
                command_loader=client.workspaces._autopilots_relation_command,
            )
            self._set_runtime("_autopilots", _autopilots)
        return self._autopilots  # type: ignore[return-value]

    @property
    def mcp_servers(self) -> LazyCollection[McpServer]:
        if self._mcp_servers is None:
            client = self._check_client("mcp_servers")

            self._set_runtime(
                "_mcp_servers",
                LazyCollection[McpServer](
                    lambda: _page_items(client.workspaces.mcp.list()),
                    command_loader=client.workspaces._mcp_servers_relation_command,
                ),
            )
        return self._mcp_servers  # type: ignore[return-value]

    def _invalidate_mcp_servers(self) -> None:
        if self._mcp_servers is not None:
            self._mcp_servers.invalidate()

    def add_mcp_server(
        self,
        server_name: str,
        *,
        server_config_file: str | os.PathLike[str] | None = None,
        server_config_stdin: bytes | None = None,
        server_config: str | None = None,
        options: OperationOptions | None = None,
    ) -> Page[McpServer]:
        return self.add_mcp_server_command(
            server_name,
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
            options=options,
        ).run()

    def add_mcp_server_command(
        self,
        server_name: str,
        *,
        server_config_file: str | os.PathLike[str] | None = None,
        server_config_stdin: bytes | None = None,
        server_config: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Page[McpServer]]:
        client = self._check_client("add_mcp_server")

        def invalidate(result: Page[McpServer]) -> Page[McpServer]:
            self._invalidate_mcp_servers()
            return result

        return client.workspaces._add_mcp_server_command(
            server_name,
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
            invalidate=invalidate,
            options=options,
        )

    def update_mcp_server(
        self,
        server_id: str,
        *,
        name: str | UnsetType = Unset,
        server_config_file: str | os.PathLike[str] | None = None,
        server_config_stdin: bytes | None = None,
        server_config: str | None = None,
        options: OperationOptions | None = None,
    ) -> Page[McpServer]:
        return self.update_mcp_server_command(
            server_id,
            name=name,
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
            options=options,
        ).run()

    def update_mcp_server_command(
        self,
        server_id: str,
        *,
        name: str | UnsetType = Unset,
        server_config_file: str | os.PathLike[str] | None = None,
        server_config_stdin: bytes | None = None,
        server_config: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Page[McpServer]]:
        client = self._check_client("update_mcp_server")

        def invalidate(result: Page[McpServer]) -> Page[McpServer]:
            self._invalidate_mcp_servers()
            return result

        return client.workspaces._update_mcp_server_command(
            server_id,
            name=name,
            server_config_file=server_config_file,
            server_config_stdin=server_config_stdin,
            server_config=server_config,
            invalidate=invalidate,
            options=options,
        )

    def remove_mcp_server(
        self, server_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.remove_mcp_server_command(server_id, options=options).run()

    def remove_mcp_server_command(
        self, server_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        client = self._check_client("remove_mcp_server")

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_mcp_servers()
            return result

        return client.workspaces._remove_mcp_server_command(
            server_id, invalidate=invalidate, options=options
        )

    @property
    def plugins(self) -> LazyCollection[Plugin]:
        if self._plugins is None:
            client = self._check_client("plugins")

            self._set_runtime(
                "_plugins",
                LazyCollection[Plugin](
                    lambda: _page_items(client.plugins.list()),
                    command_loader=client.workspaces._plugins_relation_command,
                ),
            )
        return self._plugins  # type: ignore[return-value]

    @property
    def properties(self) -> LazyCollection[PropertyDefinition]:
        if self._properties is None:
            client = self._check_client("properties")

            self._set_runtime(
                "_properties",
                LazyCollection[PropertyDefinition](
                    lambda: _page_items(client.properties.list()),
                    command_loader=client.workspaces._properties_relation_command,
                ),
            )
        return self._properties  # type: ignore[return-value]
