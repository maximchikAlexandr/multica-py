from __future__ import annotations

import typing
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

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
        ROOT / "docs/migration.md", "Direct issue lists and the five list-backed relations"
    ),
    DocumentationCase(ROOT / "docs/migration.md", "Workspace.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "Project.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "Agent.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "Squad.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "WorkspaceMember.issues"),
    DocumentationCase(ROOT / "docs/migration.md", "issues.get(summary.id)"),
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
    DocumentationCase(
        ROOT / "docs/service-usage.md", "## Direct keywords, typed objects, and presence"
    ),
    DocumentationCase(ROOT / "docs/service-usage.md", "mutation.value.added"),
    DocumentationCase(ROOT / "README.md", "client.issues.list(status=IssueStatus.backlog"),
    DocumentationCase(ROOT / "README.md", "ActionResult[T]"),
    DocumentationCase(ROOT / "docs/migration.md", "### Breaking return matrix"),
    DocumentationCase(
        ROOT / "docs/migration.md", "Relation `.all()` snapshots are explicitly unchanged"
    ),
    DocumentationCase(ROOT / "CHANGELOG.md", "## Unreleased — unified SDK operation contracts"),
    DocumentationCase(ROOT / "CHANGELOG.md", "Repository mutations"),
    DocumentationCase(ROOT / "examples/issue_queue.py", "yield from page.items"),
    DocumentationCase(ROOT / "examples/self_hosted_local.py", "client.projects.list().items"),
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
    assert "Page[T]" in api and "Page[IssueSummary]" in service

    action_return = return_annotation(cast("object", getattr(AutopilotResource, "delete")))
    assert cast("object", typing.get_origin(action_return)) is ActionResult
    assert "ActionResult[None]" in api


def test_docs_do_not_reintroduce_legacy_request_or_result_conventions() -> None:
    documents = "\n".join(
        (ROOT / relative).read_text()
        for relative in ("docs/api.md", "docs/service-usage.md", "README.md", "docs/migration.md")
    )
    forbidden = (
        "The request-object form is the only option",
        "returns `tuple[IssueSummary, ...]`",
        "returns `Command[tuple[IssueSummary, ...]]`",
        "Use `entity.to_data()`",
    )
    assert not any(phrase in documents for phrase in forbidden)


CONSUMER_DOCUMENTATION_CASES = (
    DocumentationCase(ROOT / "docs/service-usage.md", "Iterator[IssueSummary]"),
    DocumentationCase(
        ROOT / "docs/service-usage.md", "client.projects.get(project_id).issues.all()"
    ),
    DocumentationCase(ROOT / "examples/issue_queue.py", 'IssueMetadataItem(key="external_key"'),
    DocumentationCase(ROOT / "examples/issue_queue.py", "summary.label_names"),
    DocumentationCase(ROOT / "examples/issue_queue.py", "summary.metadata_snapshot"),
)


@pytest.mark.parametrize(
    "case",
    CONSUMER_DOCUMENTATION_CASES,
    ids=tuple(case.required_text for case in CONSUMER_DOCUMENTATION_CASES),
)
def test_consumer_examples_use_summary_read_paths(case: DocumentationCase) -> None:
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
