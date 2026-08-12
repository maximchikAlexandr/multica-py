from __future__ import annotations

from collections.abc import Callable

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.skills import Skill
from multica_py.models.common import ActionResult, Page
from multica_py.models.skills import SkillFile
from multica_py.resources._base import BaseResource, _page_items, _validate_optional_string
from multica_py.resources.skill_files import SkillFileResource
from multica_py.sentinels import Unset, UnsetType

__all__ = ["Skill", "SkillResource"]


class SkillResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.files = SkillFileResource(transport, config)

    def _files_relation_command(self, skill_id: str) -> Command[tuple[SkillFile, ...]]:
        return self.files.list_command(skill_id)._map(_page_items)

    def _upsert_file_command(
        self,
        skill_id: str,
        path: str,
        content: str,
        *,
        invalidate: Callable[[SkillFile], SkillFile],
        options: OperationOptions | None,
    ) -> Command[SkillFile]:
        return self.files.upsert_command(skill_id, path, content, options=options)._map(invalidate)

    def _delete_file_command(
        self,
        skill_id: str,
        file_id: str,
        *,
        invalidate: Callable[[ActionResult[None]], ActionResult[None]],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        return self.files.delete_command(skill_id, file_id, options=options)._map(invalidate)

    def list_command(self, *, options: OperationOptions | None = None) -> Command[Page[Skill]]:
        return self._decoded_page_command(("skill", "list"), Skill, options=options)._map(
            lambda page: Page(
                items=tuple(skill._with_client(self._client) for skill in page.items),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(self, *, options: OperationOptions | None = None) -> Page[Skill]:
        return self.list_command(options=options).run()

    def get_command(
        self, skill_id: str, *, options: OperationOptions | None = None
    ) -> Command[Skill]:
        validate_nonblank(skill_id)
        return self._decoded_command(("skill", "get", skill_id), Skill, options=options)._map(
            lambda skill: skill._with_client(self._client)
        )

    def get(self, skill_id: str, *, options: OperationOptions | None = None) -> Skill:
        return self.get_command(skill_id, options=options).run()

    def create_command(
        self,
        *,
        name: str,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Skill]:
        validate_nonblank(name)
        _validate_optional_string(description, "description")
        args = ["skill", "create", "--name", name]
        if description is not None:
            args.extend(["--description", description])
        return self._decoded_command(tuple(args), Skill, options=options)._map(
            lambda skill: skill._with_client(self._client)
        )

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Skill:
        return self.create_command(name=name, description=description, options=options).run()

    def update_command(
        self,
        skill_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Skill]:
        validate_nonblank(skill_id)
        if name is None:
            raise TypeError("name must be non-null")
        _validate_optional_string(name, "name")
        _validate_optional_string(description, "description")
        if name is Unset and description is Unset:
            return self._decoded_command(("skill", "get", skill_id), Skill, options=options)._map(
                lambda skill: skill._with_client(self._client)
            )
        args = ["skill", "update", skill_id]
        if name is not Unset:
            args.extend(["--name", name])
        if description is not Unset:
            args.extend(["--description", "" if description is None else description])
        return self._decoded_command(tuple(args), Skill, options=options)._map(
            lambda skill: skill._with_client(self._client)
        )

    def update(
        self,
        skill_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Skill:
        return self.update_command(
            skill_id, name=name, description=description, options=options
        ).run()

    def delete_command(
        self, skill_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(skill_id)
        return self._action_command(("skill", "delete", skill_id), options=options)

    def delete(
        self, skill_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(skill_id, options=options).run()

    def import_from_url_command(
        self, url: str, *, options: OperationOptions | None = None
    ) -> Command[Skill]:
        return self._decoded_command(
            ("skill", "import", "--url", url), Skill, options=options
        )._map(lambda skill: skill._with_client(self._client))

    def import_from_url(self, url: str, *, options: OperationOptions | None = None) -> Skill:
        return self.import_from_url_command(url, options=options).run()
