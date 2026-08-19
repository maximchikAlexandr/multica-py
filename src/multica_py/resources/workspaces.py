from __future__ import annotations

from typing import TYPE_CHECKING

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.agents import Agent
from multica_py.entities.autopilots import Autopilot
from multica_py.entities.issues import Issue
from multica_py.entities.labels import Label
from multica_py.entities.projects import Project
from multica_py.entities.skills import Skill
from multica_py.entities.squads import Squad
from multica_py.entities.workspaces import Workspace, WorkspaceMember
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import IssueListFilter
from multica_py.models.plugins import Plugin
from multica_py.models.properties import PropertyDefinition
from multica_py.models.relations import (
    OffsetPage,
    RelationMetadata,
    _RelationLoad,
)
from multica_py.models.system import RepositoryRecord, RuntimeDefinition
from multica_py.models.workspaces import McpServer
from multica_py.resources._base import BaseResource, _page_items
from multica_py.resources.workspace_mcp import WorkspaceMcpResource

if TYPE_CHECKING:
    from multica_py.client import MulticaClient

__all__ = ["Workspace", "WorkspaceMember", "WorkspaceResource"]


class WorkspaceResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.mcp = WorkspaceMcpResource(transport, config)

    def _set_client(self, client: MulticaClient) -> None:
        super()._set_client(client)
        self.mcp._set_client(client)

    def _mcp_servers_relation_command(self) -> Command[tuple[McpServer, ...]]:
        return self._bound_client().workspaces.mcp.list_command()._map(_page_items)

    def _plugins_relation_command(self) -> Command[tuple[Plugin, ...]]:
        return self._bound_client().plugins.list_command()._map(lambda page: tuple(page.items))

    def _properties_relation_command(self) -> Command[tuple[PropertyDefinition, ...]]:
        return self._bound_client().properties.list_command()._map(lambda page: tuple(page.items))

    def _members_relation_command(self, workspace_id: str) -> Command[tuple[WorkspaceMember, ...]]:
        return (
            self._bound_client()
            .workspaces.members_command(workspace_id)
            ._map(lambda page: tuple(page.items))
        )

    def _agents_relation_command(self) -> Command[tuple[Agent, ...]]:
        return self._bound_client().agents.list_command()._map(lambda page: tuple(page.items))

    def _skills_relation_command(self) -> Command[tuple[Skill, ...]]:
        return self._bound_client().skills.list_command()._map(lambda page: tuple(page.items))

    def _projects_relation_command(self) -> Command[tuple[Project, ...]]:
        return self._bound_client().projects.list_command()._map(lambda page: tuple(page.items))

    def _labels_relation_command(self) -> Command[tuple[Label, ...]]:
        return self._bound_client().labels.list_command()._map(lambda page: tuple(page.items))

    def _repositories_relation_command(self) -> Command[tuple[RepositoryRecord, ...]]:
        return self._bound_client().repositories.list_command()._map(lambda page: tuple(page.items))

    def _runtimes_relation_command(self) -> Command[tuple[RuntimeDefinition, ...]]:
        return self._bound_client().runtimes.list_command()._map(lambda page: tuple(page.items))

    def _squads_relation_command(self) -> Command[tuple[Squad, ...]]:
        return self._bound_client().squads.list_command()._map(lambda page: tuple(page.items))

    def _issues_page(
        self, assignee_id: str | None, limit: int | None, offset: int
    ) -> OffsetPage[Issue]:
        return self._bound_client().issues._offset_page(
            IssueListFilter(assignee_id=assignee_id, limit=limit, offset=offset)
        )

    def _issues_page_command(
        self, assignee_id: str | None, limit: int | None, offset: int
    ) -> Command[OffsetPage[Issue]]:
        return self._bound_client().issues._offset_page_command(
            IssueListFilter(assignee_id=assignee_id, limit=limit, offset=offset)
        )

    def _autopilots_relation_command(self) -> Command[_RelationLoad[Autopilot]]:
        return (
            self._bound_client()
            .autopilots.list_command()
            ._map(lambda page: _RelationLoad(page.autopilots, RelationMetadata(total=page.total)))
        )

    def list_command(self, *, options: OperationOptions | None = None) -> Command[Page[Workspace]]:
        return self._decoded_page_command(("workspace", "list"), Workspace, options=options)._map(
            lambda page: Page(
                items=tuple(item._with_client(self._client) for item in page.items),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(self, *, options: OperationOptions | None = None) -> Page[Workspace]:
        return self.list_command(options=options).run()

    def get_command(
        self, workspace_id: str, *, options: OperationOptions | None = None
    ) -> Command[Workspace]:
        validate_nonblank(workspace_id)
        return self._decoded_command(
            ("workspace", "get", workspace_id), Workspace, options=options
        )._map(lambda workspace: workspace._with_client(self._client))

    def get(self, workspace_id: str, *, options: OperationOptions | None = None) -> Workspace:
        return self.get_command(workspace_id, options=options).run()

    def members_command(
        self, workspace_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[WorkspaceMember]]:
        return self._decoded_page_command(
            ("workspace", "member", "list", workspace_id), WorkspaceMember, options=options
        )._map(
            lambda page: Page(
                items=tuple(item._with_client(self._client) for item in page.items),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def members(
        self, workspace_id: str, *, options: OperationOptions | None = None
    ) -> Page[WorkspaceMember]:
        return self.members_command(workspace_id, options=options).run()

    def switch_command(
        self, workspace_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("workspace", "switch", workspace_id), options=options)

    def switch(
        self, workspace_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.switch_command(workspace_id, options=options).run()

    def watch_command(
        self, workspace_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("workspace", "watch", workspace_id), options=options)

    def watch(
        self, workspace_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.watch_command(workspace_id, options=options).run()

    def unwatch_command(
        self, workspace_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("workspace", "unwatch", workspace_id), options=options)

    def unwatch(
        self, workspace_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.unwatch_command(workspace_id, options=options).run()
