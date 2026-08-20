"""Contracts for the canonical entity package relocation."""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import multica_py
import multica_py.entities as entities
import multica_py.models as models
from multica_py.entities._base import _BoundEntity
from multica_py.resources.agents import Agent as ResourceAgent
from multica_py.resources.autopilots import Autopilot, AutopilotRun
from multica_py.resources.issue_comments import Comment as ResourceComment
from multica_py.resources.issue_comments import CommentThread as ResourceCommentThread
from multica_py.resources.issues import Issue as ResourceIssue
from multica_py.resources.issues import TaskRun as ResourceTaskRun
from multica_py.resources.labels import Label as ResourceLabel
from multica_py.resources.projects import Project as ResourceProject
from multica_py.resources.skills import Skill as ResourceSkill
from multica_py.resources.squads import Squad as ResourceSquad
from multica_py.resources.workspaces import Workspace, WorkspaceMember

CANONICAL = {
    "Agent": ("multica_py.entities.agents", ResourceAgent),
    "Autopilot": ("multica_py.entities.autopilots", Autopilot),
    "AutopilotRun": ("multica_py.entities.autopilots", AutopilotRun),
    "Comment": ("multica_py.entities.comments", ResourceComment),
    "CommentThread": ("multica_py.entities.comments", ResourceCommentThread),
    "Issue": ("multica_py.entities.issues", ResourceIssue),
    "Label": ("multica_py.entities.labels", ResourceLabel),
    "Project": ("multica_py.entities.projects", ResourceProject),
    "Skill": ("multica_py.entities.skills", ResourceSkill),
    "Squad": ("multica_py.entities.squads", ResourceSquad),
    "TaskRun": ("multica_py.entities.issues", ResourceTaskRun),
    "Workspace": ("multica_py.entities.workspaces", Workspace),
    "WorkspaceMember": ("multica_py.entities.workspaces", WorkspaceMember),
}


def test_block_two_entities_have_canonical_identity_and_modules() -> None:
    for name, (module_name, resource_alias) in CANONICAL.items():
        entity = cast("type[object]", getattr(entities, name))
        assert entity.__module__ == module_name
        assert entity is resource_alias
        assert entity is cast("type[object]", getattr(multica_py, name))
        assert issubclass(entity, _BoundEntity)


def test_entities_package_inventory_remains_exact() -> None:
    assert entities.__all__ == [
        "Agent",
        "Autopilot",
        "AutopilotRun",
        "Comment",
        "CommentThread",
        "Issue",
        "Label",
        "Project",
        "Skill",
        "Squad",
        "TaskRun",
        "Workspace",
        "WorkspaceMember",
    ]
    assert "_BoundEntity" not in entities.__all__


def test_private_bound_base_has_no_legacy_module_or_public_export() -> None:
    assert not hasattr(models, "_BoundEntity")
    assert not (Path(__file__).parents[2] / "src/multica_py/models/_bound.py").exists()


def test_entity_policy_has_no_legacy_declarations_or_replacement_registry() -> None:
    root = Path(__file__).parents[2] / "src" / "multica_py" / "entities"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))

    for legacy_name in ("_PUBLIC_FIELDS", "_RUNTIME_FIELDS", "_RUNTIME_INIT_FIELDS"):
        assert legacy_name not in source
    assert "metaclass=" not in source
    assert "__init_subclass__" not in source


def test_entity_modules_do_not_import_resources_or_build_command_plans() -> None:
    root = Path(__file__).parents[2] / "src" / "multica_py" / "entities"
    for filename in (path.name for path in root.glob("*.py")):
        tree = ast.parse((root / filename).read_text(encoding="utf-8"))
        source = (root / filename).read_text(encoding="utf-8")
        assert "multica_py.resources" not in source
        assert "multica_py._internal.transport" not in source
        assert "decode_json" not in source
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"_map", "_plan", "_replace_plan"}
            for node in ast.walk(tree)
        )


def test_relation_module_does_not_own_command_plan_internals() -> None:
    relation_path = Path(__file__).parents[2] / "src" / "multica_py" / "models" / "relations.py"
    tree = ast.parse(relation_path.read_text(encoding="utf-8"))
    forbidden = {"_CommandPlan", "_Step", "_StepRef", "_replace_plan"}

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "multica_py._internal.commands":
            assert not forbidden.intersection(alias.name for alias in node.names)
        if isinstance(node, ast.Attribute):
            assert node.attr not in forbidden | {"_plan"}
        if isinstance(node, ast.Name):
            assert node.id not in forbidden


