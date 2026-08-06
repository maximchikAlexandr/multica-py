from __future__ import annotations

from typing import cast, overload

import msgspec

from multica_py._generated.approved_sdk import (
    validate_nonblank,
)
from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _project_from_wire,
    _ProjectWire,
)
from multica_py.config import ClientConfig
from multica_py.enums import ProjectStatus
from multica_py.exceptions import ValidationError
from multica_py.models._bound import _BoundEntity
from multica_py.models.issues import IssueListFilter, IssueSummary
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceRecord,
)
from multica_py.models.projects import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
)
from multica_py.models.relations import LazyCollection, OffsetLazyCollection, OffsetPage
from multica_py.resources._base import BaseResource, _resolve_request
from multica_py.resources.issues import (
    IssueResource,
    _issue_summary_offset_page,
    _issue_summary_offset_page_command,
)
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.sentinels import Unset, UnsetType


class Project(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    status: ProjectStatus
    description: str | None = None

    _resources: LazyCollection[ProjectResourceRecord] | None = msgspec.field(
        default=None, name="_resources"
    )
    _issues: OffsetLazyCollection[IssueSummary] | None = msgspec.field(default=None, name="_issues")

    _PUBLIC_FIELDS = ("id", "name", "description", "status")

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
                    lambda: resources.list(pid),
                    command_loader=lambda: resources.list_command(pid),
                ),
            )
        return self._resources  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            issues = self._require_client(
                entity_type="Project", entity_id=self.id, relation_name="issues"
            ).issues
            pid = self.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:
                return self._page_issues(issues, pid, limit, offset)

            self._set_runtime(
                "_issues",
                OffsetLazyCollection(
                    page_loader,
                    page_command_loader=lambda limit, offset: _issue_summary_offset_page_command(
                        issues,
                        IssueListFilter(project_id=pid, limit=limit, offset=offset),
                    ),
                ),
            )
        return self._issues  # type: ignore[return-value]

    def _page_issues(
        self, issues: IssueResource, pid: str, limit: int | None, offset: int
    ) -> OffsetPage[IssueSummary]:
        flt = IssueListFilter(project_id=pid, limit=limit, offset=offset)
        return _issue_summary_offset_page(issues, flt)

    def _invalidate_resources(self) -> None:
        if self._resources is not None:
            self._resources.invalidate()

    def add_local_directory(
        self, request: ProjectResourceAddLocalDirectoryRequest
    ) -> ProjectResourceRecord:
        return self.add_local_directory_command(request).run()

    def add_local_directory_command(
        self, request: ProjectResourceAddLocalDirectoryRequest
    ) -> Command[ProjectResourceRecord]:
        client = self._require_client(
            entity_type="Project", entity_id=self.id, relation_name="add_local_directory"
        )
        command = client.projects.resources.add_local_directory_command(self.id, request)

        def invalidate(result: ProjectResourceRecord) -> ProjectResourceRecord:
            self._invalidate_resources()
            return result

        return command._map(invalidate)

    def remove_resource(self, resource_id: str) -> None:
        self.remove_resource_command(resource_id).run()

    def remove_resource_command(self, resource_id: str) -> Command[None]:
        validate_nonblank(self.id)
        validate_nonblank(resource_id)
        client = self._require_client(
            entity_type="Project", entity_id=self.id, relation_name="remove_resource"
        )
        return client.projects.resources.remove_command(self.id, resource_id)._map(
            lambda result: self._invalidate_resources()
        )


class ProjectResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.resources = ProjectResourceCollection(transport, config)

    def _bind(self, project: _ProjectWire) -> Project:
        return _project_from_wire(project)._with_client(self._client)

    def list_command(self) -> Command[tuple[Project, ...]]:
        return self._decoded_list_command(("project", "list"), _ProjectWire)._map(
            lambda projects: tuple(map(self._bind, projects))
        )

    def list(self) -> tuple[Project, ...]:
        return self.list_command().run()

    def get_command(self, project_id: str) -> Command[Project]:
        return self._decoded_command(("project", "get", project_id), _ProjectWire)._map(self._bind)

    def get(self, project_id: str) -> Project:
        return self.get_command(project_id).run()

    @overload
    def create_command(self, request: ProjectCreateRequest, /) -> Command[Project]: ...
    @overload
    def create_command(self, *, name: str, description: str | None = None) -> Command[Project]: ...

    def create_command(  # type: ignore[misc]
        self, request: ProjectCreateRequest | None = None, /, **kwargs: object
    ) -> Command[Project]:
        req = _resolve_request(request, kwargs, ProjectCreateRequest)
        validate_nonblank(req.name)
        args = ["project", "create", "--title", req.name]
        if req.description is not None:
            args.extend(["--description", req.description])
        return self._decoded_command(tuple(args), _ProjectWire)._map(self._bind)

    @overload
    def create(self, request: ProjectCreateRequest, /) -> Project: ...
    @overload
    def create(self, *, name: str, description: str | None = None) -> Project: ...

    def create(  # type: ignore[misc]
        self, request: ProjectCreateRequest | None = None, /, **kwargs: object
    ) -> Project:
        return self.create_command(cast("ProjectCreateRequest", request), **kwargs).run()

    @overload
    def update_command(
        self, project_id: str, request: ProjectUpdateRequest, /
    ) -> Command[Project]: ...
    @overload
    def update_command(
        self,
        project_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
    ) -> Command[Project]: ...

    def update_command(  # type: ignore[misc]
        self, project_id: str, request: ProjectUpdateRequest | None = None, /, **kwargs: object
    ) -> Command[Project]:
        req = _resolve_request(request, kwargs, ProjectUpdateRequest)
        args = ["project", "update", project_id]
        if req.name is not Unset:
            args.extend(["--title", req.name])
        if req.description is Unset:
            pass
        elif req.description is None:
            raise ValidationError("description=None is not supported for project update via CLI")
        else:
            args.extend(["--description", req.description])
        return self._decoded_command(tuple(args), _ProjectWire)._map(self._bind)

    @overload
    def update(self, project_id: str, request: ProjectUpdateRequest, /) -> Project: ...
    @overload
    def update(
        self,
        project_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
    ) -> Project: ...

    def update(  # type: ignore[misc]
        self, project_id: str, request: ProjectUpdateRequest | None = None, /, **kwargs: object
    ) -> Project:
        return self.update_command(
            project_id, cast("ProjectUpdateRequest", request), **kwargs
        ).run()

    def delete_command(self, project_id: str) -> Command[None]:
        return self._none_command(("project", "delete", project_id))

    def delete(self, project_id: str) -> None:
        self.delete_command(project_id).run()

    def set_status_command(self, project_id: str, status: ProjectStatus) -> Command[Project]:
        return self._decoded_command(
            ("project", "status", project_id, status.value), _ProjectWire
        )._map(self._bind)

    def set_status(self, project_id: str, status: ProjectStatus) -> Project:
        return self.set_status_command(project_id, status).run()
