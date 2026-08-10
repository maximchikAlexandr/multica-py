from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import (
    SKILL_FILES_DELETE_BINDING,
    SKILL_FILES_LIST_BINDING,
    SKILL_FILES_UPSERT_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.common import ActionResult, Page
from multica_py.models.skills import SkillFile
from multica_py.resources._base import BaseResource


class SkillFileResource(BaseResource):
    def list_command(
        self, skill_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[SkillFile]]:
        _ = cast("object", SKILL_FILES_LIST_BINDING)
        validate_nonblank(skill_id)
        return self._decoded_page_command(
            ("skill", "files", "list", skill_id), SkillFile, options=options
        )

    def list(self, skill_id: str, *, options: OperationOptions | None = None) -> Page[SkillFile]:
        return self.list_command(skill_id, options=options).run()

    def upsert_command(
        self,
        skill_id: str,
        path: str,
        content: str,
        *,
        options: OperationOptions | None = None,
    ) -> Command[SkillFile]:
        _ = cast("object", SKILL_FILES_UPSERT_BINDING)
        validate_nonblank(skill_id)
        validate_nonblank(path)
        return self._decoded_command(
            ("skill", "files", "upsert", skill_id, "--path", path, "--content", content),
            SkillFile,
            options=options,
        )

    def upsert(
        self, skill_id: str, path: str, content: str, *, options: OperationOptions | None = None
    ) -> SkillFile:
        return self.upsert_command(skill_id, path, content, options=options).run()

    def delete_command(
        self, skill_id: str, file_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        _ = cast("object", SKILL_FILES_DELETE_BINDING)
        validate_nonblank(skill_id)
        validate_nonblank(file_id)
        return self._action_command(
            ("skill", "files", "delete", skill_id, file_id), options=options
        )

    def delete(
        self, skill_id: str, file_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(skill_id, file_id, options=options).run()
