from __future__ import annotations

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.skills import Skill, SkillCreateRequest, SkillUpdateRequest
from multica_py.resources._base import BaseResource
from multica_py.resources.skill_files import SkillFileResource


class SkillResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.files = SkillFileResource(transport, config)

    def list(self) -> tuple[Skill, ...]:
        return self._run_json_decode_list(("skill", "list"), Skill)

    def get(self, skill_id: str) -> Skill:
        return self._run_json_decode(("skill", "get", skill_id), Skill)

    def create(self, request: SkillCreateRequest) -> Skill:
        args = ["skill", "create", "--name", request.name]
        if request.description is not None:
            args.extend(["--description", request.description])
        return self._run_json_decode(tuple(args), Skill)

    def update(self, skill_id: str, request: SkillUpdateRequest) -> Skill:
        args = ["skill", "update", skill_id]
        if request.name is not None:
            args.extend(["--name", request.name])
        if request.description is not None:
            args.extend(["--description", request.description])
        return self._run_json_decode(tuple(args), Skill)

    def delete(self, skill_id: str) -> None:
        self._transport.run_text(("skill", "delete", skill_id))

    def import_from_url(self, url: str) -> Skill:
        return self._run_json_decode(("skill", "import", "--url", url), Skill)