def _package_modules(package_name: str) -> tuple[str, ...]:
    package = importlib.import_module(package_name)
    return tuple(
        sorted(
            module.name for module in pkgutil.walk_packages(package.__path__, f"{package_name}.")
        )
    )


def test_no_bound_entity_definitions_remain_in_resources_or_models() -> None:
    for package_name in ("multica_py.resources", "multica_py.models"):
        for module_name in _package_modules(package_name):
            module = importlib.import_module(module_name)
            defined_classes_list: list[type[object]] = []
            for value in cast("dict[str, object]", vars(module)).values():
                if not inspect.isclass(value):
                    continue
                defined_class = cast("type[object]", value)
                if defined_class.__module__ == module_name:
                    defined_classes_list.append(defined_class)
            defined_classes = tuple(defined_classes_list)
            assert all(
                value is not _BoundEntity and not issubclass(value, _BoundEntity)
                for value in defined_classes
            ), module_name


RESOURCE_ADAPTERS = {
    "multica_py.resources.agents.AgentResource": (
        "_skills_relation_command",
        "_tasks_relation_command",
        "_set_skills_command",
    ),
    "multica_py.resources.autopilots.AutopilotResource": (
        "_relation_command",
        "_runs_page_command",
        "_trigger_add_command",
        "_trigger_update_command",
        "_trigger_delete_command",
    ),
    "multica_py.resources.issue_comments.IssueCommentResource": (
        "_thread_page_command",
        "_recent_threads_page_command",
    ),
    "multica_py.resources.issues.IssueResource": (
        "_comments_relation_command",
        "_recent_comment_threads_relation_command",
        "_labels_relation_command",
        "_subscribers_relation_command",
        "_metadata_relation_command",
        "_properties_relation_command",
        "_children_relation_command",
        "_runs_relation_command",
        "_run_messages_relation_command",
        "_add_comment_command",
        "_reply_command",
        "_add_label_command",
        "_remove_label_command",
        "_add_subscriber_command",
        "_remove_subscriber_command",
        "_set_metadata_command",
        "_delete_metadata_command",
        "_offset_page",
        "_offset_page_command",
    ),
    "multica_py.resources.projects.ProjectResource": (
        "_issues_relation",
        "_resources_relation_command",
        "_add_local_directory_command",
        "_remove_resource_command",
    ),
    "multica_py.resources.squads.SquadResource": (
        "_members_relation_command",
        "_issues_page_command",
        "_add_member_command",
        "_remove_member_command",
    ),
    "multica_py.resources.skills.SkillResource": (
        "_files_relation_command",
        "_upsert_file_command",
        "_delete_file_command",
    ),
    "multica_py.resources.workspaces.WorkspaceResource": (
        "_members_relation_command",
        "_agents_relation_command",
        "_skills_relation_command",
        "_projects_relation_command",
        "_labels_relation_command",
        "_repositories_relation_command",
        "_runtimes_relation_command",
        "_squads_relation_command",
        "_issues_page_command",
        "_autopilots_relation_command",
        "_plugins_relation_command",
        "_properties_relation_command",
        "_mcp_servers_relation_command",
    ),
}


def test_command_and_wire_adapters_are_private_on_owning_resources() -> None:
    for qualified_name, adapter_names in RESOURCE_ADAPTERS.items():
        module_name, class_name = qualified_name.rsplit(".", 1)
        resource_class = cast(
            "type[object]", getattr(importlib.import_module(module_name), class_name)
        )
        for adapter_name in adapter_names:
            adapter = cast("object | None", getattr(resource_class, adapter_name, None))
            assert adapter is not None, qualified_name
            assert adapter_name.startswith("_")
            assert callable(adapter), (qualified_name, adapter_name)
            resource_exports = cast(
                "tuple[str, ...]",
                cast("dict[str, object]", vars(resource_class)).get("__all__", ()),
            )
            assert adapter_name not in resource_exports


def test_resource_entity_imports_use_canonical_entity_modules() -> None:
    entity_names = set(CANONICAL)
    for module_name in _package_modules("multica_py.resources"):
        module = importlib.import_module(module_name)
        module_file = module.__file__
        assert module_file is not None
        tree = ast.parse(Path(module_file).read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if not node.module.startswith("multica_py.resources."):
                continue
            imported_names = {alias.name for alias in node.names}
            assert not imported_names & entity_names, (module_name, node.module)


def test_entity_and_resource_modules_import_in_fresh_interpreters() -> None:
    modules = (
        _package_modules("multica_py.entities")
        + _package_modules("multica_py.resources")
        + (
            "multica_py._internal.wire_models",
            "multica_py._internal.decoders",
        )
    )
    for module in modules:
        result = subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
