from __future__ import annotations

from typing import TYPE_CHECKING

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py.models import ResourceEntity
from multica_py.models.autopilots import AutopilotListPage
from multica_py.models.issues import IssueListFilter, IssueSummary
from multica_py.models.projects import ProjectData
from multica_py.models.relations import (
    LazyCollection,
    OffsetLazyCollection,
    OffsetPage,
    RelationMetadata,
    _RelationLoad,
)
from multica_py.models.system import RepositoryRecord, RuntimeDefinition, WorkspaceMemberData
from multica_py.models.workspaces import Workspace, WorkspaceData, WorkspaceMember
from multica_py.resources._base import BaseResource
from multica_py.resources.agents import AgentEntity
from multica_py.resources.autopilots import AutopilotEntity
from multica_py.resources.issues import _issue_summary_offset_page
from multica_py.resources.labels import Label
from multica_py.resources.projects import Project
from multica_py.resources.skills import SkillEntity
from multica_py.resources.squads import SquadEntity

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


def _bind_workspace(workspace: Workspace, *, client: MulticaClient | None) -> WorkspaceEntity:
    return WorkspaceEntity(
        WorkspaceData(id=workspace.id, name=workspace.name, description=workspace.description),
        client=client,
    )


def _bind_workspace_member(
    member: WorkspaceMember | WorkspaceMemberEntity, *, client: MulticaClient | None
) -> WorkspaceMemberEntity:
    if isinstance(member, WorkspaceMemberEntity):
        return WorkspaceMemberEntity(member.to_data(), client=client)
    return WorkspaceMemberEntity(
        WorkspaceMemberData(
            id=member.id,
            name=member.name,
            role=member.role,
            user_id=member.user_id,
            email=member.email,
        ),
        client=client,
    )


class WorkspaceEntity(ResourceEntity[WorkspaceData]):
    def __init__(self, data: WorkspaceData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)
        self._members: LazyCollection[WorkspaceMemberEntity] | None = None
        self._agents: LazyCollection[AgentEntity] | None = None
        self._skills: LazyCollection[SkillEntity] | None = None
        self._projects: LazyCollection[Project] | None = None
        self._labels: LazyCollection[Label] | None = None
        self._repositories: LazyCollection[RepositoryRecord] | None = None
        self._runtimes: LazyCollection[RuntimeDefinition] | None = None
        self._squads: LazyCollection[SquadEntity] | None = None
        self._issues: OffsetLazyCollection[IssueSummary] | None = None
        self._autopilots: LazyCollection[AutopilotEntity] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def name(self) -> str:
        return self._data.name

    @property
    def description(self) -> str | None:
        return self._data.description

    def _check_client(self, relation_name: str) -> MulticaClient:
        return self._require_client(
            entity_type="WorkspaceEntity", entity_id=self._data.id, relation_name=relation_name
        ).with_workspace(self._data.id)

    @property
    def members(self) -> LazyCollection[WorkspaceMemberEntity]:
        if self._members is None:
            client = self._check_client("members")
            wid = self._data.id

            def loader() -> tuple[WorkspaceMemberEntity, ...]:
                return tuple(
                    _bind_workspace_member(item, client=client)
                    for item in client.workspaces.members(wid)
                )

            self._members = LazyCollection(loader)
        return self._members

    @property
    def agents(self) -> LazyCollection[AgentEntity]:
        if self._agents is None:
            client = self._check_client("agents")

            self._agents = LazyCollection(client.agents.list)
        return self._agents

    @property
    def skills(self) -> LazyCollection[SkillEntity]:
        if self._skills is None:
            client = self._check_client("skills")

            self._skills = LazyCollection(client.skills.list)
        return self._skills

    @property
    def projects(self) -> LazyCollection[Project]:
        if self._projects is None:
            client = self._check_client("projects")

            def loader() -> tuple[Project, ...]:
                from multica_py.resources.projects import Project

                return tuple(
                    Project(
                        item.to_data()
                        if isinstance(item, Project)
                        else ProjectData(
                            id=item.id,
                            name=item.name,
                            description=item.description,
                            status=item.status,
                        ),
                        client=client,
                    )
                    for item in client.projects.list()
                )

            self._projects = LazyCollection(loader)
        return self._projects

    @property
    def labels(self) -> LazyCollection[Label]:
        if self._labels is None:
            client = self._check_client("labels")

            self._labels = LazyCollection(client.labels.list)
        return self._labels

    @property
    def repositories(self) -> LazyCollection[RepositoryRecord]:
        if self._repositories is None:
            client = self._check_client("repositories")

            self._repositories = LazyCollection(client.repositories.list)
        return self._repositories

    @property
    def runtimes(self) -> LazyCollection[RuntimeDefinition]:
        if self._runtimes is None:
            client = self._check_client("runtimes")

            self._runtimes = LazyCollection(client.runtimes.list)
        return self._runtimes

    @property
    def squads(self) -> LazyCollection[SquadEntity]:
        if self._squads is None:
            client = self._check_client("squads")

            self._squads = LazyCollection(client.squads.list)
        return self._squads

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._check_client("issues")

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:
                return _workspace_page_issues(client, limit, offset)

            self._issues = OffsetLazyCollection(page_loader)
        return self._issues

    @property
    def autopilots(self) -> LazyCollection[AutopilotEntity]:
        if self._autopilots is None:
            client = self._check_client("autopilots")

            def loader() -> _RelationLoad[AutopilotEntity]:
                page: AutopilotListPage[AutopilotEntity] = client.autopilots.list()
                return _RelationLoad(
                    page.autopilots,
                    RelationMetadata(total=page.total),
                )

            self._autopilots = LazyCollection(loader, metadata=RelationMetadata(total=None))
        return self._autopilots


