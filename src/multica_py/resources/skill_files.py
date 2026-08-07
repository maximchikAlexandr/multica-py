from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import (
    SKILL_FILES_DELETE_BINDING,
    SKILL_FILES_LIST_BINDING,
    SKILL_FILES_UPSERT_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command
from multica_py.models.common import Page
from multica_py.models.skills import SkillFile
from multica_py.resources._base import BaseResource


class SkillFileResource(BaseResource):
    def list_command(self, skill_id: str) -> Command[Page[SkillFile]]:
        _ = cast("object", SKILL_FILES_LIST_BINDING)
        validate_nonblank(skill_id)
        return self._decoded_page_command(("skill", "files", "list", skill_id), SkillFile)

    def list(self, skill_id: str) -> Page[SkillFile]:
        return self.list_command(skill_id).run()

    def upsert_command(self, skill_id: str, path: str, content: str) -> Command[SkillFile]:
        _ = cast("object", SKILL_FILES_UPSERT_BINDING)
        validate_nonblank(skill_id)
        validate_nonblank(path)
        return self._decoded_command(
            ("skill", "files", "upsert", skill_id, "--path", path, "--content", content),
            SkillFile,
        )

    def upsert(self, skill_id: str, path: str, content: str) -> SkillFile:
        return self.upsert_command(skill_id, path, content).run()

    def delete_command(self, skill_id: str, file_id: str) -> Command[None]:
        _ = cast("object", SKILL_FILES_DELETE_BINDING)
        validate_nonblank(skill_id)
        validate_nonblank(file_id)
        return self._none_command(("skill", "files", "delete", skill_id, file_id))

    def delete(self, skill_id: str, file_id: str) -> None:
        self.delete_command(skill_id, file_id).run()
