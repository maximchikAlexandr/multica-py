from __future__ import annotations

from multica_py.models.skills import SkillFile
from multica_py.resources._base import BaseResource


class SkillFileResource(BaseResource):
    def list(self, skill_id: str) -> tuple[SkillFile, ...]:
        return self._run_json_decode_list(("skill", "file", "list", skill_id), SkillFile)

    def upsert(self, skill_id: str, path: str, content: str) -> SkillFile:
        args = ("skill", "file", "upsert", skill_id, "--path", path, "--content", content)
        return self._run_json_decode((args), SkillFile)

    def delete(self, skill_id: str, file_id: str) -> None:
        self._transport.run_text(("skill", "file", "delete", skill_id, "--file-id", file_id))
