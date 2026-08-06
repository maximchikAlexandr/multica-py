from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from types import ModuleType
from typing import cast

import pytest

import multica_py
import multica_py.models as models_pkg
import multica_py.models.relations as relations_pkg
from multica_py import (
    Agent,
    Autopilot,
    AutopilotRun,
    MulticaClient,
    Skill,
    Squad,
    Workspace,
    WorkspaceMember,
)
from multica_py.exceptions import (
    DetachedEntityError,
    MissingRelationContextError,
    RelationError,
    RelationPaginationError,
)
from multica_py.models.issues import (
    IssueChildrenResult,
    IssueListFilter,
    IssueListPage,
    IssueMetadataItem,
    IssueSummary,
)
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    OffsetLazyCollection,
    OffsetPage,
    RelationMetadata,
)
from multica_py.models.system import (
    RepositoryRecord,
    RuntimeDefinition,
)
from multica_py.resources.issue_comments import Comment, CommentThread
from multica_py.resources.issues import Issue, TaskRun
from multica_py.resources.labels import Label
from multica_py.resources.projects import Project
from tests.contract.test_public_invariants import assert_public_annotations_precise


@dataclass(frozen=True)
class UnsupportedRelationCase:
    owner: type[object]
    member: str


UNSUPPORTED_RELATION_CASES = (
    UnsupportedRelationCase(Project, "autopilots"),
    UnsupportedRelationCase(Agent, "autopilots"),
    UnsupportedRelationCase(Squad, "autopilots"),
    UnsupportedRelationCase(Label, "issues"),
    UnsupportedRelationCase(Skill, "agents"),
    UnsupportedRelationCase(RuntimeDefinition, "agents"),
    UnsupportedRelationCase(RepositoryRecord, "projects"),
    UnsupportedRelationCase(Workspace, "users"),
)


UNSUPPORTED_RELATION_IDS = tuple(
    f"{case.owner.__name__}.{case.member}" for case in UNSUPPORTED_RELATION_CASES
)


@pytest.mark.parametrize("case", UNSUPPORTED_RELATION_CASES, ids=UNSUPPORTED_RELATION_IDS)
def test_unsupported_inverse_relations_are_absent(case: UnsupportedRelationCase) -> None:
    assert not hasattr(case.owner, case.member)


def _consumer_type_examples(client: MulticaClient) -> None:
    page: IssueListPage = client.issues.list(
        IssueListFilter(metadata=(IssueMetadataItem(key="external_key", value="queue-key"),))
    )
    summary: IssueSummary = page.issues[0]
    bound_issue: Issue = client.issues.get(summary.id)
    if bound_issue.attachments:
        attachment_id: str = bound_issue.attachments[0].id
        assert attachment_id

    workspace_issues: OffsetLazyCollection[IssueSummary] = client.workspaces.get(
        "workspace_id"
    ).issues
    project_issues: OffsetLazyCollection[IssueSummary] = client.projects.get("project_id").issues
    agent_issues: OffsetLazyCollection[IssueSummary] = client.agents.get("agent_id").issues
    squad_issues: OffsetLazyCollection[IssueSummary] = client.squads.get("squad_id").issues
    member: WorkspaceMember = client.workspaces.get("workspace_id").members.all()[0]
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
        assert isinstance(client.issues.get(relation_summary.id), Issue)

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
    SingularRelationCase(Issue, ("parent", "project", "assignee", "creator")),
    SingularRelationCase(Autopilot, ("project", "assignee", "creator")),
    SingularRelationCase(AutopilotRun, ("autopilot", "issue")),
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
    PublicExportCase(multica_py, "Agent", Agent),
    PublicExportCase(multica_py, "Autopilot", Autopilot),
    PublicExportCase(multica_py, "AutopilotRun", AutopilotRun),
    PublicExportCase(multica_py, "Comment", Comment),
    PublicExportCase(multica_py, "CommentThread", CommentThread),
    PublicExportCase(multica_py, "Issue", Issue),
    PublicExportCase(multica_py, "Project", Project),
    PublicExportCase(multica_py, "Skill", Skill),
    PublicExportCase(multica_py, "Squad", Squad),
    PublicExportCase(multica_py, "TaskRun", TaskRun),
    PublicExportCase(multica_py, "Workspace", Workspace),
    PublicExportCase(multica_py, "WorkspaceMember", WorkspaceMember),
    PublicExportCase(multica_py, "Label", Label),
    PublicExportCase(multica_py, "IssueChildrenResult", IssueChildrenResult),
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
)


PUBLIC_EXPORT_IDS = tuple(case.name for case in PUBLIC_EXPORT_CASES)


@dataclass(frozen=True)
class RemovedPublicNameCase:
    module_name: str
    name: str


