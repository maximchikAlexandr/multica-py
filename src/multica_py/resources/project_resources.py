from __future__ import annotations

import pathlib

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
from multica_py.resources._base import BaseResource


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

    def add_local_directory(
        self,
        project_id: str,
        request: ProjectResourceAddLocalDirectoryRequest,
    ) -> ProjectResourceRecord:
        _ = PROJECT_RESOURCE_ADD_BINDING
        validate_nonblank(project_id)
        validate_nonblank(request.daemon_id)
        local_path = str(pathlib.Path(request.local_path).resolve())
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
            request.daemon_id,
        ]
        if request.label is not None and request.label.strip():
            args.extend(["--ref-label", request.label])
        return project_resource_from_wire(
            self._run_json_decode(tuple(args), ProjectResourceRecordWire)
        )

    def update_local_directory(
        self,
        project_id: str,
        resource_id: str,
        request: ProjectResourceUpdateLocalDirectoryRequest,
    ) -> ProjectResourceRecord:
        _ = PROJECT_RESOURCE_UPDATE_BINDING
        validate_nonblank(project_id)
        validate_nonblank(resource_id)
        local_path = str(pathlib.Path(request.local_path).resolve())
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
        self._transport.run_text(("project", "resource", "remove", project_id, resource_id))
