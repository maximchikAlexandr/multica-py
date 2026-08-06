from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, cast

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command, _replace_plan, _Step
from multica_py.models._bound import _BoundEntity
from multica_py.models.autopilots import AutopilotListPage
from multica_py.models.issues import IssueListFilter, IssueSummary
from multica_py.models.relations import (
    LazyCollection,
    OffsetLazyCollection,
    OffsetPage,
    RelationMetadata,
    _RelationLoad,
)
from multica_py.models.system import RepositoryRecord, RuntimeDefinition
from multica_py.resources._base import BaseResource
from multica_py.resources.agents import Agent
from multica_py.resources.autopilots import Autopilot
from multica_py.resources.issues import (
    _issue_summary_offset_page,
    _issue_summary_offset_page_command,
)
from multica_py.resources.labels import Label
from multica_py.resources.projects import Project
from multica_py.resources.skills import Skill
from multica_py.resources.squads import Squad

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


S = TypeVar("S", bound=msgspec.Struct)


def _workspace_page_issues(
    client: MulticaClient, limit: int | None, offset: int
) -> OffsetPage[IssueSummary]:

    flt = IssueListFilter(
        limit=limit,
        offset=offset,
    )
    return _issue_summary_offset_page(client.issues, flt)


def _resource_list_command(
    resource: BaseResource,
    args: tuple[str, ...],
    item_type: type[S],
    bind: Callable[[S], S] | None = None,
) -> Command[tuple[S, ...]]:
    plan_args, decode = resource._plan_decode_list(args, item_type)

    def finalize(results: tuple[object, ...]) -> tuple[S, ...]:
        items = cast("tuple[S, ...]", results[0])
        return tuple(bind(item) if bind is not None else item for item in items)

    return resource._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)


def _workspace_issues_page_command(
    client: MulticaClient,
    assignee_id: str | None,
    limit: int | None,
    offset: int,
) -> Command[OffsetPage[IssueSummary]]:
    return _issue_summary_offset_page_command(
        client.issues,
        IssueListFilter(assignee_id=assignee_id, limit=limit, offset=offset),
    )


def _workspace_autopilots_command(
    client: MulticaClient,
) -> Command[_RelationLoad[Autopilot]]:
    command = client.autopilots.list_command()
    plan = command._plan

    def finalize(results: tuple[object, ...]) -> _RelationLoad[Autopilot]:
        page = plan.finalize(results)
        return _RelationLoad(page.autopilots, RelationMetadata(total=page.total))

    return Command(_replace_plan(plan, finalize=finalize))


