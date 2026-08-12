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
    return cast("object", getattr(import_module(f"multica_py.entities.{module_name}"), name))
