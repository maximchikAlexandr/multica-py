from __future__ import annotations

import inspect
from dataclasses import dataclass
from types import ModuleType
from typing import cast

import pytest

import multica_py
import multica_py.models as models_pkg
import multica_py.models.relations as relations_pkg
from multica_py import MulticaClient
from multica_py.enums import IssueStatus
from multica_py.exceptions import (
    DetachedEntityError,
    MissingRelationContextError,
    RelationError,
    RelationPaginationError,
)
from multica_py.models import ResourceEntity
from multica_py.models.agents import AgentData
from multica_py.models.autopilots import AutopilotData, AutopilotRunData
from multica_py.models.issue_activity import CommentData, CommentThreadData, TaskRunData
from multica_py.models.issues import (
    IssueChildrenResult,
    IssueData,
    IssueListFilter,
    IssueListPage,
    IssueMetadataItem,
    IssueSummary,
)
from multica_py.models.labels import LabelData
from multica_py.models.project_resources import ProjectResourceData
from multica_py.models.projects import ProjectData
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    OffsetLazyCollection,
    OffsetPage,
    RelationMetadata,
)
from multica_py.models.skills import SkillData
from multica_py.models.system import (
    AttachmentResult,
    RepositoryRecord,
    RuntimeDefinition,
    SquadData,
    WorkspaceMemberData,
)
from multica_py.models.workspaces import WorkspaceData
from multica_py.resources.agents import AgentEntity
from multica_py.resources.autopilots import AutopilotEntity, AutopilotRunEntity
from multica_py.resources.issue_comments import Comment, CommentThread
from multica_py.resources.issues import IssueEntity, TaskRun
from multica_py.resources.labels import Label
from multica_py.resources.projects import Project
from multica_py.resources.skills import SkillEntity
from multica_py.resources.squads import SquadEntity
from multica_py.resources.workspaces import WorkspaceEntity, WorkspaceMemberEntity
from tests.contract.test_public_invariants import assert_public_annotations_precise


@dataclass(frozen=True)
class UnsupportedRelationCase:
    owner: type[object]
    member: str


UNSUPPORTED_RELATION_CASES = (
    UnsupportedRelationCase(Project, "autopilots"),
    UnsupportedRelationCase(AgentEntity, "autopilots"),
    UnsupportedRelationCase(SquadEntity, "autopilots"),
    UnsupportedRelationCase(Label, "issues"),
    UnsupportedRelationCase(SkillEntity, "agents"),
    UnsupportedRelationCase(RuntimeDefinition, "agents"),
    UnsupportedRelationCase(RepositoryRecord, "projects"),
    UnsupportedRelationCase(WorkspaceEntity, "users"),
)


UNSUPPORTED_RELATION_IDS = tuple(
    f"{case.owner.__name__}.{case.member}" for case in UNSUPPORTED_RELATION_CASES
)


@pytest.mark.parametrize("case", UNSUPPORTED_RELATION_CASES, ids=UNSUPPORTED_RELATION_IDS)
def test_unsupported_inverse_relations_are_absent(case: UnsupportedRelationCase) -> None:
    assert not hasattr(case.owner, case.member)


def test_issue_entity_attachments_are_passive_snapshots() -> None:
    attachment = AttachmentResult(id="a1", filename="result.txt")
    entity = IssueEntity(
        IssueData(id="i1", title="Issue", status=IssueStatus.todo, attachments=(attachment,))
    )
    descriptor = cast("object", inspect.getattr_static(IssueEntity, "attachments"))
    assert type(descriptor).__name__ == "property"
    assert entity.attachments == (attachment,)
    assert entity.attachments == (attachment,)
    assert type(entity.attachments[0]) is AttachmentResult
    assert not hasattr(entity.attachments, "list")
    assert not hasattr(IssueEntity, "_attachments")


def _consumer_type_examples(client: MulticaClient) -> None:
    page: IssueListPage = client.issues.list(
        IssueListFilter(metadata=(IssueMetadataItem(key="external_key", value="queue-key"),))
    )
    summary: IssueSummary = page.issues[0]
    bound_issue: IssueEntity = client.issues.get(summary.id)
    if bound_issue.attachments:
        attachment_id: str = bound_issue.attachments[0].id
        assert attachment_id

    workspace_issues: OffsetLazyCollection[IssueSummary] = client.workspaces.get(
        "workspace_id"
    ).issues
    project_issues: OffsetLazyCollection[IssueSummary] = client.projects.get("project_id").issues
    agent_issues: OffsetLazyCollection[IssueSummary] = client.agents.get("agent_id").issues
    squad_issues: OffsetLazyCollection[IssueSummary] = client.squads.get("squad_id").issues
    member: WorkspaceMemberEntity = client.workspaces.get("workspace_id").members.all()[0]
    member_issues: OffsetLazyCollection[IssueSummary] = member.issues

    relation_summaries: tuple[tuple[IssueSummary, ...], ...] = (
        workspace_issues.all(),
        project_issues.all(),
        agent_issues.all(),
        squad_issues.all(),
        member_issues.all(),
    )
    for summaries in relation_summaries:
        relation_summary: IssueSummary = summaries[0]
        assert isinstance(client.issues.get(relation_summary.id), IssueEntity)

    member_user_id: str | None = member.user_id
    member_email: str | None = member.email
    for summary in page.issues:
        if member_user_id is not None and summary.creator_id == member_user_id:
            assert member_email is None or isinstance(member_email, str)


@dataclass(frozen=True)
class SingularRelationCase:
    owner: type[object]
    members: tuple[str, ...]


