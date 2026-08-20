from __future__ import annotations

import importlib
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from types import ModuleType
from typing import cast, get_origin, get_type_hints

import pytest

import multica_py
import multica_py.models as models_pkg
import multica_py.models.relations as relations_pkg
from multica_py import (
    Agent,
    Autopilot,
    AutopilotRun,
    Command,
    MulticaClient,
    Skill,
    Squad,
    Workspace,
    WorkspaceMember,
)
from multica_py.entities import Comment, CommentThread, Issue, Label, Project, TaskRun
from multica_py.exceptions import (
    DetachedEntityError,
    MissingPermalinkContextError,
    MissingRelationContextError,
    RelationError,
    RelationPaginationError,
    UnloadedReferenceError,
    UnsupportedReferenceTargetError,
)
from multica_py.models.issues import IssueListFilter, IssueListPage, IssueMetadataItem
from multica_py.models.plugins import Plugin
from multica_py.models.properties import PropertyValue
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    LazyRef,
    OffsetLazyCollection,
    OffsetPage,
    RelationMetadata,
)
from multica_py.models.system import (
    RepositoryRecord,
    RuntimeDefinition,
)
from multica_py.models.workspaces import McpServer
from multica_py.resources.projects import ProjectIssueCollection
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
    issue: Issue = page.issues[0]
    bound_issue: Issue = client.issues.get(issue.id)
    if bound_issue.attachments:
        attachment_id: str = bound_issue.attachments[0].id
        assert attachment_id

    workspace_issues: OffsetLazyCollection[Issue] = client.workspaces.get("workspace_id").issues
    project_issues = cast("ProjectIssueCollection", client.projects.get("project_id").issues)
    agent_issues: OffsetLazyCollection[Issue] = client.agents.get("agent_id").issues
    squad_issues: OffsetLazyCollection[Issue] = client.squads.get("squad_id").issues
    member: WorkspaceMember = client.workspaces.get("workspace_id").members.all()[0]
    member_issues: OffsetLazyCollection[Issue] = member.issues

    relation_issues: tuple[tuple[Issue, ...], ...] = (
        workspace_issues.all(),
        project_issues.all(),
        agent_issues.all(),
        squad_issues.all(),
        member_issues.all(),
    )
    for issues in relation_issues:
        relation_issue: Issue = issues[0]
        assert isinstance(relation_issue, Issue)

    member_user_id: str | None = member.user_id
    member_email: str | None = member.email
    for issue in page.issues:
        if member_user_id is not None and issue.creator_id == member_user_id:
            assert member_email is None or isinstance(member_email, str)


@dataclass(frozen=True)
class SingularRelationCase:
    owner: type[object]
    members: tuple[str, ...]


