from __future__ import annotations

from typing import TYPE_CHECKING, overload

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models import ResourceEntity
from multica_py.models.relations import LazyCollection
from multica_py.models.skills import (
    Skill,
    SkillCreateRequest,
    SkillData,
    SkillFile,
    SkillUpdateRequest,
)
from multica_py.resources._base import BaseResource, _resolve_request
from multica_py.resources.skill_files import SkillFileResource

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


class SkillEntity(ResourceEntity[SkillData]):
    def __init__(self, data: SkillData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)
        self._files: LazyCollection[SkillFile] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def name(self) -> str:
        return self._data.name

    @property
    def description(self) -> str | None:
        return self._data.description

    @property
    def file_count(self) -> int:
        return self._data.file_count

    def _check_client(self, relation_name: str) -> MulticaClient:
        return self._require_client(
            entity_type="SkillEntity", entity_id=self._data.id, relation_name=relation_name
        )

    @property
    def files(self) -> LazyCollection[SkillFile]:
        if self._files is None:
            client = self._check_client("files")
            sid = self._data.id

            def loader() -> tuple[SkillFile, ...]:
                return client.skills.files.list(sid)

            self._files = LazyCollection(loader)
        return self._files

    def _invalidate_files(self) -> None:
        if self._files is not None:
            self._files.invalidate()

    def upsert_file(self, path: str, content: str) -> SkillFile:
        client = self._check_client("upsert_file")
        files = client.skills.files
        result = files.upsert(self._data.id, path, content)
        self._invalidate_files()
        return result

    def delete_file(self, file_id: str) -> None:
        client = self._check_client("delete_file")
        files = client.skills.files
        files.delete(self._data.id, file_id)
        self._invalidate_files()


class SkillResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.files = SkillFileResource(transport, config)

    def list(self) -> tuple[SkillEntity, ...]:
        items = self._run_json_decode_list(("skill", "list"), Skill)
        return tuple(self._bind_skill(s) for s in items)

    def get(self, skill_id: str) -> SkillEntity:
        validate_nonblank(skill_id)
        s = self._run_json_decode(("skill", "get", skill_id), Skill)
        return self._bind_skill(s)

    def _bind_skill(self, s: Skill) -> SkillEntity:
        data = SkillData(
            id=s.id,
            name=s.name,
            description=s.description,
            file_count=s.file_count,
        )
        return SkillEntity(data, client=self._client)

    @overload
    def create(self, request: SkillCreateRequest, /) -> SkillEntity: ...
    @overload
    def create(self, *, name: str, description: str | None = None) -> SkillEntity: ...

    def create(self, request: SkillCreateRequest | None = None, /, **kwargs: object) -> SkillEntity:  # type: ignore[misc]
        req = _resolve_request(request, kwargs, SkillCreateRequest)
        validate_nonblank(req.name)
        args = ["skill", "create", "--name", req.name]
        if req.description is not None:
            args.extend(["--description", req.description])
        s = self._run_json_decode(tuple(args), Skill)
        return self._bind_skill(s)

    @overload
    def update(self, skill_id: str, request: SkillUpdateRequest, /) -> SkillEntity: ...
    @overload
    def update(
        self, skill_id: str, *, name: str | None = None, description: str | None = None
    ) -> SkillEntity: ...

    def update(  # type: ignore[misc]
        self, skill_id: str, request: SkillUpdateRequest | None = None, /, **kwargs: object
    ) -> SkillEntity:
        validate_nonblank(skill_id)
        req = _resolve_request(request, kwargs, SkillUpdateRequest)
        args = ["skill", "update", skill_id]
        if req.name is not None:
            args.extend(["--name", req.name])
        if req.description is not None:
            args.extend(["--description", req.description])
        s = self._run_json_decode(tuple(args), Skill)
        return self._bind_skill(s)

    def delete(self, skill_id: str) -> None:
        validate_nonblank(skill_id)
        self._transport.run_text(("skill", "delete", skill_id))

    def import_from_url(self, url: str) -> SkillEntity:
        s = self._run_json_decode(("skill", "import", "--url", url), Skill)
        return self._bind_skill(s)