class WorkspaceResource(BaseResource):
    def list(self) -> tuple[WorkspaceEntity, ...]:
        items = self._run_json_decode_list(("workspace", "list"), Workspace)
        return tuple(self._bind_workspace(w) for w in items)

    def get(self, workspace_id: str) -> WorkspaceEntity:
        validate_nonblank(workspace_id)
        w = self._run_json_decode(("workspace", "get", workspace_id), Workspace)
        return self._bind_workspace(w)

    def _bind_workspace(self, w: Workspace) -> WorkspaceEntity:
        return _bind_workspace(w, client=self._client)

    def members(self, workspace_id: str) -> tuple[WorkspaceMemberEntity, ...]:
        members = self._run_json_decode_list(
            ("workspace", "member", "list", workspace_id),
            WorkspaceMember,
        )
        return tuple(_bind_workspace_member(item, client=self._client) for item in members)

    def switch(self, workspace_id: str) -> None:
        self._transport.run_text(("workspace", "switch", workspace_id))

    def watch(self, workspace_id: str) -> None:
        self._transport.run_text(("workspace", "watch", workspace_id))

    def unwatch(self, workspace_id: str) -> None:
        self._transport.run_text(("workspace", "unwatch", workspace_id))


class WorkspaceMemberEntity(ResourceEntity[WorkspaceMemberData]):
    def __init__(self, data: WorkspaceMemberData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)
        self._issues: OffsetLazyCollection[IssueSummary] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def name(self) -> str:
        return self._data.name

    @property
    def role(self) -> str | None:
        return self._data.role

    @property
    def user_id(self) -> str | None:
        return self._data.user_id

    @property
    def email(self) -> str | None:
        return self._data.email

    def _check_client(self, relation_name: str) -> MulticaClient:
        return self._require_client(
            entity_type="WorkspaceMemberEntity",
            entity_id=self._data.id,
            relation_name=relation_name,
        )

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._check_client("issues")
            mid = self._data.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:

                flt = IssueListFilter(
                    assignee_id=mid,
                    limit=limit,
                    offset=offset,
                )
                return _issue_summary_offset_page(client.issues, flt)

            self._issues = OffsetLazyCollection(page_loader)
        return self._issues