SINGULAR_RELATION_CASES = (
    SingularRelationCase(IssueEntity, ("parent", "project", "assignee", "creator")),
    SingularRelationCase(AutopilotEntity, ("project", "assignee", "creator")),
    SingularRelationCase(AutopilotRunEntity, ("autopilot", "issue")),
    SingularRelationCase(TaskRun, ("issue", "autopilot")),
)


SINGULAR_RELATION_IDS = tuple(case.owner.__name__ for case in SINGULAR_RELATION_CASES)


@pytest.mark.parametrize("case", SINGULAR_RELATION_CASES, ids=SINGULAR_RELATION_IDS)
def test_singular_references_are_not_many_relations(case: SingularRelationCase) -> None:
    relation_types: tuple[type[object], ...] = (
        cast("type[object]", LazyCollection),
        cast("type[object]", OffsetLazyCollection),
        cast("type[object]", CursorLazyCollection),
        cast("type[object]", LazyMapping),
    )
    for member in case.members:
        descriptor = cast("object | None", inspect.getattr_static(case.owner, member, None))
        if descriptor is None:
            continue
        assert not isinstance(descriptor, relation_types)


@dataclass(frozen=True)
class PublicExportCase:
    package: ModuleType
    name: str
    value: object


PUBLIC_EXPORT_CASES = (
    PublicExportCase(multica_py, "Agent", AgentEntity),
    PublicExportCase(multica_py, "Autopilot", AutopilotEntity),
    PublicExportCase(multica_py, "AutopilotRun", AutopilotRunEntity),
    PublicExportCase(multica_py, "Comment", Comment),
    PublicExportCase(multica_py, "CommentThread", CommentThread),
    PublicExportCase(multica_py, "Issue", IssueEntity),
    PublicExportCase(multica_py, "Project", Project),
    PublicExportCase(multica_py, "Skill", SkillEntity),
    PublicExportCase(multica_py, "Squad", SquadEntity),
    PublicExportCase(multica_py, "TaskRun", TaskRun),
    PublicExportCase(multica_py, "Workspace", WorkspaceEntity),
    PublicExportCase(multica_py, "WorkspaceMember", WorkspaceMemberEntity),
    PublicExportCase(multica_py, "AgentData", AgentData),
    PublicExportCase(multica_py, "AutopilotData", AutopilotData),
    PublicExportCase(multica_py, "AutopilotRunData", AutopilotRunData),
    PublicExportCase(multica_py, "CommentData", CommentData),
    PublicExportCase(multica_py, "CommentThreadData", CommentThreadData),
    PublicExportCase(multica_py, "IssueData", IssueData),
    PublicExportCase(multica_py, "Label", Label),
    PublicExportCase(multica_py, "LabelData", LabelData),
    PublicExportCase(multica_py, "IssueChildrenResult", IssueChildrenResult),
    PublicExportCase(multica_py, "ProjectData", ProjectData),
    PublicExportCase(multica_py, "ProjectResourceData", ProjectResourceData),
    PublicExportCase(multica_py, "SkillData", SkillData),
    PublicExportCase(multica_py, "SquadData", SquadData),
    PublicExportCase(multica_py, "TaskRunData", TaskRunData),
    PublicExportCase(multica_py, "WorkspaceData", WorkspaceData),
    PublicExportCase(multica_py, "WorkspaceMemberData", WorkspaceMemberData),
    PublicExportCase(multica_py, "CursorLazyCollection", CursorLazyCollection),
    PublicExportCase(multica_py, "CursorPage", CursorPage),
    PublicExportCase(multica_py, "LazyCollection", LazyCollection),
    PublicExportCase(multica_py, "LazyMapping", cast("type[object]", LazyMapping)),
    PublicExportCase(
        multica_py, "OffsetLazyCollection", cast("type[object]", OffsetLazyCollection)
    ),
    PublicExportCase(multica_py, "OffsetPage", cast("type[object]", OffsetPage)),
    PublicExportCase(multica_py, "RelationMetadata", cast("type[object]", RelationMetadata)),
    PublicExportCase(multica_py, "RelationError", RelationError),
    PublicExportCase(multica_py, "DetachedEntityError", DetachedEntityError),
    PublicExportCase(multica_py, "MissingRelationContextError", MissingRelationContextError),
    PublicExportCase(multica_py, "RelationPaginationError", RelationPaginationError),
    PublicExportCase(multica_py, "ResourceEntity", ResourceEntity),
)


PUBLIC_EXPORT_IDS = tuple(case.name for case in PUBLIC_EXPORT_CASES)


@pytest.mark.parametrize("case", PUBLIC_EXPORT_CASES, ids=PUBLIC_EXPORT_IDS)
def test_bound_public_exports_are_explicit(case: PublicExportCase) -> None:
    exports = cast("tuple[str, ...] | list[str]", getattr(case.package, "__all__"))
    assert case.name in exports
    assert cast("object", getattr(case.package, case.name)) is case.value


@pytest.mark.parametrize("case", PUBLIC_EXPORT_CASES, ids=PUBLIC_EXPORT_IDS)
def test_bound_public_export_annotations_are_precise(case: PublicExportCase) -> None:
    if not inspect.isclass(case.value):
        return
    assert_public_annotations_precise(cast("type[object]", case.value))


def test_relation_module_exports_only_public_relation_types() -> None:
    exports = cast("tuple[str, ...]", getattr(relations_pkg, "__all__"))
    assert exports == (
        "CursorLazyCollection",
        "CursorPage",
        "LazyCollection",
        "LazyMapping",
        "OffsetLazyCollection",
        "OffsetPage",
        "RelationMetadata",
    )
    assert all(not name.startswith("_") for name in exports)


def test_models_package_exports_only_non_runtime_relation_types() -> None:
    exports = cast("list[str]", getattr(models_pkg, "__all__"))
    assert "_RelationLoad" not in exports
    assert all(not name.startswith("_") for name in exports)
