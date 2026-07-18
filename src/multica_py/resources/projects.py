from __future__ import annotations

from multica_py.enums import ProjectStatus
from multica_py.exceptions import ValidationError
from multica_py.models.projects import Project, ProjectCreateRequest, ProjectUpdateRequest
from multica_py.resources._base import BaseResource
from multica_py.sentinels import Unset


class ProjectResource(BaseResource):
    def list(self) -> tuple[Project, ...]:
        return self._run_json_decode_list(("project", "list"), Project)

    def get(self, project_id: str) -> Project:
        return self._run_json_decode(("project", "get", project_id), Project)

    def create(self, request: ProjectCreateRequest) -> Project:
        args = ["project", "create", "--title", request.name]
        if request.description is not None:
            args.extend(["--description", request.description])
        return self._run_json_decode(tuple(args), Project)

    def update(self, project_id: str, request: ProjectUpdateRequest) -> Project:
        args = ["project", "update", project_id]
        if request.name is not Unset:
            args.extend(["--title", request.name])
        if request.description is Unset:
            pass
        elif request.description is None:
            raise ValidationError(
                "description=None is not supported for project update via CLI"
            )
        else:
            args.extend(["--description", request.description])
        return self._run_json_decode(tuple(args), Project)

    def delete(self, project_id: str) -> None:
        self._transport.run_text(("project", "delete", project_id))

    def set_status(self, project_id: str, status: ProjectStatus) -> Project:
        return self._run_json_decode(
            ("project", "set-status", project_id, "--status", status.value), Project
        )
