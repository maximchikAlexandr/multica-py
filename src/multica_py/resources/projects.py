from __future__ import annotations

import os
import pathlib
from typing import TYPE_CHECKING, cast

import msgspec

from multica_py._generated.approved_sdk import (
    validate_nonblank,
)
from multica_py._internal.commands import Command
from multica_py._internal.permalinks import build_permalink
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _project_from_wire,
    _ProjectWire,
)
from multica_py.config import ClientConfig, OperationOptions
from multica_py.enums import ProjectStatus
from multica_py.models._bound import _BoundEntity
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import (
    IssueDescriptionInput,
    IssueListFilter,
)
from multica_py.models.project_resources import ProjectResourceRecord
from multica_py.models.relations import LazyCollection, OffsetLazyCollection, OffsetPage
from multica_py.resources._base import (
    BaseResource,
    _normalize_description_file,
    _page_items,
    _validate_optional_string,
)
from multica_py.resources.issues import (
    Issue,
    IssueResource,
    _issue_offset_page,
    _issue_offset_page_command,
)
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.sentinels import Unset, UnsetType

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


def _normalize_project_status(value: ProjectStatus | str) -> ProjectStatus:
    if isinstance(value, ProjectStatus):
        return value
    if type(value) is str:
        return ProjectStatus(value)
    raise TypeError("status must be a ProjectStatus or exact status string")


