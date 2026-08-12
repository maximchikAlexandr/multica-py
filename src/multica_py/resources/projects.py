from __future__ import annotations

import os
import pathlib
from collections.abc import Callable

from multica_py._generated.approved_sdk import (
    validate_nonblank,
)
from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _project_from_wire,
    _ProjectWire,
)
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities import projects as _project_entities
from multica_py.entities.issues import Issue
from multica_py.entities.projects import Project
from multica_py.enums import ProjectStatus
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import (
    IssueDescriptionInput,
    IssueListFilter,
)
from multica_py.models.project_resources import ProjectResourceRecord
from multica_py.models.relations import OffsetLazyCollection, OffsetPage
from multica_py.resources._base import (
    BaseResource,
    _normalize_description_file,
    _validate_optional_string,
)
from multica_py.resources.issues import IssueResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.sentinels import Unset, UnsetType

__all__ = ["Project", "ProjectIssueCollection", "ProjectResource"]


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
            return issues._offset_page(
                IssueListFilter(project_id=project_id, limit=limit, offset=offset)
            )

        super().__init__(
            page_loader,
            page_command_loader=lambda limit, offset: issues._offset_page_command(
                IssueListFilter(project_id=project_id, limit=limit, offset=offset)
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


class ProjectResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.resources = ProjectResourceCollection(transport, config)

    def _issues_relation(self, project: Project) -> ProjectIssueCollection:
        return ProjectIssueCollection(project, self._bound_client().issues)

    def _resources_relation_command(
        self, project_id: str
    ) -> Command[tuple[ProjectResourceRecord, ...]]:
        return self.resources.list_command(project_id)._map(lambda page: tuple(page.items))

    def _add_local_directory_command(
        self,
        project_id: str,
        *,
        local_path: str | pathlib.Path,
        daemon_id: str,
        label: str | None,
        invalidate: Callable[[ProjectResourceRecord], ProjectResourceRecord],
        options: OperationOptions | None,
    ) -> Command[ProjectResourceRecord]:
        return self.resources.add_local_directory_command(
            project_id,
            local_path=local_path,
            daemon_id=daemon_id,
            label=label,
            options=options,
        )._map(invalidate)

    def _remove_resource_command(
        self,
        project_id: str,
        resource_id: str,
        *,
        invalidate: Callable[[ActionResult[None]], ActionResult[None]],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        return self.resources.remove_command(project_id, resource_id, options=options)._map(
            invalidate
        )

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


# Preserve the historical concrete relation annotation without making the
# canonical entity module import its owning resource.
setattr(_project_entities, "ProjectIssueCollection", ProjectIssueCollection)
