from __future__ import annotations

from typing import overload

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models._bound import _BoundEntity
from multica_py.models.relations import LazyCollection
from multica_py.models.skills import (
    SkillCreateRequest,
    SkillFile,
    SkillUpdateRequest,
)
from multica_py.resources._base import BaseResource, _resolve_request
from multica_py.resources.skill_files import SkillFileResource


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

            def loader() -> tuple[SkillFile, ...]:
                return client.skills.files.list(sid)

            self._set_runtime("_files", LazyCollection(loader))
        return self._files  # type: ignore[return-value]

    def _invalidate_files(self) -> None:
        if self._files is not None:
            self._files.invalidate()

    def upsert_file(self, path: str, content: str) -> SkillFile:
        client = self._require_client(
            entity_type="Skill", entity_id=self.id, relation_name="upsert_file"
        )
        files = client.skills.files
        result = files.upsert(self.id, path, content)
        self._invalidate_files()
        return result

    def delete_file(self, file_id: str) -> None:
        client = self._require_client(
            entity_type="Skill", entity_id=self.id, relation_name="delete_file"
        )
        files = client.skills.files
        files.delete(self.id, file_id)
        self._invalidate_files()


class SkillResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.files = SkillFileResource(transport, config)

    def list(self) -> tuple[Skill, ...]:
        items = self._run_json_decode_list(("skill", "list"), Skill)
        return tuple(s._with_client(self._client) for s in items)

    def get(self, skill_id: str) -> Skill:
        validate_nonblank(skill_id)
        s = self._run_json_decode(("skill", "get", skill_id), Skill)
        return s._with_client(self._client)

    @overload
    def create(self, request: SkillCreateRequest, /) -> Skill: ...
    @overload
    def create(self, *, name: str, description: str | None = None) -> Skill: ...

    def create(self, request: SkillCreateRequest | None = None, /, **kwargs: object) -> Skill:  # type: ignore[misc]
        req = _resolve_request(request, kwargs, SkillCreateRequest)
        validate_nonblank(req.name)
        args = ["skill", "create", "--name", req.name]
        if req.description is not None:
            args.extend(["--description", req.description])
        s = self._run_json_decode(tuple(args), Skill)
        return s._with_client(self._client)

    @overload
    def update(self, skill_id: str, request: SkillUpdateRequest, /) -> Skill: ...
    @overload
    def update(
        self, skill_id: str, *, name: str | None = None, description: str | None = None
    ) -> Skill: ...

    def update(  # type: ignore[misc]
        self, skill_id: str, request: SkillUpdateRequest | None = None, /, **kwargs: object
    ) -> Skill:
        validate_nonblank(skill_id)
        req = _resolve_request(request, kwargs, SkillUpdateRequest)
        args = ["skill", "update", skill_id]
        if req.name is not None:
            args.extend(["--name", req.name])
        if req.description is not None:
            args.extend(["--description", req.description])
        s = self._run_json_decode(tuple(args), Skill)
        return s._with_client(self._client)

    def delete(self, skill_id: str) -> None:
        validate_nonblank(skill_id)
        self._transport.run_text(("skill", "delete", skill_id))

    def import_from_url(self, url: str) -> Skill:
        s = self._run_json_decode(("skill", "import", "--url", url), Skill)
        return s._with_client(self._client)