class ProjectIssueCollection(OffsetLazyCollection[Issue]):
    """Issue relation scoped to one bound project.

    The relation delegates creation to the root issue resource so it keeps the
    root validation, command plan and result binding.  Only a successful
    result invalidates this collection's cached read snapshot.
    """

    def __init__(self, project: Project, issues: IssueResource) -> None:
        project_id = project.id

        def page_loader(*, limit: int | None, offset: int) -> OffsetPage[Issue]:
            return _issue_offset_page(
                issues,
                IssueListFilter(project_id=project_id, limit=limit, offset=offset),
            )

        super().__init__(
            page_loader,
            page_command_loader=lambda limit, offset: _issue_offset_page_command(
                issues,
                IssueListFilter(project_id=project_id, limit=limit, offset=offset),
            ),
        )
        self._project_id = project_id
        self._issues = issues

    def create_command(
        self,
        *,
        title: str,
        description: str | None = None,
        description_file: str | os.PathLike[str] | None = None,
        description_input: IssueDescriptionInput | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        label_ids: tuple[str, ...] = (),
        parent_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        command = self._issues.create_command(
            title=title,
            description=description,
            description_file=description_file,
            description_input=description_input,
            priority=priority,
            assignee_id=assignee_id,
            label_ids=label_ids,
            project_id=self._project_id,
            parent_id=parent_id,
            options=options,
        )

        def invalidate(result: Issue) -> Issue:
            self.invalidate()
            return result

        return command._map(invalidate)

    def create(
        self,
        *,
        title: str,
        description: str | None = None,
        description_file: str | os.PathLike[str] | None = None,
        description_input: IssueDescriptionInput | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        label_ids: tuple[str, ...] = (),
        parent_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.create_command(
            title=title,
            description=description,
            description_file=description_file,
            description_input=description_input,
            priority=priority,
            assignee_id=assignee_id,
            label_ids=label_ids,
            parent_id=parent_id,
            options=options,
        ).run()


class Project(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    status: ProjectStatus
    description: str | None = None

    _resources: LazyCollection[ProjectResourceRecord] | None = msgspec.field(
        default=None, name="_resources"
    )
    _issues: ProjectIssueCollection | None = msgspec.field(default=None, name="_issues")

    _PUBLIC_FIELDS = ("id", "name", "description", "status")

    def permalink(self) -> str:
        client = cast("MulticaClient | None", self._client)
        return build_permalink(
            entity_type="Project",
            entity_id=self.id,
            collection="projects",
            app_url=client.config.app_url if client is not None else None,
            workspace_slug=client.config.workspace_slug if client is not None else None,
        )

    @property
    def resources(self) -> LazyCollection[ProjectResourceRecord]:
        if self._resources is None:
            resources = self._require_client(
                entity_type="Project", entity_id=self.id, relation_name="resources"
            ).projects.resources
            pid = self.id
            self._set_runtime(
                "_resources",
                LazyCollection(
                    lambda: _page_items(resources.list(pid)),
                    command_loader=lambda: resources.list_command(pid)._map(_page_items),
                ),
            )
        return self._resources  # type: ignore[return-value]

    @property
    def issues(self) -> ProjectIssueCollection:
        if self._issues is None:
            issues = self._require_client(
                entity_type="Project", entity_id=self.id, relation_name="issues"
            ).issues
            self._set_runtime("_issues", ProjectIssueCollection(self, issues))
        return self._issues  # type: ignore[return-value]

    def refresh_command(self, *, options: OperationOptions | None = None) -> Command[Project]:
        client = self._require_client(
            entity_type="Project", entity_id=self.id, relation_name="refresh"
        )
        return client.projects.get_command(self.id, options=options)

    def refresh(self, *, options: OperationOptions | None = None) -> Project:
        return self.refresh_command(options=options).run()

    def update_command(
        self,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Project]:
        client = self._require_client(
            entity_type="Project", entity_id=self.id, relation_name="update"
        )
        return client.projects.update_command(
            self.id,
            name=name,
            description=description,
            options=options,
        )

    def update(
        self,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Project:
        return self.update_command(
            name=name,
            description=description,
            options=options,
        ).run()

    def _invalidate_resources(self) -> None:
        if self._resources is not None:
            self._resources.invalidate()

    def add_local_directory(
        self,
        *,
        local_path: str | pathlib.Path,
        daemon_id: str,
        label: str | None = None,
        options: OperationOptions | None = None,
    ) -> ProjectResourceRecord:
        return self.add_local_directory_command(
            local_path=local_path, daemon_id=daemon_id, label=label, options=options
        ).run()

    def add_local_directory_command(
        self,
        *,
        local_path: str | pathlib.Path,
        daemon_id: str,
        label: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[ProjectResourceRecord]:
        client = self._require_client(
            entity_type="Project", entity_id=self.id, relation_name="add_local_directory"
        )
        command = client.projects.resources.add_local_directory_command(
            self.id,
            local_path=local_path,
            daemon_id=daemon_id,
            label=label,
            options=options,
        )

        def invalidate(result: ProjectResourceRecord) -> ProjectResourceRecord:
            self._invalidate_resources()
            return result

        return command._map(invalidate)

    def remove_resource(
        self, resource_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.remove_resource_command(resource_id, options=options).run()

    def remove_resource_command(
        self, resource_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(self.id)
        validate_nonblank(resource_id)
        client = self._require_client(
            entity_type="Project", entity_id=self.id, relation_name="remove_resource"
        )

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_resources()
            return result

        command = client.projects.resources.remove_command(self.id, resource_id, options=options)
        return command._map(invalidate)


class ProjectResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.resources = ProjectResourceCollection(transport, config)

    def _bind(self, project: _ProjectWire) -> Project:
        return _project_from_wire(project)._with_client(self._client)

    def list_command(self, *, options: OperationOptions | None = None) -> Command[Page[Project]]:
        return self._decoded_page_command(("project", "list"), _ProjectWire, options=options)._map(
            lambda page: Page(
                items=tuple(map(self._bind, page.items)),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(self, *, options: OperationOptions | None = None) -> Page[Project]:
        return self.list_command(options=options).run()

    def get_command(
        self, project_id: str, *, options: OperationOptions | None = None
    ) -> Command[Project]:
        return self._decoded_command(
            ("project", "get", project_id), _ProjectWire, options=options
        )._map(self._bind)

    def get(self, project_id: str, *, options: OperationOptions | None = None) -> Project:
        return self.get_command(project_id, options=options).run()

    def create_command(
        self,
        *,
        name: str,
        description: str | None = None,
        description_file: str | os.PathLike[str] | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Project]:
        validate_nonblank(name)
        _validate_optional_string(description, "description")
        if description is not None and description_file is not None:
            raise TypeError("description and description_file are mutually exclusive")
        normalized_description_file = (
            _normalize_description_file(
                description_file,
                cwd=self._effective_config(options).cwd,
            )
            if description_file is not None
            else None
        )
        args = ["project", "create", "--title", name]
        if description is not None:
            args.extend(["--description", description])
        elif normalized_description_file is not None:
            args.extend(["--description-file", normalized_description_file])
        return self._decoded_command(tuple(args), _ProjectWire, options=options)._map(self._bind)

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        description_file: str | os.PathLike[str] | None = None,
        options: OperationOptions | None = None,
    ) -> Project:
        return self.create_command(
            name=name,
            description=description,
            description_file=description_file,
            options=options,
        ).run()

    def update_command(
        self,
        project_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Project]:
        validate_nonblank(project_id)
        if name is None:
            raise TypeError("name must be non-null")
        _validate_optional_string(name, "name")
        _validate_optional_string(description, "description")
        if name is Unset and description is Unset:
            return self.get_command(project_id, options=options)
        args = ["project", "update", project_id]
        if name is not Unset:
            args.extend(["--title", name])
        if description is Unset:
            pass
        elif description is None:
            args.extend(["--description", ""])
        else:
            args.extend(["--description", description])
        return self._decoded_command(tuple(args), _ProjectWire, options=options)._map(self._bind)

    def update(
        self,
        project_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Project:
        return self.update_command(
            project_id, name=name, description=description, options=options
        ).run()

    def delete_command(
        self, project_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("project", "delete", project_id), options=options)

    def delete(
        self, project_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(project_id, options=options).run()

    def set_status_command(
        self,
        project_id: str,
        status: ProjectStatus | str,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Project]:
        normalized_status = _normalize_project_status(status)
        return self._decoded_command(
            ("project", "status", project_id, normalized_status.value),
            _ProjectWire,
            options=options,
        )._map(self._bind)

    def set_status(
        self,
        project_id: str,
        status: ProjectStatus | str,
        *,
        options: OperationOptions | None = None,
    ) -> Project:
        return self.set_status_command(project_id, status, options=options).run()
