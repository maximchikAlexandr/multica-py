from __future__ import annotations

from typing import cast, overload

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
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
            files = client.skills.files

            def loader() -> tuple[SkillFile, ...]:
                return files.list(sid)

            self._set_runtime(
                "_files",
                LazyCollection[SkillFile](
                    loader,
                    command_loader=lambda: files.list_command(sid),
                ),
            )
        return self._files  # type: ignore[return-value]

    def _invalidate_files(self) -> None:
        if self._files is not None:
            self._files.invalidate()

    def upsert_file(self, path: str, content: str) -> SkillFile:
        return self.upsert_file_command(path, content).run()

    def upsert_file_command(self, path: str, content: str) -> Command[SkillFile]:
        client = self._require_client(
            entity_type="Skill", entity_id=self.id, relation_name="upsert_file"
        )

        def invalidate(result: SkillFile) -> SkillFile:
            self._invalidate_files()
            return result

        return client.skills.files.upsert_command(self.id, path, content)._map(invalidate)

    def delete_file(self, file_id: str) -> None:
        self.delete_file_command(file_id).run()

    def delete_file_command(self, file_id: str) -> Command[None]:
        client = self._require_client(
            entity_type="Skill", entity_id=self.id, relation_name="delete_file"
        )
        return client.skills.files.delete_command(self.id, file_id)._map(
            lambda result: self._invalidate_files()
        )


class SkillResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.files = SkillFileResource(transport, config)

    def list_command(self) -> Command[tuple[Skill, ...]]:
        return self._decoded_list_command(("skill", "list"), Skill)._map(
            lambda items: tuple(skill._with_client(self._client) for skill in items)
        )

    def list(self) -> tuple[Skill, ...]:
        return self.list_command().run()

    def get_command(self, skill_id: str) -> Command[Skill]:
        validate_nonblank(skill_id)
        return self._decoded_command(("skill", "get", skill_id), Skill)._map(
            lambda skill: skill._with_client(self._client)
        )

    def get(self, skill_id: str) -> Skill:
        return self.get_command(skill_id).run()

    @overload
    def create_command(self, request: SkillCreateRequest, /) -> Command[Skill]: ...
    @overload
    def create_command(self, *, name: str, description: str | None = None) -> Command[Skill]: ...

    def create_command(  # type: ignore[misc]
        self, request: SkillCreateRequest | None = None, /, **kwargs: object
    ) -> Command[Skill]:
        req = _resolve_request(request, kwargs, SkillCreateRequest)
        validate_nonblank(req.name)
        args = ["skill", "create", "--name", req.name]
        if req.description is not None:
            args.extend(["--description", req.description])
        return self._decoded_command(tuple(args), Skill)._map(
            lambda skill: skill._with_client(self._client)
        )

    @overload
    def create(self, request: SkillCreateRequest, /) -> Skill: ...
    @overload
    def create(self, *, name: str, description: str | None = None) -> Skill: ...

    def create(  # type: ignore[misc]
        self, request: SkillCreateRequest | None = None, /, **kwargs: object
    ) -> Skill:
        return self.create_command(cast("SkillCreateRequest", request), **kwargs).run()

    @overload
    def update_command(self, skill_id: str, request: SkillUpdateRequest, /) -> Command[Skill]: ...
    @overload
    def update_command(
        self, skill_id: str, *, name: str | None = None, description: str | None = None
    ) -> Command[Skill]: ...

    def update_command(  # type: ignore[misc]
        self, skill_id: str, request: SkillUpdateRequest | None = None, /, **kwargs: object
    ) -> Command[Skill]:
        validate_nonblank(skill_id)
        req = _resolve_request(request, kwargs, SkillUpdateRequest)
        args = ["skill", "update", skill_id]
        if req.name is not None:
            args.extend(["--name", req.name])
        if req.description is not None:
            args.extend(["--description", req.description])
        return self._decoded_command(tuple(args), Skill)._map(
            lambda skill: skill._with_client(self._client)
        )

    @overload
    def update(self, skill_id: str, request: SkillUpdateRequest, /) -> Skill: ...
    @overload
    def update(
        self, skill_id: str, *, name: str | None = None, description: str | None = None
    ) -> Skill: ...

    def update(  # type: ignore[misc]
        self, skill_id: str, request: SkillUpdateRequest | None = None, /, **kwargs: object
    ) -> Skill:
        return self.update_command(skill_id, cast("SkillUpdateRequest", request), **kwargs).run()

    def delete_command(self, skill_id: str) -> Command[None]:
        validate_nonblank(skill_id)
        return self._none_command(("skill", "delete", skill_id))

    def delete(self, skill_id: str) -> None:
        self.delete_command(skill_id).run()

    def import_from_url_command(self, url: str) -> Command[Skill]:
        return self._decoded_command(("skill", "import", "--url", url), Skill)._map(
            lambda skill: skill._with_client(self._client)
        )

    def import_from_url(self, url: str) -> Skill:
        return self.import_from_url_command(url).run()
