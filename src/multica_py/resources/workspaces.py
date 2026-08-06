from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, cast

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
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
from multica_py.resources.issues import _issue_summary_offset_page
from multica_py.resources.labels import Label
from multica_py.resources.projects import Project
from multica_py.resources.skills import Skill
from multica_py.resources.squads import Squad

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


def _workspace_page_issues(
    client: MulticaClient, limit: int | None, offset: int
) -> OffsetPage[IssueSummary]:

    flt = IssueListFilter(
        limit=limit,
        offset=offset,
    )
    return _issue_summary_offset_page(client.issues, flt)


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

            self._set_runtime("_issues", OffsetLazyCollection(page_loader))
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
                LazyCollection[WorkspaceMember](lambda: members(wid)),
            )
        return self._members  # type: ignore[return-value]

    @property
    def agents(self) -> LazyCollection[Agent]:
        if self._agents is None:
            client = self._check_client("agents")

            self._set_runtime("_agents", LazyCollection(client.agents.list))
        return self._agents  # type: ignore[return-value]

    @property
    def skills(self) -> LazyCollection[Skill]:
        if self._skills is None:
            client = self._check_client("skills")

            self._set_runtime("_skills", LazyCollection(client.skills.list))
        return self._skills  # type: ignore[return-value]

    @property
    def projects(self) -> LazyCollection[Project]:
        if self._projects is None:
            client = self._check_client("projects")
            self._set_runtime("_projects", LazyCollection(client.projects.list))
        return self._projects  # type: ignore[return-value]

    @property
    def labels(self) -> LazyCollection[Label]:
        if self._labels is None:
            client = self._check_client("labels")

            self._set_runtime("_labels", LazyCollection(client.labels.list))
        return self._labels  # type: ignore[return-value]

    @property
    def repositories(self) -> LazyCollection[RepositoryRecord]:
        if self._repositories is None:
            client = self._check_client("repositories")

            self._set_runtime("_repositories", LazyCollection(client.repositories.list))
        return self._repositories  # type: ignore[return-value]

    @property
    def runtimes(self) -> LazyCollection[RuntimeDefinition]:
        if self._runtimes is None:
            client = self._check_client("runtimes")

            self._set_runtime("_runtimes", LazyCollection(client.runtimes.list))
        return self._runtimes  # type: ignore[return-value]

    @property
    def squads(self) -> LazyCollection[Squad]:
        if self._squads is None:
            client = self._check_client("squads")

            self._set_runtime("_squads", LazyCollection(client.squads.list))
        return self._squads  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._check_client("issues")

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:
                return _workspace_page_issues(client, limit, offset)

            self._set_runtime("_issues", OffsetLazyCollection(page_loader))
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

            _autopilots = LazyCollection(loader, metadata=RelationMetadata(total=None))
            self._set_runtime("_autopilots", _autopilots)
        return self._autopilots  # type: ignore[return-value]


class WorkspaceResource(BaseResource):
    def list(self) -> tuple[Workspace, ...]:
        items = self._run_json_decode_list(("workspace", "list"), Workspace)
        return tuple(w._with_client(self._client) for w in items)

    def get(self, workspace_id: str) -> Workspace:
        validate_nonblank(workspace_id)
        w = self._run_json_decode(("workspace", "get", workspace_id), Workspace)
        return w._with_client(self._client)

    def members(self, workspace_id: str) -> tuple[WorkspaceMember, ...]:
        members = self._run_json_decode_list(
            ("workspace", "member", "list", workspace_id),
            WorkspaceMember,
        )
        return tuple(item._with_client(self._client) for item in members)

    def switch(self, workspace_id: str) -> None:
        self._transport.run_text(("workspace", "switch", workspace_id))

    def watch(self, workspace_id: str) -> None:
        self._transport.run_text(("workspace", "watch", workspace_id))

    def unwatch(self, workspace_id: str) -> None:
        self._transport.run_text(("workspace", "unwatch", workspace_id))
