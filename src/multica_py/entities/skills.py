from __future__ import annotations

from typing import TypeVar

import msgspec

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.entities._base import _BoundEntity
from multica_py.models.common import ActionResult, Page
from multica_py.models.relations import LazyCollection
from multica_py.models.skills import SkillFile

S = TypeVar("S")


def _page_items(page: Page[S] | tuple[S, ...]) -> tuple[S, ...]:
    return page.items if isinstance(page, Page) else page


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
                    command_loader=lambda: client.skills._files_relation_command(sid),
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

        return client.skills._upsert_file_command(
            self.id,
            path,
            content,
            invalidate=invalidate,
            options=options,
        )

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

        return client.skills._delete_file_command(
            self.id,
            file_id,
            invalidate=invalidate,
            options=options,
        )
