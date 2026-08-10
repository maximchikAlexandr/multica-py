from __future__ import annotations

import pathlib

import msgspec


class LocalDirectoryResourceRef(msgspec.Struct, frozen=True, kw_only=True):
    local_path: str
    daemon_id: str
    label: str | None = None

    def __post_init__(self) -> None:
        if not self.daemon_id.strip():
            raise ValueError("daemon_id must be non-empty")
        if not pathlib.Path(self.local_path).is_absolute():
            raise ValueError("local_path must be an absolute path")


class ProjectResourceRecord(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    project_id: str
    resource_type: str
    resource_ref: LocalDirectoryResourceRef

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.project_id.strip():
            raise ValueError("project_id must be non-empty")
