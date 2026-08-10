from __future__ import annotations

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.models._bound import _BoundEntity
from multica_py.models.common import ActionResult, Page
from multica_py.models.relations import LazyCollection
from multica_py.models.skills import SkillFile
from multica_py.resources._base import BaseResource, _page_items, _validate_optional_string
from multica_py.resources.skill_files import SkillFileResource
from multica_py.sentinels import Unset, UnsetType


class Skill(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    description: str | None = None
    file_count: int = 0

    _files: LazyCollection[SkillFile] | None = msgspec.field(default=None, name="_files")

    _PUBLIC_FIELDS = ("id", "name", "description", "file_count")

    @property
    def files(self) -> LazyCollection[SkillFile]:
        if self._files is None:
            client = self._require_client(
                entity_type="Skill", entity_id=self.id, relation_name="files"
            )
            sid = self.id
            files = client.skills.files

            def loader() -> tuple[SkillFile, ...]:
                return _page_items(files.list(sid))

            self._set_runtime(
                "_files",
                LazyCollection[SkillFile](
                    loader,
                    command_loader=lambda: files.list_command(sid)._map(_page_items),
                ),
            )
        return self._files  # type: ignore[return-value]

    def _invalidate_files(self) -> None:
        if self._files is not None:
            self._files.invalidate()

    def upsert_file(
        self, path: str, content: str, *, options: OperationOptions | None = None
    ) -> SkillFile:
        return self.upsert_file_command(path, content, options=options).run()

    def upsert_file_command(
        self, path: str, content: str, *, options: OperationOptions | None = None
    ) -> Command[SkillFile]:
        client = self._require_client(
            entity_type="Skill", entity_id=self.id, relation_name="upsert_file"
        )

        def invalidate(result: SkillFile) -> SkillFile:
            self._invalidate_files()
            return result

        command = client.skills.files.upsert_command(self.id, path, content, options=options)
        return command._map(invalidate)

    def delete_file(
        self, file_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_file_command(file_id, options=options).run()

    def delete_file_command(
        self, file_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        client = self._require_client(
            entity_type="Skill", entity_id=self.id, relation_name="delete_file"
        )

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_files()
            return result

        command = client.skills.files.delete_command(self.id, file_id, options=options)
        return command._map(invalidate)


class SkillResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.files = SkillFileResource(transport, config)

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
