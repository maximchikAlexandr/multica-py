from __future__ import annotations

from typing import TYPE_CHECKING, cast

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models._bound import _BoundEntity
from multica_py.models.autopilots import AutopilotListPage
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import IssueListFilter
from multica_py.models.relations import (
    LazyCollection,
    OffsetLazyCollection,
    OffsetPage,
    RelationMetadata,
    _RelationLoad,
)
from multica_py.models.system import RepositoryRecord, RuntimeDefinition
from multica_py.resources._base import BaseResource, _page_items
from multica_py.resources.agents import Agent
from multica_py.resources.autopilots import Autopilot
from multica_py.resources.issues import (
    Issue,
    _issue_offset_page,
    _issue_offset_page_command,
)
from multica_py.resources.labels import Label
from multica_py.resources.projects import Project
from multica_py.resources.skills import Skill
from multica_py.resources.squads import Squad

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


def _workspace_page_issues(
    client: MulticaClient, limit: int | None, offset: int
) -> OffsetPage[Issue]:

    flt = IssueListFilter(
        limit=limit,
        offset=offset,
    )
    return _issue_offset_page(client.issues, flt)


def _workspace_issues_page_command(
    client: MulticaClient,
    assignee_id: str | None,
    limit: int | None,
    offset: int,
) -> Command[OffsetPage[Issue]]:
    return _issue_offset_page_command(
        client.issues,
        IssueListFilter(assignee_id=assignee_id, limit=limit, offset=offset),
    )


def _workspace_autopilots_command(
    client: MulticaClient,
) -> Command[_RelationLoad[Autopilot]]:
    command = client.autopilots.list_command()

    def finalize(page: AutopilotListPage[Autopilot]) -> _RelationLoad[Autopilot]:
        return _RelationLoad(page.autopilots, RelationMetadata(total=page.total))

    return command._map(finalize)


class WorkspaceMember(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    role: str | None = None
    user_id: str | None = None
    email: str | None = None

    _issues: OffsetLazyCollection[Issue] | None = msgspec.field(default=None, name="_issues")

    _PUBLIC_FIELDS = ("id", "name", "role", "user_id", "email")

    @property
    def issues(self) -> OffsetLazyCollection[Issue]:
        if self._issues is None:
            client = self._require_client(
                entity_type="WorkspaceMember", entity_id=self.id, relation_name="issues"
            )
            mid = self.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[Issue]:

                flt = IssueListFilter(
                    assignee_id=mid,
                    limit=limit,
                    offset=offset,
                )
                return _issue_offset_page(client.issues, flt)

            self._set_runtime(
                "_issues",
                OffsetLazyCollection(
                    page_loader,
                    default_limit=50,
                    page_command_loader=lambda limit, offset: _workspace_issues_page_command(
                        client, mid, limit, offset
                    ),
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

    _PUBLIC_FIELDS = ("id", "name", "description")

    def _check_client(self, relation_name: str) -> MulticaClient:
        return self._require_client(
            entity_type="Workspace", entity_id=self.id, relation_name=relation_name
        ).with_workspace(self.id)

    @property
    def members(self) -> LazyCollection[WorkspaceMember]:
        if self._members is None:
            client = self._check_client("members")
            wid = self.id
            self._set_runtime(
                "_members",
                LazyCollection[WorkspaceMember](
                    lambda: client.workspaces.members(wid).items,  # type: ignore[misc]
                    command_loader=lambda: cast(  # type: ignore[misc]
                        "Command[tuple[WorkspaceMember, ...]]",
                        client.workspaces.members_command(wid)._map(_page_items),
                    ),
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
                    lambda: client.agents.list().items,  # type: ignore[misc]
                    command_loader=lambda: cast(  # type: ignore[misc]
                        "Command[tuple[Agent, ...]]",
                        client.agents.list_command()._map(_page_items),
                    ),
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
                    lambda: client.skills.list().items,  # type: ignore[misc]
                    command_loader=lambda: cast(  # type: ignore[misc]
                        "Command[tuple[Skill, ...]]",
                        client.skills.list_command()._map(_page_items),
                    ),
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
                    lambda: client.projects.list().items,  # type: ignore[misc]
                    command_loader=lambda: cast(  # type: ignore[misc]
                        "Command[tuple[Project, ...]]",
                        client.projects.list_command()._map(_page_items),
                    ),
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
                    lambda: client.labels.list().items,  # type: ignore[misc]
                    command_loader=lambda: cast(  # type: ignore[misc]
                        "Command[tuple[Label, ...]]",
                        client.labels.list_command()._map(_page_items),
                    ),
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
                    lambda: client.repositories.list().items,  # type: ignore[misc]
                    command_loader=lambda: cast(  # type: ignore[misc]
                        "Command[tuple[RepositoryRecord, ...]]",
                        client.repositories.list_command()._map(_page_items),
                    ),
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
                    lambda: client.runtimes.list().items,  # type: ignore[misc]
                    command_loader=lambda: cast(  # type: ignore[misc]
                        "Command[tuple[RuntimeDefinition, ...]]",
                        client.runtimes.list_command()._map(_page_items),
                    ),
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
                    lambda: client.squads.list().items,  # type: ignore[misc]
                    command_loader=lambda: cast(  # type: ignore[misc]
                        "Command[tuple[Squad, ...]]",
                        client.squads.list_command()._map(_page_items),
                    ),
                ),
            )
        return self._squads  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[Issue]:
        if self._issues is None:
            client = self._check_client("issues")

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[Issue]:
                return _workspace_page_issues(client, limit, offset)

            self._set_runtime(
                "_issues",
                OffsetLazyCollection(
                    page_loader,
                    default_limit=50,
                    page_command_loader=lambda limit, offset: _workspace_issues_page_command(
                        client, None, limit, offset
                    ),
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
                command_loader=lambda: _workspace_autopilots_command(client),
            )
            self._set_runtime("_autopilots", _autopilots)
        return self._autopilots  # type: ignore[return-value]


class WorkspaceResource(BaseResource):
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
