from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]


@dataclass(frozen=True)
class DocumentationCase:
    path: Path
    required_text: str


MIGRATION_CASES = (
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
    DocumentationCase(ROOT / "docs/migration.md", "only new public type is"),
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
