from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING, cast

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py._internal.permalinks import build_permalink
from multica_py.config import OperationOptions
from multica_py.entities._base import _BoundEntity
from multica_py.entities.issues import Issue
from multica_py.enums import ProjectStatus
from multica_py.models.common import ActionResult
from multica_py.models.project_resources import ProjectResourceRecord
from multica_py.models.relations import LazyCollection, OffsetLazyCollection
from multica_py.sentinels import Unset, UnsetType

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


# The concrete collection remains resource-owned.  The resource module replaces
# this typing fallback after defining its compatibility-exported collection.
ProjectIssueCollection = OffsetLazyCollection[Issue]


class Project(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    status: ProjectStatus
    description: str | None = None

    _resources: LazyCollection[ProjectResourceRecord] | None = msgspec.field(
        default=None, name="_resources"
    )
    _issues: ProjectIssueCollection | None = msgspec.field(default=None, name="_issues")

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
            client = self._require_client(
                entity_type="Project", entity_id=self.id, relation_name="resources"
            )
            resources = client.projects.resources
            pid = self.id
            self._set_runtime(
                "_resources",
                LazyCollection(
                    lambda: resources.list(pid).items,
                    command_loader=lambda: client.projects._resources_relation_command(pid),
                ),
            )
        return self._resources  # type: ignore[return-value]

    @property
    def issues(self) -> ProjectIssueCollection:
        if self._issues is None:
            client = self._require_client(
                entity_type="Project", entity_id=self.id, relation_name="issues"
            )
            self._set_runtime("_issues", client.projects._issues_relation(self))
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

        def invalidate(result: ProjectResourceRecord) -> ProjectResourceRecord:
            self._invalidate_resources()
            return result

        return client.projects._add_local_directory_command(
            self.id,
            local_path=local_path,
            daemon_id=daemon_id,
            label=label,
            invalidate=invalidate,
            options=options,
        )

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

        return client.projects._remove_resource_command(
            self.id, resource_id, invalidate=invalidate, options=options
        )
