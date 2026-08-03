from __future__ import annotations

import os
import pathlib
from typing import overload

from multica_py._generated.approved_sdk import (
    PROJECT_RESOURCE_ADD_BINDING,
    PROJECT_RESOURCE_LIST_BINDING,
    PROJECT_RESOURCE_REMOVE_BINDING,
    PROJECT_RESOURCE_UPDATE_BINDING,
    validate_nonblank,
)
from multica_py._internal.wire_models import (
    ProjectResourceRecordWire,
    project_resource_from_wire,
)
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceRecord,
    ProjectResourceUpdateLocalDirectoryRequest,
)
from multica_py.resources._base import BaseResource, _resolve_request


class ProjectResourceCollection(BaseResource):
    def list(self, project_id: str) -> tuple[ProjectResourceRecord, ...]:
        _ = PROJECT_RESOURCE_LIST_BINDING
        return tuple(
            project_resource_from_wire(item)
            for item in self._run_json_decode_list(
                ("project", "resource", "list", project_id),
                ProjectResourceRecordWire,
            )
        )

    @overload
    def add_local_directory(
        self,
        project_id: str,
        request: ProjectResourceAddLocalDirectoryRequest,
        /,
    ) -> ProjectResourceRecord: ...
    @overload
    def add_local_directory(
        self,
        project_id: str,
        *,
        local_path: str | pathlib.Path,
        daemon_id: str,
        label: str | None = None,
    ) -> ProjectResourceRecord: ...

    def add_local_directory(  # type: ignore[misc]
        self,
        project_id: str,
        request: ProjectResourceAddLocalDirectoryRequest | None = None,
        /,
        **kwargs: object,
    ) -> ProjectResourceRecord:
        _ = PROJECT_RESOURCE_ADD_BINDING
        validate_nonblank(project_id)
        req = _resolve_request(request, kwargs, ProjectResourceAddLocalDirectoryRequest)
        validate_nonblank(req.daemon_id)
        local_path = os.path.abspath(req.local_path)
        args = [
            "project",
            "resource",
            "add",
            project_id,
            "--type",
            "local_directory",
            "--local-path",
            local_path,
            "--daemon-id",
            req.daemon_id,
        ]
        if req.label is not None and req.label.strip():
            args.extend(["--ref-label", req.label])
        return project_resource_from_wire(
            self._run_json_decode(tuple(args), ProjectResourceRecordWire)
        )

    @overload
    def update_local_directory(
        self,
        project_id: str,
        resource_id: str,
        request: ProjectResourceUpdateLocalDirectoryRequest,
        /,
    ) -> ProjectResourceRecord: ...
    @overload
    def update_local_directory(
        self,
        project_id: str,
        resource_id: str,
        *,
        local_path: str | pathlib.Path,
    ) -> ProjectResourceRecord: ...

    def update_local_directory(  # type: ignore[misc]
        self,
        project_id: str,
        resource_id: str,
        request: ProjectResourceUpdateLocalDirectoryRequest | None = None,
        /,
        **kwargs: object,
    ) -> ProjectResourceRecord:
        _ = PROJECT_RESOURCE_UPDATE_BINDING
        validate_nonblank(project_id)
        validate_nonblank(resource_id)
        req = _resolve_request(request, kwargs, ProjectResourceUpdateLocalDirectoryRequest)
        local_path = os.path.abspath(req.local_path)
        args = [
            "project",
            "resource",
            "update",
            project_id,
            resource_id,
            "--local-path",
            local_path,
        ]
        return project_resource_from_wire(
            self._run_json_decode(tuple(args), ProjectResourceRecordWire)
        )

    def remove(self, project_id: str, resource_id: str) -> None:
        _ = PROJECT_RESOURCE_REMOVE_BINDING
        validate_nonblank(project_id)
        validate_nonblank(resource_id)
        self._transport.run_text(("project", "resource", "remove", project_id, resource_id))
