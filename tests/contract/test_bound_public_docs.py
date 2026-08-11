from __future__ import annotations

import ast
import datetime
import inspect
import re
import typing
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig, OperationOptions
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.models.common import CommentCursor
from multica_py.models.issue_activity import MetadataPredicate
from multica_py.resources.agents import AgentResource
from multica_py.resources.attachments import AttachmentResource
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.cli import CliResource
from multica_py.resources.issue_comments import IssueCommentResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issues import Issue, IssueResource
from multica_py.resources.labels import LabelResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.resources.projects import Project, ProjectIssueCollection, ProjectResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.skills import SkillResource
from multica_py.resources.users import UserResource

ROOT = Path(__file__).parents[2]


@dataclass(frozen=True)
class DocumentationCase:
    path: Path
    required_text: str


MIGRATION_CASES = (
    DocumentationCase(
        ROOT / "docs/migration.md", "canonical public import path for the bound agent domain class"
    ),
    DocumentationCase(ROOT / "docs/migration.md", "multica_py.resources.agents.Agent"),
    DocumentationCase(ROOT / "docs/migration.md", "Agent.skill_refs"),
    DocumentationCase(ROOT / "docs/migration.md", "agent skills list/set"),
    DocumentationCase(ROOT / "docs/migration.md", "Skill.files"),
    DocumentationCase(ROOT / "docs/migration.md", "Issue.label_names"),
    DocumentationCase(ROOT / "docs/migration.md", "Issue.child_stages"),
    DocumentationCase(ROOT / "docs/migration.md", "Issue.metadata_snapshot"),
    DocumentationCase(ROOT / "docs/migration.md", "IssueData.pull_requests"),
    DocumentationCase(ROOT / "docs/migration.md", "Issue.pull_request_snapshot"),
    DocumentationCase(ROOT / "docs/migration.md", "issues.rerun(issue_id)"),
    DocumentationCase(ROOT / "docs/migration.md", "issues.cancel_task(task_id)"),
    DocumentationCase(ROOT / "docs/migration.md", "issues.run_messages(task_run_id"),
    DocumentationCase(ROOT / "docs/migration.md", "attachments.list(issue_id)"),
    DocumentationCase(ROOT / "docs/migration.md", "users.profile_get()"),
    DocumentationCase(ROOT / "docs/migration.md", "repositories.get(repo_id)"),
    DocumentationCase(ROOT / "docs/migration.md", "runtimes.get(runtime_id)"),
    DocumentationCase(ROOT / "docs/migration.md", "autopilots.trigger(autopilot_id)"),
    DocumentationCase(ROOT / "docs/migration.md", "autopilots.get_run(run_id)"),
    DocumentationCase(ROOT / "docs/migration.md", "Project.autopilots"),
    DocumentationCase(ROOT / "docs/migration.md", "ManyRelation"),
    DocumentationCase(ROOT / "docs/migration.md", "LazyRef"),
    DocumentationCase(
        ROOT / "docs/migration.md",
        "Direct issue lists, the five list-backed relations, and child collections",
    ),
    DocumentationCase(ROOT / "docs/migration.md", "Workspace.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "Project.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "Agent.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "Squad.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "WorkspaceMember.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "no implicit `issues.get` hydration occurs"),
    DocumentationCase(ROOT / "docs/migration.md", "WorkspaceMember.id"),
    DocumentationCase(ROOT / "docs/migration.md", "WorkspaceMember.user_id"),
    DocumentationCase(ROOT / "docs/migration.md", "user_id is None"),
    DocumentationCase(ROOT / "docs/migration.md", "Issue.attachments"),
    DocumentationCase(
        ROOT / "docs/migration.md", "attachments.download_bytes(issue.attachments[0].id)"
    ),
    DocumentationCase(ROOT / "docs/migration.md", "best-effort"),
)


COMMAND_DOCUMENTATION_CASES = (
    DocumentationCase(ROOT / "docs/api.md", "Command[T]"),
    DocumentationCase(ROOT / "docs/api.md", "commands` is always a tuple"),
    DocumentationCase(ROOT / "docs/api.md", "Preview performs no"),
    DocumentationCase(ROOT / "docs/api.md", "immutable plan"),
    DocumentationCase(ROOT / "docs/service-usage.md", 'client.issues.get_command("issue_123")'),
    DocumentationCase(ROOT / "docs/service-usage.md", "${create.id}"),
    DocumentationCase(ROOT / "docs/migration.md", "`Command[T]`"),
)


CONVENTION_DOCUMENTATION_CASES = (
    DocumentationCase(ROOT / "docs/api.md", "## SDK-wide operation conventions"),
    DocumentationCase(ROOT / "docs/api.md", "direct = client.issues.list"),
    DocumentationCase(ROOT / "docs/api.md", "all-optional updates"),
    DocumentationCase(ROOT / "docs/api.md", "ActionResult[None]"),
    DocumentationCase(ROOT / "docs/api.md", "Bound relation `.all()` snapshots"),
    DocumentationCase(ROOT / "docs/service-usage.md", "## Direct inputs, options, and presence"),
    DocumentationCase(ROOT / "docs/service-usage.md", "mutation.value.added"),
    DocumentationCase(ROOT / "README.md", 'scoped.issues.list(status="todo"'),
    DocumentationCase(ROOT / "README.md", "ActionResult[T]"),
    DocumentationCase(ROOT / "docs/migration.md", "### Breaking return matrix"),
    DocumentationCase(
        ROOT / "docs/migration.md", "Relation `.all()` snapshots are explicitly unchanged"
    ),
    DocumentationCase(ROOT / "CHANGELOG.md", "## Unreleased — unified SDK operation contracts"),
    DocumentationCase(ROOT / "CHANGELOG.md", "Breaking before/after inventory"),
    DocumentationCase(ROOT / "examples/issue_queue.py", "yield from page.items"),
    DocumentationCase(ROOT / "examples/self_hosted_local.py", "client.projects.list().items"),
    DocumentationCase(ROOT / "examples/public_workflow.py", "scoped.cli.command"),
)


RAW_BOUNDARY_DOCUMENTATION_CASES = (
    DocumentationCase(ROOT / "docs/api.md", "## Raw CLI execution boundary"),
    DocumentationCase(ROOT / "docs/api.md", "auth login --token <token>"),
    DocumentationCase(ROOT / "docs/api.md", "setup cloud"),
    DocumentationCase(ROOT / "docs/api.md", "setup self-host"),
    DocumentationCase(ROOT / "docs/api.md", "daemon start"),
    DocumentationCase(ROOT / "docs/api.md", "daemon logs"),
    DocumentationCase(ROOT / "docs/api.md", "top-level `update`"),
    DocumentationCase(ROOT / "docs/api.md", "workspace watch"),
    DocumentationCase(ROOT / "docs/api.md", "Unknown non-interactive bounded argv"),
    DocumentationCase(ROOT / "docs/service-usage.md", "no transport or spawn call"),
    DocumentationCase(ROOT / "docs/service-usage.md", "redaction marker `***`"),
)


@pytest.mark.parametrize(
    "case", MIGRATION_CASES, ids=tuple(case.required_text for case in MIGRATION_CASES)
)
def test_migration_table_covers_required_surface(case: DocumentationCase) -> None:
    assert case.required_text in case.path.read_text()


@pytest.mark.parametrize(
    "case",
    COMMAND_DOCUMENTATION_CASES,
    ids=tuple(case.required_text for case in COMMAND_DOCUMENTATION_CASES),
)
def test_command_preview_documentation_is_pinned(case: DocumentationCase) -> None:
    assert case.required_text in case.path.read_text()


@pytest.mark.parametrize(
    "case",
    CONVENTION_DOCUMENTATION_CASES,
    ids=tuple(case.required_text for case in CONVENTION_DOCUMENTATION_CASES),
)
def test_operation_conventions_are_documented(case: DocumentationCase) -> None:
    assert case.required_text in case.path.read_text()


@pytest.mark.parametrize(
    "case",
    RAW_BOUNDARY_DOCUMENTATION_CASES,
    ids=tuple(case.required_text for case in RAW_BOUNDARY_DOCUMENTATION_CASES),
)
def test_raw_boundary_documentation_is_complete(case: DocumentationCase) -> None:
    assert case.required_text in case.path.read_text()


def test_readme_teaches_the_canonical_workflow_in_order() -> None:
    readme = (ROOT / "README.md").read_text()
    markers = (
        "client = MulticaClient()",
        'client.issues.get("issue_123")',
        'issue.set_status("done")',
        'client.issues.list(status="todo"',
        'client.issues.get_command("issue_123")',
    )
    positions = tuple(readme.index(marker) for marker in markers)
    assert positions == tuple(sorted(positions))


def test_active_docs_use_exact_statuses_and_no_secret_or_stale_claims() -> None:
    paths = [ROOT / "README.md", ROOT / "docs/api.md", ROOT / "docs/service-usage.md"]
    paths.extend((ROOT / "examples").glob("*.py"))
    documents = "\n".join(path.read_text() for path in paths)

    assert not re.search(r"\bopen\b", documents, flags=re.IGNORECASE)
    assert "secret-token" not in documents
    assert "raw-token" not in documents
    assert "request-object" not in documents
    assert "IssueCreateRequest" not in documents
    assert "ProjectCreateRequest" not in documents
    assert "description_input" in documents
    assert "description_file" in documents
    assert "project=project" in documents


def test_documented_result_examples_follow_current_signatures() -> None:
    from multica_py.models.common import ActionResult, Page
    from multica_py.resources.autopilots import AutopilotResource
    from multica_py.resources.issues import IssueResource
    from multica_py.resources.projects import ProjectResource

    api = (ROOT / "docs/api.md").read_text()
    service = (ROOT / "docs/service-usage.md").read_text()

    def return_annotation(method: object) -> object:
        hints = cast(
            "dict[str, object]",
            typing.get_type_hints(cast("Callable[[], object]", method)),
        )
        return hints["return"]

    read_types = (
        return_annotation(cast("object", getattr(IssueResource, "list"))),
        return_annotation(cast("object", getattr(ProjectResource, "list"))),
    )
    assert any(cast("object", typing.get_origin(result)) is Page for result in read_types)
    assert any(
        cast("object", getattr(result, "__name__", "")) == "IssueListPage" for result in read_types
    )
    assert "Page[T]" in api and "Page[Issue]" in service

    action_return = return_annotation(cast("object", getattr(AutopilotResource, "delete")))
    assert cast("object", typing.get_origin(action_return)) is ActionResult
    assert "ActionResult[None]" in api


def test_docs_do_not_reintroduce_legacy_request_or_result_conventions() -> None:
    documents = "\n".join(
        (ROOT / relative).read_text()
        for relative in ("docs/api.md", "docs/service-usage.md", "README.md")
    )
    forbidden = (
        "The request-object form is the only option",
        "returns `tuple[IssueSummary, ...]`",
        "returns `Command[tuple[IssueSummary, ...]]`",
        "Page[IssueSummary]",
        "IssueSummary",
        "Use `entity.to_data()`",
    )
    assert not any(phrase in documents for phrase in forbidden)


REMOVED_DTO_NAMES = (
    "AgentCreateRequest",
    "AgentUpdateRequest",
    "ProjectCreateRequest",
    "ProjectUpdateRequest",
    "SkillCreateRequest",
    "SkillUpdateRequest",
    "LabelUpdateRequest",
    "IssueCreateRequest",
    "IssueUpdateRequest",
    "IssueAssignmentRequest",
    "IssueReorderRequest",
    "CommentListFlatRequest",
    "CommentListRecentRequest",
    "CommentListThreadRequest",
    "MetadataListRequest",
    "MetadataSetRequest",
    "ProjectResourceAddLocalDirectoryRequest",
    "ProjectResourceUpdateLocalDirectoryRequest",
    "AutopilotUpdateRequest",
    "AutopilotTriggerCreate",
    "AutopilotTriggerUpdate",
    "RuntimeUpdate",
    "UserProfileUpdate",
)


@dataclass(frozen=True)
class MigrationInventoryCase:
    dto: str
    before: str
    legacy_fields: tuple[str, ...]
    required_fields: tuple[str, ...]


MIGRATION_INVENTORY = (
    MigrationInventoryCase(
        "AgentCreateRequest",
        'AgentCreateRequest(name="build")',
        ("name", "description", "runtime_id", "model"),
        ("name",),
    ),
    MigrationInventoryCase(
        "AgentUpdateRequest",
        'AgentUpdateRequest(name="build")',
        ("name", "description"),
        (),
    ),
    MigrationInventoryCase(
        "ProjectCreateRequest",
        'ProjectCreateRequest(name="alpha")',
        ("name", "description"),
        ("name",),
    ),
    MigrationInventoryCase(
        "ProjectUpdateRequest",
        'ProjectUpdateRequest(name="alpha")',
        ("name", "description"),
        (),
    ),
    MigrationInventoryCase(
        "SkillCreateRequest",
        'SkillCreateRequest(name="lint")',
        ("name", "description"),
        ("name",),
    ),
    MigrationInventoryCase(
        "SkillUpdateRequest",
        'SkillUpdateRequest(name="lint")',
        ("name", "description"),
        (),
    ),
    MigrationInventoryCase(
        "LabelUpdateRequest",
        'LabelUpdateRequest(name="ready")',
        ("name", "color"),
        (),
    ),
    MigrationInventoryCase(
        "IssueCreateRequest",
        'IssueCreateRequest(title="Deploy")',
        (
            "title",
            "description_input",
            "priority",
            "assignee_id",
            "label_ids",
            "project_id",
            "parent_id",
        ),
        ("title",),
    ),
    MigrationInventoryCase(
        "IssueUpdateRequest",
        'IssueUpdateRequest(description="Ready")',
        ("title", "description", "priority", "assignee_id", "project_id", "parent_id"),
        (),
    ),
    MigrationInventoryCase(
        "IssueAssignmentRequest",
        "IssueAssignmentRequest(issue_id=issue_id, member_id=member_id)",
        ("issue_id", "member_id", "agent_id", "squad_id", "unassign"),
        ("issue_id", "member_id"),
    ),
    MigrationInventoryCase(
        "IssueAssignmentRequest",
        "IssueAssignmentRequest(issue_id=issue_id, agent_id=agent_id)",
        ("issue_id", "member_id", "agent_id", "squad_id", "unassign"),
        ("issue_id", "agent_id"),
    ),
    MigrationInventoryCase(
        "IssueReorderRequest",
        "IssueReorderRequest(issue_id=issue_id, before_id=target_id)",
        ("issue_id", "before_id", "after_id", "top", "bottom"),
        ("issue_id", "before_id"),
    ),
    MigrationInventoryCase(
        "CommentListFlatRequest",
        "CommentListFlatRequest(issue_id=issue_id, since=since)",
        ("issue_id", "since"),
        ("issue_id",),
    ),
    MigrationInventoryCase(
        "CommentListRecentRequest",
        "CommentListRecentRequest(issue_id=issue_id, limit=20)",
        ("issue_id", "cursor", "limit", "since"),
        ("issue_id",),
    ),
    MigrationInventoryCase(
        "CommentListThreadRequest",
        "CommentListThreadRequest(issue_id=issue_id, thread_id=thread_id, cursor=cursor, limit=50)",
        ("issue_id", "thread_id", "cursor", "limit", "since"),
        ("issue_id", "thread_id"),
    ),
    MigrationInventoryCase(
        "MetadataListRequest",
        "MetadataListRequest(issue_id=issue_id, predicates=predicates, cursor=cursor, limit=limit)",
        ("issue_id", "predicates", "cursor", "limit"),
        ("issue_id",),
    ),
    MigrationInventoryCase(
        "MetadataSetRequest",
        'MetadataSetRequest(issue_id=issue_id, key="build.id", value="42")',
        ("issue_id", "key", "value", "value_type"),
        ("issue_id", "key", "value"),
    ),
    MigrationInventoryCase(
        "ProjectResourceAddLocalDirectoryRequest",
        "ProjectResourceAddLocalDirectoryRequest(local_path=path, daemon_id=daemon_id)",
        ("local_path", "daemon_id", "label"),
        ("local_path", "daemon_id"),
    ),
    MigrationInventoryCase(
        "ProjectResourceUpdateLocalDirectoryRequest",
        "ProjectResourceUpdateLocalDirectoryRequest(local_path=path)",
        ("local_path",),
        ("local_path",),
    ),
    MigrationInventoryCase(
        "AutopilotUpdateRequest",
        'AutopilotUpdateRequest(title="Nightly")',
        (
            "title",
            "agent",
            "priority",
            "status",
            "execution_mode",
            "description",
            "project_id",
            "issue_title_template",
            "subscribers",
        ),
        (),
    ),
    MigrationInventoryCase(
        "AutopilotTriggerCreate",
        'AutopilotTriggerCreate(title="Daily", kind="schedule")',
        ("title", "kind"),
        ("title", "kind"),
    ),
    MigrationInventoryCase(
        "AutopilotTriggerUpdate",
        'AutopilotTriggerUpdate(kind="schedule")',
        ("title", "kind"),
        (),
    ),
    MigrationInventoryCase(
        "RuntimeUpdate",
        'RuntimeUpdate(target_version="stable")',
        ("target_version", "wait"),
        ("target_version",),
    ),
    MigrationInventoryCase(
        "UserProfileUpdate",
        'UserProfileUpdate(description="On call")',
        ("description",),
        (),
    ),
)

_MIGRATION_ROW_PATTERN = re.compile(r"^\| `(?P<before>[^`]+)` \| `(?P<after>[^`]+)` \|$")


def _direct_migration_rows(path: Path) -> tuple[tuple[str, str], ...]:
    heading = (
        "### Removed one-operation DTOs: direct typed calls"
        if path.name == "migration.md"
        else "### Breaking before/after inventory"
    )
    section = path.read_text().split(heading, 1)[1]
    terminator = "Each `After` call" if path.name == "migration.md" else "The same import move"
    section = section.split(terminator, 1)[0]
    return tuple(
        (match.group("before"), match.group("after"))
        for line in section.splitlines()
        if (match := _MIGRATION_ROW_PATTERN.match(line)) is not None
    )


def _assert_legacy_schema(case: MigrationInventoryCase) -> None:
    expression = ast.parse(case.before, mode="eval").body
    assert isinstance(expression, ast.Call)
    assert isinstance(expression.func, ast.Name)
    assert expression.func.id == case.dto
    assert not expression.args
    field_names = tuple(keyword.arg for keyword in expression.keywords)
    assert all(field_name is not None for field_name in field_names)
    assert len(field_names) == len(set(field_names))
    assert set(field_names) <= set(case.legacy_fields)
    assert set(case.required_fields) <= set(field_names)


def test_migration_inventory_is_fail_closed_against_legacy_schema() -> None:
    assert {case.dto for case in MIGRATION_INVENTORY} == set(REMOVED_DTO_NAMES)
    for case in MIGRATION_INVENTORY:
        _assert_legacy_schema(case)
    documented_after = tuple(
        case.snippet for case in AFTER_EXAMPLES if case.documents == _MIGRATION_AND_CHANGELOG
    )
    assert len(documented_after) == len(MIGRATION_INVENTORY)
    expected_rows = tuple(
        (case.before, after)
        for case, after in zip(MIGRATION_INVENTORY, documented_after, strict=True)
    )
    assert len(expected_rows) == len(set(expected_rows))
    for path in (ROOT / "docs/migration.md", ROOT / "CHANGELOG.md"):
        assert _direct_migration_rows(path) == expected_rows


def test_public_docs_and_examples_have_no_deleted_surface_terms() -> None:
    paths = [ROOT / "README.md", ROOT / "docs/api.md", ROOT / "docs/service-usage.md"]
    paths.extend((ROOT / "examples").glob("*.py"))
    documents = "\n".join(path.read_text() for path in paths)
    forbidden = (*REMOVED_DTO_NAMES, "IssueSummary", "request-object", "request object")
    assert not any(term in documents for term in forbidden)


def test_documented_advanced_import_locations_are_real() -> None:
    from multica_py.models.autopilots import AutopilotListPage, AutopilotRunListPage
    from multica_py.models.common import CommentCursor
    from multica_py.models.issue_activity import MetadataPage
    from multica_py.models.issues import (
        FileDescription,
        InlineDescription,
        IssueChildrenResult,
        IssueDescriptionInput,
        IssueListFilter,
        IssueListPage,
        NoDescription,
    )
    from multica_py.models.project_resources import LocalDirectoryResourceRef, ProjectResourceRecord
    from multica_py.models.relations import (
        CursorLazyCollection,
        CursorPage,
        LazyCollection,
        LazyMapping,
        OffsetLazyCollection,
        OffsetPage,
        RelationMetadata,
    )
    from multica_py.models.system import RuntimeUpdateResult
    from multica_py.resources.cli import CliResult
    from multica_py.types import JsonValue

    # Import statements above are the assertion: a documented location that
    # disappears or moves makes this contract test fail during collection.


@dataclass(frozen=True)
class AfterExample:
    snippet: str
    method: object
    target: Callable[[MulticaClient], object]
    args: tuple[object, ...]
    kwargs: tuple[tuple[str, object], ...]
    documents: tuple[Path, ...]
    expects_command: bool = True


class _Invokable(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> object: ...


def _example_id(case: object) -> str:
    assert isinstance(case, AfterExample)
    return case.snippet


def _issue(client: MulticaClient) -> Issue:
    return Issue(id="issue_id", title="Issue", status=IssueStatus.todo, _client=client)


def _project(client: MulticaClient) -> Project:
    return Project(id="project_id", name="Project", status=ProjectStatus.planned, _client=client)


def _project_issues(client: MulticaClient) -> ProjectIssueCollection:
    return _project(client).issues


_MIGRATION = ROOT / "docs/migration.md"
_CHANGELOG = ROOT / "CHANGELOG.md"
_MIGRATION_AND_CHANGELOG = (_MIGRATION, _CHANGELOG)
_MIGRATION_ONLY = (_MIGRATION,)


def _build_command(case: AfterExample, target: object) -> object:
    method = cast("_Invokable", case.method)
    if not case.expects_command:
        return method(target, *case.args, **dict(case.kwargs))
    method_name = cast("str", getattr(case.method, "__name__"))
    builder = cast("_Invokable", getattr(target, f"{method_name}_command"))
    return builder(*case.args, **dict(case.kwargs))


AFTER_EXAMPLES = (
    AfterExample(
        'client.agents.create(name="build")',
        AgentResource.create,
        lambda client: client.agents,
        (),
        (("name", "build"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.agents.update(agent_id, name="build")',
        AgentResource.update,
        lambda client: client.agents,
        ("agent_id",),
        (("name", "build"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.projects.create(name="alpha")',
        ProjectResource.create,
        lambda client: client.projects,
        (),
        (("name", "alpha"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.projects.update(project_id, name="alpha")',
        ProjectResource.update,
        lambda client: client.projects,
        ("project_id",),
        (("name", "alpha"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.skills.create(name="lint")',
        SkillResource.create,
        lambda client: client.skills,
        (),
        (("name", "lint"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.skills.update(skill_id, name="lint")',
        SkillResource.update,
        lambda client: client.skills,
        ("skill_id",),
        (("name", "lint"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.labels.update(label_id, name="ready")',
        LabelResource.update,
        lambda client: client.labels,
        ("label_id",),
        (("name", "ready"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.issues.create(title="Deploy")',
        IssueResource.create,
        lambda client: client.issues,
        (),
        (("title", "Deploy"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.issues.update(issue_id, description="Ready")',
        IssueResource.update,
        lambda client: client.issues,
        ("issue_id",),
        (("description", "Ready"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        "client.issues.assign(issue_id, member_id)",
        IssueResource.assign,
        lambda client: client.issues,
        ("issue_id", "member_id"),
        (),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        "client.issues.assign(issue_id, agent_id)",
        IssueResource.assign,
        lambda client: client.issues,
        ("issue_id", "agent_id"),
        (),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        "client.issues.reorder(issue_id, before_id=target_id)",
        IssueResource.reorder,
        lambda client: client.issues,
        ("issue_id",),
        (("before_id", "target_id"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        "client.issues.comments.list_flat(issue_id=issue_id, since=since)",
        IssueCommentResource.list_flat,
        lambda client: client.issues.comments,
        (),
        (
            ("issue_id", "issue_id"),
            ("since", datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)),
        ),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        "client.issues.comments.list_recent(issue_id=issue_id, limit=20)",
        IssueCommentResource.list_recent,
        lambda client: client.issues.comments,
        (),
        (("issue_id", "issue_id"), ("limit", 20)),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        "client.issues.comments.list_thread(issue_id=issue_id, thread_id=thread_id, cursor=cursor, limit=50)",
        IssueCommentResource.list_thread,
        lambda client: client.issues.comments,
        (),
        (
            ("issue_id", "issue_id"),
            ("thread_id", "thread_id"),
            ("cursor", CommentCursor(before="before", before_id="before_id")),
            ("limit", 50),
        ),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        "client.issues.metadata.query(issue_id=issue_id, predicates=predicates, cursor=cursor, limit=limit)",
        IssueMetadataResource.query,
        lambda client: client.issues.metadata,
        (),
        (
            ("issue_id", "issue_id"),
            ("predicates", (MetadataPredicate(key="priority", value="high"),)),
            ("cursor", "cursor"),
            ("limit", 50),
        ),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'issue.set_metadata("build.id", "42")',
        Issue.set_metadata,
        _issue,
        ("build.id", "42"),
        (),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        "project.add_local_directory(local_path=path, daemon_id=daemon_id)",
        Project.add_local_directory,
        _project,
        (),
        (("local_path", "/repo"), ("daemon_id", "daemon_id")),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        "client.projects.resources.update_local_directory(project_id, resource_id, local_path=path)",
        ProjectResourceCollection.update_local_directory,
        lambda client: client.projects.resources,
        ("project_id", "resource_id"),
        (("local_path", "/repo"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.autopilots.update(autopilot_id, title="Nightly")',
        AutopilotResource.update,
        lambda client: client.autopilots,
        ("autopilot_id",),
        (("title", "Nightly"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.autopilots.trigger_add(autopilot_id, title="Daily", kind="schedule")',
        AutopilotResource.trigger_add,
        lambda client: client.autopilots,
        ("autopilot_id",),
        (("title", "Daily"), ("kind", "schedule")),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.autopilots.trigger_update(autopilot_id, trigger_id, kind="schedule")',
        AutopilotResource.trigger_update,
        lambda client: client.autopilots,
        ("autopilot_id", "trigger_id"),
        (("kind", "schedule"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.runtimes.update(runtime_id, target_version="stable")',
        RuntimeResource.update,
        lambda client: client.runtimes,
        ("runtime_id",),
        (("target_version", "stable"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.users.profile_update(description="On call")',
        UserResource.profile_update,
        lambda client: client.users,
        (),
        (("description", "On call"),),
        _MIGRATION_AND_CHANGELOG,
    ),
    AfterExample(
        'client.cli.command("issue", "get", issue_id, options=options)',
        CliResource.command,
        lambda client: client.cli,
        ("issue", "get", "issue_id"),
        (("options", OperationOptions()),),
        _MIGRATION_ONLY,
    ),
    AfterExample(
        "issue.permalink()",
        Issue.permalink,
        _issue,
        (),
        (),
        _MIGRATION_ONLY,
        expects_command=False,
    ),
    AfterExample(
        'client.projects.get(project_id).issues.create(title="Deploy")',
        ProjectIssueCollection.create,
        _project_issues,
        (),
        (("title", "Deploy"),),
        _MIGRATION_ONLY,
    ),
    AfterExample(
        "attachments.upload(payload, filename=filename)",
        AttachmentResource.upload,
        lambda client: client.attachments,
        (b"payload",),
        (("filename", "payload.bin"),),
        _MIGRATION_ONLY,
    ),
    AfterExample(
        "client.agents.copy(source_agent_id, runtime_id=runtime_id)",
        AgentResource.copy,
        lambda client: client.agents,
        ("source_agent_id",),
        (("runtime_id", "runtime_id"),),
        _MIGRATION_ONLY,
    ),
)


@pytest.mark.parametrize("case", AFTER_EXAMPLES, ids=_example_id)
def test_migration_after_examples_are_signature_checked_and_constructible(
    case: AfterExample,
) -> None:
    for path in case.documents:
        text = path.read_text()
        assert case.snippet in text

    client = MulticaClient(ClientConfig(app_url="https://app.example", workspace_slug="workspace"))
    try:
        target = case.target(client)
        assert inspect.isfunction(case.method)
        inspect.signature(case.method).bind(target, *case.args, **dict(case.kwargs))
        built = _build_command(case, target)
        if case.expects_command:
            assert hasattr(built, "commands")
        else:
            assert isinstance(built, str)
    finally:
        client._transport.close()


CONSUMER_DOCUMENTATION_CASES = (
    DocumentationCase(ROOT / "docs/service-usage.md", "Iterator[Issue]"),
    DocumentationCase(
        ROOT / "docs/service-usage.md", "client.projects.get(project_id).issues.all()"
    ),
    DocumentationCase(ROOT / "examples/issue_queue.py", 'IssueMetadataItem(key="external_key"'),
    DocumentationCase(ROOT / "examples/issue_queue.py", "issue.label_names"),
    DocumentationCase(ROOT / "examples/issue_queue.py", "issue.metadata_snapshot"),
)


@pytest.mark.parametrize(
    "case",
    CONSUMER_DOCUMENTATION_CASES,
    ids=tuple(case.required_text for case in CONSUMER_DOCUMENTATION_CASES),
)
def test_consumer_examples_use_bound_issue_read_paths(case: DocumentationCase) -> None:
    assert case.required_text in case.path.read_text()


EXAMPLE_CASES = (
    "workspace.members",
    "workspace.issues.page",
    "project.resources",
    "agent.skills",
    "skill.files",
    "squad.members",
    "issue.comments",
    "recent_comment_threads",
    "run.messages",
    "autopilot.runs",
    "client.prefetch",
    "triggers.loaded",
    "issue.to_dict",
)


@pytest.mark.parametrize("required_text", EXAMPLE_CASES)
def test_graph_example_covers_required_load_points(required_text: str) -> None:
    example = (ROOT / "examples/resource_relations.py").read_text()
    assert required_text in example
