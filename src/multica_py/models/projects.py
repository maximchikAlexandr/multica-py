from __future__ import annotations

import msgspec

from multica_py.enums import ProjectStatus
from multica_py.sentinels import Unset, UnsetType


class Project(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None
    status: ProjectStatus


class ProjectCreateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    description: str | None = None


class ProjectUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str | UnsetType = Unset
    description: str | None | UnsetType = Unset
