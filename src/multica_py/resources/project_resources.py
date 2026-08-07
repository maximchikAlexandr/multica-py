from __future__ import annotations

import os
import pathlib
from typing import cast, overload

from multica_py._generated.approved_sdk import (
    PROJECT_RESOURCE_ADD_BINDING,
    PROJECT_RESOURCE_LIST_BINDING,
    PROJECT_RESOURCE_REMOVE_BINDING,
    PROJECT_RESOURCE_UPDATE_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command
from multica_py._internal.wire_models import (
    _ProjectResourceRecordWire,
    project_resource_from_wire,
)
from multica_py.models.common import ActionResult, Page
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceRecord,
    ProjectResourceUpdateLocalDirectoryRequest,
)
from multica_py.resources._base import BaseResource, _resolve_request


class ProjectResourceCollection(BaseResource):
    def list_command(self, project_id: str) -> Command[Page[ProjectResourceRecord]]:
        _ = cast("object", PROJECT_RESOURCE_LIST_BINDING)
        return self._decoded_page_command(
            ("project", "resource", "list", project_id), _ProjectResourceRecordWire
        )._map(
            lambda page: Page(
                items=tuple(project_resource_from_wire(item) for item in page.items),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(self, project_id: str) -> Page[ProjectResourceRecord]:
        return self.list_command(project_id).run()

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
        return self.add_local_directory_command(
            project_id, cast("ProjectResourceAddLocalDirectoryRequest", request), **kwargs
        ).run()

    @overload
    def add_local_directory_command(
        self,
        project_id: str,
        request: ProjectResourceAddLocalDirectoryRequest,
        /,
    ) -> Command[ProjectResourceRecord]: ...
    @overload
    def add_local_directory_command(
        self,
        project_id: str,
        *,
        local_path: str | pathlib.Path,
        daemon_id: str,
        label: str | None = None,
    ) -> Command[ProjectResourceRecord]: ...

    def add_local_directory_command(  # type: ignore[misc]
        self,
        project_id: str,
        request: ProjectResourceAddLocalDirectoryRequest | None = None,
        /,
        **kwargs: object,
    ) -> Command[ProjectResourceRecord]:
        _ = cast("object", PROJECT_RESOURCE_ADD_BINDING)
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

        return self._decoded_command(tuple(args), _ProjectResourceRecordWire)._map(
            project_resource_from_wire
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
        return self.update_local_directory_command(
            project_id,
            resource_id,
            cast("ProjectResourceUpdateLocalDirectoryRequest", request),
            **kwargs,
        ).run()

    @overload
    def update_local_directory_command(
        self,
        project_id: str,
        resource_id: str,
        request: ProjectResourceUpdateLocalDirectoryRequest,
        /,
    ) -> Command[ProjectResourceRecord]: ...
    @overload
    def update_local_directory_command(
        self,
        project_id: str,
        resource_id: str,
        *,
        local_path: str | pathlib.Path,
    ) -> Command[ProjectResourceRecord]: ...

    def update_local_directory_command(  # type: ignore[misc]
        self,
        project_id: str,
        resource_id: str,
        request: ProjectResourceUpdateLocalDirectoryRequest | None = None,
        /,
        **kwargs: object,
    ) -> Command[ProjectResourceRecord]:
        _ = cast("object", PROJECT_RESOURCE_UPDATE_BINDING)
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

        return self._decoded_command(tuple(args), _ProjectResourceRecordWire)._map(
            project_resource_from_wire
        )

    def remove_command(self, project_id: str, resource_id: str) -> Command[ActionResult[None]]:
        _ = cast("object", PROJECT_RESOURCE_REMOVE_BINDING)
        validate_nonblank(project_id)
        validate_nonblank(resource_id)
        return self._action_command(("project", "resource", "remove", project_id, resource_id))

    def remove(self, project_id: str, resource_id: str) -> ActionResult[None]:
        return self.remove_command(project_id, resource_id).run()
