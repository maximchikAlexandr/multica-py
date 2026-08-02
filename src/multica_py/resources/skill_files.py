from __future__ import annotations

from multica_py._generated.approved_sdk import (
    SKILL_FILES_DELETE_BINDING,
    SKILL_FILES_LIST_BINDING,
    SKILL_FILES_UPSERT_BINDING,
    validate_nonblank,
)
from multica_py.models.skills import SkillFile
from multica_py.resources._base import BaseResource


class SkillFileResource(BaseResource):
    def list(self, skill_id: str) -> tuple[SkillFile, ...]:
        _ = SKILL_FILES_LIST_BINDING
        validate_nonblank(skill_id)
        return self._run_json_decode_list(("skill", "files", "list", skill_id), SkillFile)

    def upsert(self, skill_id: str, path: str, content: str) -> SkillFile:
        _ = SKILL_FILES_UPSERT_BINDING
        validate_nonblank(skill_id)
        validate_nonblank(path)
        args = ("skill", "files", "upsert", skill_id, "--path", path, "--content", content)
        return self._run_json_decode(args, SkillFile)

    def delete(self, skill_id: str, file_id: str) -> None:
        _ = SKILL_FILES_DELETE_BINDING
        validate_nonblank(skill_id)
        validate_nonblank(file_id)
        self._transport.run_text(("skill", "files", "delete", skill_id, file_id))
