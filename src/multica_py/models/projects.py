from __future__ import annotations

import msgspec

from multica_py.enums import ProjectStatus


class Project(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None
    status: ProjectStatus


class ProjectCreateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    description: str | None = None


class ProjectUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str | None = None
    description: str | None = None
