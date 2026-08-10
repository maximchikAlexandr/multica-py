from __future__ import annotations

import os
import pathlib
from typing import cast

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
from multica_py.config import OperationOptions
from multica_py.models.common import ActionResult, Page
from multica_py.models.project_resources import ProjectResourceRecord
from multica_py.resources._base import BaseResource


class ProjectResourceCollection(BaseResource):
    def list_command(
        self, project_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[ProjectResourceRecord]]:
        _ = cast("object", PROJECT_RESOURCE_LIST_BINDING)
        return self._decoded_page_command(
            ("project", "resource", "list", project_id),
            _ProjectResourceRecordWire,
            options=options,
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

    def list(
        self, project_id: str, *, options: OperationOptions | None = None
    ) -> Page[ProjectResourceRecord]:
        return self.list_command(project_id, options=options).run()

    def add_local_directory(
        self,
        project_id: str,
        *,
        local_path: str | pathlib.Path,
        daemon_id: str,
        label: str | None = None,
        options: OperationOptions | None = None,
    ) -> ProjectResourceRecord:
        return self.add_local_directory_command(
            project_id,
            local_path=local_path,
            daemon_id=daemon_id,
            label=label,
            options=options,
        ).run()

    def add_local_directory_command(
        self,
        project_id: str,
        *,
        local_path: str | pathlib.Path,
        daemon_id: str,
        label: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[ProjectResourceRecord]:
        _ = cast("object", PROJECT_RESOURCE_ADD_BINDING)
        validate_nonblank(project_id)
        if not daemon_id.strip():
            raise ValueError("daemon_id must be non-empty")
        if local_path is None or not str(local_path).strip():
            raise ValueError("local_path must be non-empty")
        local_path = os.path.abspath(local_path)
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
            daemon_id,
        ]
        if label is not None and label.strip():
            args.extend(["--ref-label", label])

        return self._decoded_command(tuple(args), _ProjectResourceRecordWire, options=options)._map(
            project_resource_from_wire
        )

    def update_local_directory(
        self,
        project_id: str,
        resource_id: str,
        *,
        local_path: str | pathlib.Path,
        options: OperationOptions | None = None,
    ) -> ProjectResourceRecord:
        return self.update_local_directory_command(
            project_id, resource_id, local_path=local_path, options=options
        ).run()

    def update_local_directory_command(
        self,
        project_id: str,
        resource_id: str,
        *,
        local_path: str | pathlib.Path,
        options: OperationOptions | None = None,
    ) -> Command[ProjectResourceRecord]:
        _ = cast("object", PROJECT_RESOURCE_UPDATE_BINDING)
        validate_nonblank(project_id)
        validate_nonblank(resource_id)
        if local_path is None:
            raise TypeError("local_path must be non-null")
        if not str(local_path).strip():
            raise ValueError("local_path must be non-empty")
        local_path = os.path.abspath(local_path)
        args = [
            "project",
            "resource",
            "update",
            project_id,
            resource_id,
            "--local-path",
            local_path,
        ]

        return self._decoded_command(tuple(args), _ProjectResourceRecordWire, options=options)._map(
            project_resource_from_wire
        )

    def remove_command(
        self, project_id: str, resource_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        _ = cast("object", PROJECT_RESOURCE_REMOVE_BINDING)
        validate_nonblank(project_id)
        validate_nonblank(resource_id)
        return self._action_command(
            ("project", "resource", "remove", project_id, resource_id), options=options
        )

    def remove(
        self, project_id: str, resource_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.remove_command(project_id, resource_id, options=options).run()
