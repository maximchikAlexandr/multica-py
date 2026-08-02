from __future__ import annotations

from typing import TYPE_CHECKING

from multica_py._generated.approved_sdk import (
    PROJECT_CREATE_BINDING,
    PROJECT_STATUS_BINDING,
    PROJECT_UPDATE_BINDING,
    validate_nonblank,
)
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import ProjectWire, project_from_wire
from multica_py.config import ClientConfig
from multica_py.enums import ProjectStatus
from multica_py.exceptions import ValidationError
from multica_py.models import ResourceEntity
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceRecord,
)
from multica_py.models.projects import (
    Project as ProjectRecord,
)
from multica_py.models.projects import (
    ProjectCreateRequest,
    ProjectData,
    ProjectUpdateRequest,
)
from multica_py.models.relations import LazyCollection, OffsetLazyCollection, OffsetPage
from multica_py.resources._base import BaseResource
from multica_py.resources.issues import IssueEntity, IssueResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.sentinels import Unset

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


class Project(ResourceEntity[ProjectData]):
    def __init__(self, data: ProjectData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)
        self._resources: LazyCollection[ProjectResourceRecord] | None = None
        self._issues: OffsetLazyCollection[IssueEntity] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def name(self) -> str:
        return self._data.name

    @property
    def description(self) -> str | None:
        return self._data.description

    @property
    def status(self) -> ProjectStatus:
        return self._data.status

    @property
    def resources(self) -> LazyCollection[ProjectResourceRecord]:
        if self._resources is None:
            resources = self._require_client(
                entity_type="Project", entity_id=self._data.id, relation_name="resources"
            ).projects.resources
            pid = self._data.id
            self._resources = LazyCollection(lambda: resources.list(pid))
        return self._resources

    @property
    def issues(self) -> OffsetLazyCollection[IssueEntity]:
        if self._issues is None:
            issues = self._require_client(
                entity_type="Project", entity_id=self._data.id, relation_name="issues"
            ).issues
            pid = self._data.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueEntity]:
                return self._page_issues(issues, pid, limit, offset)

            self._issues = OffsetLazyCollection(page_loader)
        return self._issues

    def _page_issues(
        self, issues: IssueResource, pid: str, limit: int | None, offset: int
    ) -> OffsetPage[IssueEntity]:
        from multica_py.models.issues import IssueListFilter
        from multica_py.resources.issues import _issue_data_from_summary

        flt = IssueListFilter(project_id=pid, limit=limit, offset=offset)
        page = issues.list(flt)
        return OffsetPage(
            items=tuple(
                item
                if isinstance(item, IssueEntity)
                else IssueEntity(_issue_data_from_summary(item), client=self._client)
                for item in page.issues
            ),
            total=page.total or 0,
            limit=page.limit or 50,
            offset=page.offset or 0,
            has_more=page.has_more,
        )

    def _invalidate_resources(self) -> None:
        if self._resources is not None:
            self._resources.invalidate()

    def add_local_directory(
        self, request: ProjectResourceAddLocalDirectoryRequest
    ) -> ProjectResourceRecord:
        client = self._require_client(
            entity_type="Project", entity_id=self.id, relation_name="add_local_directory"
        )
        result = client.projects.resources.add_local_directory(self.id, request)
        self._invalidate_resources()
        return result

    def remove_resource(self, resource_id: str) -> None:
        validate_nonblank(resource_id)
        client = self._require_client(
            entity_type="Project", entity_id=self.id, relation_name="remove_resource"
        )
        client.projects.resources.remove(self.id, resource_id)
        self._invalidate_resources()


class ProjectResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.resources = ProjectResourceCollection(transport, config)

    def list(self) -> tuple[Project, ...]:
        return tuple(
            self._bind_project(project_from_wire(item))
            for item in self._run_json_decode_list(("project", "list"), ProjectWire)
        )

    def get(self, project_id: str) -> Project:
        return self._bind_project(
            project_from_wire(self._run_json_decode(("project", "get", project_id), ProjectWire))
        )

    def create(self, request: ProjectCreateRequest) -> Project:
        _ = PROJECT_CREATE_BINDING
        validate_nonblank(request.name)
        args = ["project", "create", "--title", request.name]
        if request.description is not None:
            args.extend(["--description", request.description])
        return self._bind_project(
            project_from_wire(self._run_json_decode(tuple(args), ProjectWire))
        )

    def update(self, project_id: str, request: ProjectUpdateRequest) -> Project:
        _ = PROJECT_UPDATE_BINDING
        args = ["project", "update", project_id]
        if request.name is not Unset:
            args.extend(["--title", request.name])
        if request.description is Unset:
            pass
        elif request.description is None:
            raise ValidationError("description=None is not supported for project update via CLI")
        else:
            args.extend(["--description", request.description])
        return self._bind_project(
            project_from_wire(self._run_json_decode(tuple(args), ProjectWire))
        )

    def delete(self, project_id: str) -> None:
        self._transport.run_text(("project", "delete", project_id))

    def set_status(self, project_id: str, status: ProjectStatus) -> Project:
        _ = PROJECT_STATUS_BINDING
        return self._bind_project(
            project_from_wire(
                self._run_json_decode(("project", "status", project_id, status.value), ProjectWire)
            )
        )

    def _bind_project(self, project: ProjectRecord) -> Project:
        return Project(
            ProjectData(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
            ),
            client=self._client,
        )