REMOVED_PUBLIC_NAMES = (
    *(
        RemovedPublicNameCase("multica_py", name)
        for name in (
            "AgentData",
            "AgentEntity",
            "AutopilotData",
            "AutopilotEntity",
            "AutopilotRunData",
            "AutopilotRunEntity",
            "CommentData",
            "CommentThreadData",
            "IssueData",
            "IssueEntity",
            "LabelData",
            "LabelEntity",
            "ProjectData",
            "ProjectEntity",
            "ProjectResourceData",
            "ResourceEntity",
            "SkillData",
            "SkillEntity",
            "SquadData",
            "SquadEntity",
            "TaskRunData",
            "TaskRunEntity",
            "WorkspaceData",
            "WorkspaceEntity",
            "WorkspaceMemberData",
            "WorkspaceMemberEntity",
        )
    ),
    *(
        RemovedPublicNameCase("multica_py.models", name)
        for name in (
            "AgentData",
            "AutopilotData",
            "AutopilotRunData",
            "CommentData",
            "CommentThreadData",
            "IssueData",
            "LabelData",
            "ProjectData",
            "ProjectResourceData",
            "ResourceEntity",
            "SkillData",
            "SquadData",
            "TaskRunData",
            "WorkspaceData",
            "WorkspaceMemberData",
        )
    ),
    RemovedPublicNameCase("multica_py.models.agents", "AgentData"),
    RemovedPublicNameCase("multica_py.models.agents", "Agent"),
    RemovedPublicNameCase("multica_py.models.autopilots", "AutopilotData"),
    RemovedPublicNameCase("multica_py.models.autopilots", "AutopilotRunData"),
    RemovedPublicNameCase("multica_py.models.autopilots", "Autopilot"),
    RemovedPublicNameCase("multica_py.models.autopilots", "AutopilotRun"),
    RemovedPublicNameCase("multica_py.models.issue_activity", "CommentData"),
    RemovedPublicNameCase("multica_py.models.issue_activity", "CommentThreadData"),
    RemovedPublicNameCase("multica_py.models.issue_activity", "TaskRunData"),
    RemovedPublicNameCase("multica_py.models.issue_activity", "Comment"),
    RemovedPublicNameCase("multica_py.models.issue_activity", "CommentThread"),
    RemovedPublicNameCase("multica_py.models.issue_activity", "TaskRun"),
    RemovedPublicNameCase("multica_py.models.issues", "IssueData"),
    RemovedPublicNameCase("multica_py.models.issues", "Issue"),
    RemovedPublicNameCase("multica_py.models.labels", "LabelData"),
    RemovedPublicNameCase("multica_py.models.projects", "ProjectData"),
    RemovedPublicNameCase("multica_py.models.projects", "Project"),
    RemovedPublicNameCase("multica_py.models.project_resources", "ProjectResourceData"),
    RemovedPublicNameCase("multica_py.models.skills", "SkillData"),
    RemovedPublicNameCase("multica_py.models.skills", "Skill"),
    RemovedPublicNameCase("multica_py.models.system", "SquadData"),
    RemovedPublicNameCase("multica_py.models.system", "Squad"),
    RemovedPublicNameCase("multica_py.models.system", "WorkspaceMemberData"),
    RemovedPublicNameCase("multica_py.models.workspaces", "WorkspaceData"),
    RemovedPublicNameCase("multica_py.models.workspaces", "Workspace"),
    RemovedPublicNameCase("multica_py.resources.agents", "AgentEntity"),
    RemovedPublicNameCase("multica_py.resources.autopilots", "AutopilotEntity"),
    RemovedPublicNameCase("multica_py.resources.autopilots", "AutopilotRunEntity"),
    RemovedPublicNameCase("multica_py.resources.issues", "IssueEntity"),
    RemovedPublicNameCase("multica_py.resources.skills", "SkillEntity"),
    RemovedPublicNameCase("multica_py.resources.squads", "SquadEntity"),
    RemovedPublicNameCase("multica_py.resources.workspaces", "WorkspaceEntity"),
    RemovedPublicNameCase("multica_py.resources.workspaces", "WorkspaceMemberEntity"),
)


REMOVED_PUBLIC_NAME_IDS = tuple(f"{case.module_name}.{case.name}" for case in REMOVED_PUBLIC_NAMES)


@pytest.mark.parametrize("case", REMOVED_PUBLIC_NAMES, ids=REMOVED_PUBLIC_NAME_IDS)
def test_removed_public_names_are_absent(case: RemovedPublicNameCase) -> None:
    module = importlib.import_module(case.module_name)
    exports = cast("tuple[str, ...] | list[str]", getattr(module, "__all__", ()))
    assert case.name not in exports
    assert not hasattr(module, case.name)


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
