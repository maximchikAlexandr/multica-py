from importlib import import_module
from typing import TYPE_CHECKING, cast

__all__ = [
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

_MODULES = {
    "Agent": "agents",
    "Autopilot": "autopilots",
    "AutopilotRun": "autopilots",
    "Comment": "comments",
    "CommentThread": "comments",
    "Issue": "issues",
    "Label": "labels",
    "Project": "projects",
    "Skill": "skills",
    "Squad": "squads",
    "TaskRun": "issues",
    "Workspace": "workspaces",
    "WorkspaceMember": "workspaces",
}

if TYPE_CHECKING:
    from multica_py.entities.agents import Agent
    from multica_py.entities.autopilots import Autopilot, AutopilotRun
    from multica_py.entities.comments import Comment, CommentThread
    from multica_py.entities.issues import Issue, TaskRun
    from multica_py.entities.labels import Label
    from multica_py.entities.projects import Project
    from multica_py.entities.skills import Skill
    from multica_py.entities.squads import Squad
    from multica_py.entities.workspaces import Workspace, WorkspaceMember


def __getattr__(name: str) -> object:
    module_name = _MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = cast("object", getattr(import_module(f"multica_py.entities.{module_name}"), name))
    _sync_relation_type_names()
    return value


def _sync_relation_type_names() -> None:
    """Make circular relation annotations resolvable after lazy entity imports."""
    import sys

    modules = {
        name: sys.modules.get(f"multica_py.entities.{module_name}")
        for name, module_name in _MODULES.items()
    }
    for target_name in ("issues", "autopilots"):
        target = sys.modules.get(f"multica_py.entities.{target_name}")
        if target is None:
            continue
        target_vars = cast("dict[str, object]", vars(target))
        for name, module in modules.items():
            if module is not None and hasattr(module, name):
                target_vars.setdefault(name, cast("object", getattr(module, name)))