SINGULAR_RELATION_CASES = (
    SingularRelationCase(Issue, ("parent", "project", "assignee_ref")),
    SingularRelationCase(Autopilot, ("project", "assignee")),
    SingularRelationCase(AutopilotRun, ("autopilot", "issue")),
    SingularRelationCase(TaskRun, ("issue", "agent")),
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


EXPECTED_LAZY_REF_MEMBERS = {
    Issue: {"parent", "project", "assignee_ref"},
    Autopilot: {"project", "assignee"},
    AutopilotRun: {"autopilot", "issue"},
    TaskRun: {"issue", "agent"},
}


def _lazy_ref_members(owner: type[object]) -> set[str]:
    members: set[str] = set()
    for name in dir(owner):
        descriptor = cast("object | None", inspect.getattr_static(owner, name, None))
        getter = cast("Callable[[object], object] | None", getattr(descriptor, "fget", None))
        if getter is None:
            continue
        annotation = cast("dict[str, object]", get_type_hints(getter))["return"]
        if cast("object", get_origin(annotation)) is cast("object", LazyRef):
            members.add(name)
    return members


def test_exact_nine_lazy_ref_members_are_public_and_inventory_bound() -> None:
    discovered = {owner: _lazy_ref_members(owner) for owner in EXPECTED_LAZY_REF_MEMBERS}
    assert discovered == EXPECTED_LAZY_REF_MEMBERS
    assert sum(len(members) for members in discovered.values()) == 9


@dataclass(frozen=True)
class ExcludedSingularCase:
    owner: type[object]
    names: frozenset[str]


UNSUPPORTED_SINGULAR_NAMES = (
    ExcludedSingularCase(
        Issue, frozenset({"creator", "member", "trigger", "task", "author", "users", "leader"})
    ),
    ExcludedSingularCase(
        Autopilot,
        frozenset({"creator", "member", "trigger", "task", "author", "users", "leader"}),
    ),
    ExcludedSingularCase(
        AutopilotRun,
        frozenset({"creator", "member", "trigger", "task", "author", "users", "agent"}),
    ),
    ExcludedSingularCase(
        TaskRun,
        frozenset({"autopilot", "creator", "member", "trigger", "task", "author", "users"}),
    ),
)


def _excluded_singular_id(case: ExcludedSingularCase) -> str:
    return case.owner.__name__


@pytest.mark.parametrize(
    "case",
    UNSUPPORTED_SINGULAR_NAMES,
    ids=_excluded_singular_id,
)
def test_excluded_singular_edges_have_no_lazy_ref_surface(case: ExcludedSingularCase) -> None:
    assert _lazy_ref_members(case.owner).isdisjoint(case.names)


def test_property_plugin_and_mcp_ids_remain_passive_values() -> None:
    property_value = PropertyValue(
        property_id="property-1", name="Priority", type="text", value="high"
    )
    plugin = Plugin(
        plugin_key="plugin-1",
        desired_version="1.0.0",
        lifecycle_status="installed",
        trust_tier="trusted",
        uploader_id="agent-1",
    )
    mcp_server = McpServer(id="server-1", name="MCP", transport="stdio")

    assert isinstance(property_value.property_id, str)
    assert isinstance(plugin.uploader_id, str)
    assert isinstance(mcp_server.id, str)
    assert not _lazy_ref_members(type(property_value))
    assert not _lazy_ref_members(type(plugin))
    assert not _lazy_ref_members(type(mcp_server))


@dataclass(frozen=True)
class PublicExportCase:
    package: ModuleType
    name: str
    value: object


PUBLIC_EXPORT_CASES = (
    PublicExportCase(multica_py, "Agent", Agent),
    PublicExportCase(multica_py, "Command", Command),
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
    PublicExportCase(multica_py, "RelationError", RelationError),
    PublicExportCase(multica_py, "DetachedEntityError", DetachedEntityError),
    PublicExportCase(multica_py, "MissingRelationContextError", MissingRelationContextError),
    PublicExportCase(
        multica_py, "UnsupportedReferenceTargetError", UnsupportedReferenceTargetError
    ),
    PublicExportCase(multica_py, "UnloadedReferenceError", UnloadedReferenceError),
    PublicExportCase(multica_py, "MissingPermalinkContextError", MissingPermalinkContextError),
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
            "AgentEntity",
            "AutopilotData",
            "AutopilotEntity",
            "AutopilotRunData",
            "AutopilotRunEntity",
            "CommentData",
            "CommentEntity",
            "CommentThreadData",
            "CommentThreadEntity",
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
        "LazyRef",
        "OffsetLazyCollection",
        "OffsetPage",
        "RelationMetadata",
    )
    assert all(not name.startswith("_") for name in exports)


def test_lazy_ref_is_only_exported_by_the_dedicated_relations_module() -> None:
    assert LazyRef.__module__ == "multica_py.models.relations"
    assert "LazyRef" in relations_pkg.__all__
    assert not hasattr(multica_py, "LazyRef")
    assert not hasattr(models_pkg, "LazyRef")
    assert "LazyRef" not in multica_py.__all__
    assert "LazyRef" not in models_pkg.__all__


def test_models_package_exports_only_non_runtime_relation_types() -> None:
    exports = cast("list[str]", getattr(models_pkg, "__all__"))
    assert "_RelationLoad" not in exports
    assert all(not name.startswith("_") for name in exports)


def test_canonical_entities_preserve_resource_compatibility_identity() -> None:
    from multica_py.resources.issue_comments import (
        Comment as ResourceComment,
    )
    from multica_py.resources.issue_comments import (
        CommentThread as ResourceCommentThread,
    )
    from multica_py.resources.issues import Issue as ResourceIssue
    from multica_py.resources.issues import TaskRun as ResourceTaskRun
    from multica_py.resources.labels import Label as ResourceLabel
    from multica_py.resources.projects import Project as ResourceProject

    assert Comment is ResourceComment
    assert CommentThread is ResourceCommentThread
    assert Issue is ResourceIssue
    assert Label is ResourceLabel
    assert Project is ResourceProject
    assert TaskRun is ResourceTaskRun


def test_process_root_exports_remain_curated() -> None:
    assert multica_py.ProcessResult.__module__ == "multica_py.process"
    assert multica_py.ProcessOutputModeError.__module__ == "multica_py.exceptions"
    assert "ManagedProcess" in multica_py.__all__
    assert "ProcessResult" in multica_py.__all__
    assert "ProcessOutputModeError" in multica_py.__all__
    assert "ProcessOutputMode" not in multica_py.__all__
