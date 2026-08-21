from __future__ import annotations

import ast
from pathlib import Path

from multica_py.entities.autopilots import Autopilot, AutopilotRun
from multica_py.entities.issues import Issue, TaskRun

ROOT = Path(__file__).parents[2]
INVENTORY = (
    "Issue.parent",
    "Issue.project",
    "Issue.assignee_ref",
    "Autopilot.project",
    "Autopilot.assignee",
    "AutopilotRun.autopilot",
    "AutopilotRun.issue",
    "TaskRun.issue",
    "TaskRun.agent",
)
FORBIDDEN_LAZY_PROPERTIES = (
    "Issue.creator_ref",
    "Autopilot.trigger_ref",
    "TaskRun.task_ref",
    "Squad.leader_ref",
    "Comment.author_ref",
    "Workspace.user_ref",
    "Plugin.uploader_ref",
)
RESOLVED_INVENTORY = (
    (Issue, "parent"),
    (Issue, "project"),
    (Issue, "assignee_ref"),
    (Autopilot, "project"),
    (Autopilot, "assignee"),
    (AutopilotRun, "autopilot"),
    (AutopilotRun, "issue"),
    (TaskRun, "issue"),
    (TaskRun, "agent"),
)


def _docs() -> tuple[str, str, str]:
    api = (ROOT / "docs/api.md").read_text()
    service = (ROOT / "docs/service-usage.md").read_text()
    migration = (ROOT / "docs/migration.md").read_text()
    return api, service, migration


def test_singular_docs_pin_baseline_import_and_complete_inventory() -> None:
    api, service, migration = _docs()
    for document in (api, service, migration):
        assert "[0.4.28, 0.4.29)" in document
        assert "from multica_py.models.relations import LazyRef" in document
        assert all(member in document for member in INVENTORY)


def test_every_documented_reference_resolves_on_its_bound_entity() -> None:
    assert all(hasattr(owner, name) for owner, name in RESOLVED_INVENTORY)


def test_singular_docs_cover_passive_explicit_and_failure_semantics() -> None:
    api, service, migration = _docs()
    documents = api + service + migration
    for phrase in (
        "property access",
        "zero-I/O",
        "get()",
        "get_command().run()",
        "refresh()",
        "refresh_command().run()",
        "prefetch(",
        "max_parallel",
        "loaded optional `None`",
        "MissingRelationContextError",
        "UnloadedReferenceError",
        "DetachedEntityError",
        "UnsupportedReferenceTargetError",
        "immutable replacement",
        "Issue.assignee",
        "Issue.assignee_ref",
    ):
        assert phrase in documents
    assert "hidden workspace scan" in migration
    assert "workspace-member" in migration
    assert "email" in migration


def test_unsupported_singular_properties_are_not_documented_as_handles() -> None:
    documents = "\n".join(_docs())
    for property_name in FORBIDDEN_LAZY_PROPERTIES:
        assert property_name not in documents
    assert "creator/member" in documents
    assert "autopilot\ntrigger" in documents


def test_singular_example_uses_only_approved_imports_and_explicit_load_points() -> None:
    path = ROOT / "examples/singular_references.py"
    source = path.read_text()
    tree = ast.parse(source, filename=str(path))
    compile(source, str(path), "exec")

    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    lazy_imports = [node for node in imports if node.module and node.module.endswith("relations")]
    assert any(alias.name == "LazyRef" for node in lazy_imports for alias in node.names)
    assert not any(
        node.module in {"multica_py", "multica_py.models"}
        and any(alias.name == "LazyRef" for alias in node.names)
        for node in imports
    )

    assert "client.prefetch(" in source
    assert "max_parallel=2" in source
    assert ".value" in source
    assert ".refresh()" in source
    assert "client.cli.command" not in source
    assert "subprocess" not in source
    assert "sys.argv" not in source
    assert "raw argv" not in source.lower()
