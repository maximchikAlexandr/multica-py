from __future__ import annotations

import os
import pathlib
from collections.abc import Mapping
from typing import cast

import msgspec

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
from multica_py.sentinels import Unset, UnsetType


class ProjectResourceCollection(BaseResource):
    def add_command(
        self,
        project_id: str,
        *,
        resource_type: str = "local_directory",
        local_path: str | pathlib.Path | None = None,
        daemon_id: str | None = None,
        url: str | None = None,
        default_branch_hint: str | None = None,
        ref: Mapping[str, object] | str | None = None,
        label: str | None = None,
        execution_mode: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[ProjectResourceRecord]:
        return self.add_local_directory_command(
            project_id,
            resource_type=resource_type,
            local_path=local_path,
            daemon_id=daemon_id,
            url=url,
            default_branch_hint=default_branch_hint,
            ref=ref,
            label=label,
            execution_mode=execution_mode,
            options=options,
        )

    def add(self, project_id: str, **kwargs: object) -> ProjectResourceRecord:
        return self.add_command(project_id, **kwargs).run()  # type: ignore[arg-type]

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
        local_path: str | pathlib.Path | None = None,
        daemon_id: str | None = None,
        label: str | None = None,
        resource_type: str = "local_directory",
        url: str | None = None,
        default_branch_hint: str | None = None,
        ref: Mapping[str, object] | str | None = None,
        execution_mode: str | None = None,
        options: OperationOptions | None = None,
    ) -> ProjectResourceRecord:
        return self.add_local_directory_command(
            project_id,
            local_path=local_path,
            daemon_id=daemon_id,
            label=label,
            resource_type=resource_type,
            url=url,
            default_branch_hint=default_branch_hint,
            ref=ref,
            execution_mode=execution_mode,
            options=options,
        ).run()

    def add_local_directory_command(
        self,
        project_id: str,
        *,
        local_path: str | pathlib.Path | None = None,
        daemon_id: str | None = None,
        label: str | None = None,
        resource_type: str = "local_directory",
        url: str | None = None,
        default_branch_hint: str | None = None,
        ref: Mapping[str, object] | str | None = None,
        execution_mode: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[ProjectResourceRecord]:
        _ = cast("object", PROJECT_RESOURCE_ADD_BINDING)
        validate_nonblank(project_id)
        if not resource_type.strip():
            raise ValueError("resource_type must be non-empty")
        args = ["project", "resource", "add", project_id, "--type", resource_type]
        if local_path is not None:
            if not str(local_path).strip():
                raise ValueError("local_path must be non-empty")
            args.extend(("--local-path", os.path.abspath(local_path)))
        if daemon_id is not None:
            if not daemon_id.strip():
                raise ValueError("daemon_id must be non-empty")
            args.extend(("--daemon-id", daemon_id))
        if resource_type == "local_directory" and (local_path is None or daemon_id is None):
            raise ValueError("local_directory requires local_path and daemon_id")
        if url is not None:
            if not url.strip():
                raise ValueError("url must be non-empty")
            args.extend(("--url", url))
        if default_branch_hint is not None:
            if not default_branch_hint.strip():
                raise ValueError("default_branch_hint must be non-empty")
            args.extend(("--default-branch-hint", default_branch_hint))
        if ref is not None:
            encoded_ref = ref if isinstance(ref, str) else msgspec.json.encode(ref).decode()
            if not encoded_ref.strip():
                raise ValueError("ref must be non-empty")
            args.extend(("--ref", encoded_ref))
        if execution_mode is not None:
            if not execution_mode.strip():
                raise ValueError("execution_mode must be non-empty")
            args.extend(("--execution-mode", execution_mode))
        if label is not None:
            if not label.strip():
                raise ValueError("label must be non-empty")
            args.extend(("--ref-label" if resource_type == "local_directory" else "--label", label))
        return self._decoded_command(tuple(args), _ProjectResourceRecordWire, options=options)._map(
            project_resource_from_wire
        )

    def update_local_directory(
        self,
        project_id: str,
        resource_id: str,
        *,
        local_path: str | pathlib.Path | None = None,
        url: str | None = None,
        default_branch_hint: str | None = None,
        daemon_id: str | None = None,
        ref_label: str | None = None,
        execution_mode: str | None = None,
        ref: Mapping[str, object] | str | None = None,
        label: str | None | UnsetType = Unset,
        clear_label: bool = False,
        position: int | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> ProjectResourceRecord:
        return self.update_local_directory_command(
            project_id,
            resource_id,
            local_path=local_path,
            url=url,
            default_branch_hint=default_branch_hint,
            daemon_id=daemon_id,
            ref_label=ref_label,
            execution_mode=execution_mode,
            ref=ref,
            label=label,
            clear_label=clear_label,
            position=position,
            options=options,
        ).run()

    def update_local_directory_command(
        self,
        project_id: str,
        resource_id: str,
        *,
        local_path: str | pathlib.Path | None = None,
        url: str | None = None,
        default_branch_hint: str | None = None,
        daemon_id: str | None = None,
        ref_label: str | None = None,
        execution_mode: str | None = None,
        ref: Mapping[str, object] | str | None = None,
        label: str | None | UnsetType = Unset,
        clear_label: bool = False,
        position: int | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[ProjectResourceRecord]:
        _ = cast("object", PROJECT_RESOURCE_UPDATE_BINDING)
        validate_nonblank(project_id)
        validate_nonblank(resource_id)
        args = ["project", "resource", "update", project_id, resource_id]
        if local_path is not None:
            if not str(local_path).strip():
                raise ValueError("local_path must be non-empty")
            args.extend(("--local-path", os.path.abspath(local_path)))
        if url is not None:
            if not url.strip():
                raise ValueError("url must be non-empty")
            args.extend(("--url", url))
        if default_branch_hint is not None:
            args.extend(("--default-branch-hint", default_branch_hint))
        if daemon_id is not None:
            if not daemon_id.strip():
                raise ValueError("daemon_id must be non-empty")
            args.extend(("--daemon-id", daemon_id))
        if ref_label is not None:
            args.extend(("--ref-label", ref_label))
        if execution_mode is not None:
            args.extend(("--execution-mode", execution_mode))
        if ref is not None:
            args.extend(
                ("--ref", ref if isinstance(ref, str) else msgspec.json.encode(ref).decode())
            )
        if clear_label:
            args.append("--clear-label")
        elif label is not Unset:
            args.extend(("--label", "" if label is None else label))
        if position is not Unset:
            if position is None:
                raise ValueError("position cannot be null")
            args.extend(("--position", str(position)))
        if len(args) == 5:
            raise ValueError("at least one project resource field is required")
        return self._decoded_command(tuple(args), _ProjectResourceRecordWire, options=options)._map(
            project_resource_from_wire
        )

    def update_command(
        self, project_id: str, resource_id: str, **kwargs: object
    ) -> Command[ProjectResourceRecord]:
        return self.update_local_directory_command(
            project_id,
            resource_id,
            **kwargs,  # type: ignore[arg-type]
        )

    def update(self, project_id: str, resource_id: str, **kwargs: object) -> ProjectResourceRecord:
        return self.update_command(project_id, resource_id, **kwargs).run()

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
