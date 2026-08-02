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
    DocumentationCase(ROOT / "docs/migration.md", "AgentData.skill_refs"),
    DocumentationCase(ROOT / "docs/migration.md", "agent skills list/set"),
    DocumentationCase(ROOT / "docs/migration.md", "Skill.files"),
    DocumentationCase(ROOT / "docs/migration.md", "IssueData.label_names"),
    DocumentationCase(ROOT / "docs/migration.md", "IssueData.child_stages"),
    DocumentationCase(ROOT / "docs/migration.md", "IssueData.metadata_snapshot"),
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
)


@pytest.mark.parametrize(
    "case", MIGRATION_CASES, ids=tuple(case.required_text for case in MIGRATION_CASES)
)
def test_migration_table_covers_required_surface(case: DocumentationCase) -> None:
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
    "issue.to_data",
)


@pytest.mark.parametrize("required_text", EXAMPLE_CASES)
def test_graph_example_covers_required_load_points(required_text: str) -> None:
    example = (ROOT / "examples/resource_relations.py").read_text()
    assert required_text in example
