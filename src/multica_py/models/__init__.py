from typing import TYPE_CHECKING, Generic, Self, TypeVar

from multica_py.exceptions import DetachedEntityError

if TYPE_CHECKING:
    from multica_py.client import MulticaClient

from multica_py.models.agents import AgentData
from multica_py.models.autopilots import (
    AutopilotData,
    AutopilotRunData,
    AutopilotTriggerCreate,
    AutopilotTriggerUpdate,
)
from multica_py.models.issue_activity import CommentData, CommentThreadData, TaskRunData
from multica_py.models.issues import IssueChildrenResult, IssueData
from multica_py.models.labels import LabelData
from multica_py.models.project_resources import (
    LocalDirectoryResourceRef,
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceData,
    ProjectResourceRecord,
    ProjectResourceUpdateLocalDirectoryRequest,
)
from multica_py.models.projects import ProjectData
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    OffsetLazyCollection,
    OffsetPage,
    RelationMetadata,
)
from multica_py.models.skills import SkillData
from multica_py.models.system import SquadData, WorkspaceMemberData
from multica_py.models.workspaces import WorkspaceData

TData = TypeVar("TData")


class ResourceEntity(Generic[TData]):
    def __init__(self, data: TData, *, client: "MulticaClient | None" = None) -> None:
        self._data = data
        self._client = client

    def to_data(self) -> TData:
        return self._data

    @classmethod
    def from_data(cls, data: TData) -> Self:
        return cls(data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._data!r})"

    def _require_client(
        self, *, entity_type: str, entity_id: str, relation_name: str
    ) -> "MulticaClient":
        if self._client is None:
            raise DetachedEntityError(entity_type, entity_id, relation_name)
        return self._client


__all__ = [
    "AgentData",
    "AutopilotData",
    "AutopilotRunData",
    "AutopilotTriggerCreate",
    "AutopilotTriggerUpdate",
    "CommentData",
    "CommentThreadData",
    "CursorLazyCollection",
    "CursorPage",
    "IssueChildrenResult",
    "IssueData",
    "LabelData",
    "LazyCollection",
    "LazyMapping",
    "LocalDirectoryResourceRef",
    "OffsetLazyCollection",
    "OffsetPage",
    "ProjectData",
    "ProjectResourceAddLocalDirectoryRequest",
    "ProjectResourceData",
    "ProjectResourceRecord",
    "ProjectResourceUpdateLocalDirectoryRequest",
    "RelationMetadata",
    "ResourceEntity",
    "SkillData",
    "SquadData",
    "TaskRunData",
    "WorkspaceData",
    "WorkspaceMemberData",
]