class WorkspaceMember(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    role: str | None = None
    user_id: str | None = None
    email: str | None = None

    _issues: OffsetLazyCollection[IssueSummary] | None = msgspec.field(default=None, name="_issues")

    _PUBLIC_FIELDS = ("id", "name", "role", "user_id", "email")

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._require_client(
                entity_type="WorkspaceMember", entity_id=self.id, relation_name="issues"
            )
            mid = self.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:

                flt = IssueListFilter(
                    assignee_id=mid,
                    limit=limit,
                    offset=offset,
                )
                return _issue_summary_offset_page(client.issues, flt)

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
    _issues: OffsetLazyCollection[IssueSummary] | None = msgspec.field(default=None, name="_issues")
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
            members = cast(
                "Callable[[str], tuple[WorkspaceMember, ...]]", client.workspaces.members
            )
            self._set_runtime(
                "_members",
                LazyCollection[WorkspaceMember](
                    lambda: members(wid),
                    command_loader=lambda: client.workspaces.members_command(wid),
                ),
            )
        return self._members  # type: ignore[return-value]

    @property
    def agents(self) -> LazyCollection[Agent]:
        if self._agents is None:
            client = self._check_client("agents")

            self._set_runtime(
                "_agents",
                LazyCollection(
                    client.agents.list,
                    command_loader=client.agents.list_command,
                ),
            )
        return self._agents  # type: ignore[return-value]

    @property
    def skills(self) -> LazyCollection[Skill]:
        if self._skills is None:
            client = self._check_client("skills")

            self._set_runtime(
                "_skills",
                LazyCollection(
                    client.skills.list,
                    command_loader=client.skills.list_command,
                ),
            )
        return self._skills  # type: ignore[return-value]

    @property
    def projects(self) -> LazyCollection[Project]:
        if self._projects is None:
            client = self._check_client("projects")
            self._set_runtime(
                "_projects",
                LazyCollection(
                    client.projects.list,
                    command_loader=client.projects.list_command,
                ),
            )
        return self._projects  # type: ignore[return-value]

    @property
    def labels(self) -> LazyCollection[Label]:
        if self._labels is None:
            client = self._check_client("labels")

            self._set_runtime(
                "_labels",
                LazyCollection(
                    client.labels.list,
                    command_loader=lambda: _resource_list_command(
                        client.labels,
                        ("label", "list"),
                        Label,
                        bind=lambda item: item._with_client(client),
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
                LazyCollection(
                    client.repositories.list,
                    command_loader=lambda: _resource_list_command(
                        client.repositories,
                        ("repo", "list"),
                        RepositoryRecord,
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
                LazyCollection(
                    client.runtimes.list,
                    command_loader=lambda: _resource_list_command(
                        client.runtimes,
                        ("runtime", "list"),
                        RuntimeDefinition,
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
                LazyCollection(
                    client.squads.list,
                    command_loader=client.squads.list_command,
                ),
            )
        return self._squads  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._check_client("issues")

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:
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
    def list_command(self) -> Command[tuple[Workspace, ...]]:
        args, decode = self._plan_decode_list(("workspace", "list"), Workspace)

        def finalize(results: tuple[object, ...]) -> tuple[Workspace, ...]:
            items = cast("tuple[Workspace, ...]", results[0])
            return tuple(item._with_client(self._client) for item in items)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def list(self) -> tuple[Workspace, ...]:
        return self.list_command().run()

    def get_command(self, workspace_id: str) -> Command[Workspace]:
        validate_nonblank(workspace_id)
        args, decode = self._plan_decode(("workspace", "get", workspace_id), Workspace)

        def finalize(results: tuple[object, ...]) -> Workspace:
            return cast("Workspace", results[0])._with_client(self._client)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def get(self, workspace_id: str) -> Workspace:
        return self.get_command(workspace_id).run()

    def members_command(self, workspace_id: str) -> Command[tuple[WorkspaceMember, ...]]:
        args, decode = self._plan_decode_list(
            ("workspace", "member", "list", workspace_id), WorkspaceMember
        )

        def finalize(results: tuple[object, ...]) -> tuple[WorkspaceMember, ...]:
            items = cast("tuple[WorkspaceMember, ...]", results[0])
            return tuple(item._with_client(self._client) for item in items)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def members(self, workspace_id: str) -> tuple[WorkspaceMember, ...]:
        return self.members_command(workspace_id).run()

    def switch_command(self, workspace_id: str) -> Command[None]:
        return self._plan(
            steps=(_Step(("workspace", "switch", workspace_id), "run_text"),),
            finalize=lambda results: None,
        )

    def switch(self, workspace_id: str) -> None:
        self.switch_command(workspace_id).run()

    def watch_command(self, workspace_id: str) -> Command[None]:
        return self._plan(
            steps=(_Step(("workspace", "watch", workspace_id), "run_text"),),
            finalize=lambda results: None,
        )

    def watch(self, workspace_id: str) -> None:
        self.watch_command(workspace_id).run()

    def unwatch_command(self, workspace_id: str) -> Command[None]:
        return self._plan(
            steps=(_Step(("workspace", "unwatch", workspace_id), "run_text"),),
            finalize=lambda results: None,
        )

    def unwatch(self, workspace_id: str) -> None:
        self.unwatch_command(workspace_id).run()
