from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import (
    SKILL_FILES_DELETE_BINDING,
    SKILL_FILES_LIST_BINDING,
    SKILL_FILES_UPSERT_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command, _Step
from multica_py.models.skills import SkillFile
from multica_py.resources._base import BaseResource


class SkillFileResource(BaseResource):
    def list_command(self, skill_id: str) -> Command[tuple[SkillFile, ...]]:
        _ = cast("object", SKILL_FILES_LIST_BINDING)
        validate_nonblank(skill_id)
        args, decode = self._plan_decode_list(("skill", "files", "list", skill_id), SkillFile)

        def finalize(results: tuple[object, ...]) -> tuple[SkillFile, ...]:
            return cast("tuple[SkillFile, ...]", results[0])

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def list(self, skill_id: str) -> tuple[SkillFile, ...]:
        return self.list_command(skill_id).run()

    def upsert_command(self, skill_id: str, path: str, content: str) -> Command[SkillFile]:
        _ = cast("object", SKILL_FILES_UPSERT_BINDING)
        validate_nonblank(skill_id)
        validate_nonblank(path)
        args = ("skill", "files", "upsert", skill_id, "--path", path, "--content", content)
        plan_args, decode = self._plan_decode(args, SkillFile)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("SkillFile", results[0]),
        )

    def upsert(self, skill_id: str, path: str, content: str) -> SkillFile:
        return self.upsert_command(skill_id, path, content).run()

    def delete_command(self, skill_id: str, file_id: str) -> Command[None]:
        _ = cast("object", SKILL_FILES_DELETE_BINDING)
        validate_nonblank(skill_id)
        validate_nonblank(file_id)
        return self._plan(
            steps=(_Step(("skill", "files", "delete", skill_id, file_id), "run_text"),),
            finalize=lambda results: None,
        )

    def delete(self, skill_id: str, file_id: str) -> None:
        self.delete_command(skill_id, file_id).run()
