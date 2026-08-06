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
from multica_py._internal.commands import Command, _Step
from multica_py._internal.wire_models import (
    _ProjectResourceRecordWire,
    project_resource_from_wire,
)
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceRecord,
    ProjectResourceUpdateLocalDirectoryRequest,
)
from multica_py.resources._base import BaseResource, _resolve_request


class ProjectResourceCollection(BaseResource):
    def list_command(self, project_id: str) -> Command[tuple[ProjectResourceRecord, ...]]:
        _ = cast("object", PROJECT_RESOURCE_LIST_BINDING)
        args, decode = self._plan_decode_list(
            ("project", "resource", "list", project_id), _ProjectResourceRecordWire
        )

        def finalize(results: tuple[object, ...]) -> tuple[ProjectResourceRecord, ...]:
            items = cast("tuple[_ProjectResourceRecordWire, ...]", results[0])
            return tuple(project_resource_from_wire(item) for item in items)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def list(self, project_id: str) -> tuple[ProjectResourceRecord, ...]:
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

        plan_args, decode = self._plan_decode(tuple(args), _ProjectResourceRecordWire)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: project_resource_from_wire(
                cast("_ProjectResourceRecordWire", results[0])
            ),
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

        plan_args, decode = self._plan_decode(tuple(args), _ProjectResourceRecordWire)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: project_resource_from_wire(
                cast("_ProjectResourceRecordWire", results[0])
            ),
        )

    def remove_command(self, project_id: str, resource_id: str) -> Command[None]:
        _ = cast("object", PROJECT_RESOURCE_REMOVE_BINDING)
        validate_nonblank(project_id)
        validate_nonblank(resource_id)
        return self._plan(
            steps=(_Step(("project", "resource", "remove", project_id, resource_id), "run_text"),),
            finalize=lambda results: None,
        )

    def remove(self, project_id: str, resource_id: str) -> None:
        self.remove_command(project_id, resource_id).run()
