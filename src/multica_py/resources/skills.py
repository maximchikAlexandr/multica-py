from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, cast

import msgspec

from multica_py._generated.approved_sdk import SKILL_LIST_BINDING, validate_nonblank
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.issue_wires import _LabelWire
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.labels import Label
from multica_py.entities.skills import Skill
from multica_py.models.common import ActionResult, Page
from multica_py.models.relations import LazyCollection
from multica_py.models.skills import SkillFile, SkillSearchResult
from multica_py.resources._base import (
    BaseResource,
    _operation_minimum_cli_version,
    _page_items,
    _validate_optional_string,
)
from multica_py.resources.skill_files import SkillFileResource
from multica_py.resources.skill_labels import SkillLabelResource, _ensure_skill_scope
from multica_py.sentinels import Unset, UnsetType

if TYPE_CHECKING:
    from multica_py.client import MulticaClient

__all__ = ["Skill", "SkillResource"]

T = TypeVar("T")


def _invalidate_result(invalidate: Callable[[], None]) -> Callable[[T], T]:
    def finish(result: T) -> T:
        invalidate()
        return result

    return finish


class _SkillSearchResultWire(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    url: str
    source: str
    install_count: int
    description: str = ""


class _SkillWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None
    file_count: int = 0
    content: str | None | msgspec.UnsetType = msgspec.UNSET


class _SkillListWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None
    file_count: int = 0
    labels: tuple[_LabelWire, ...]


def _skill_from_wire(wire: _SkillWire) -> Skill:
    presence = (
        "missing" if wire.content is msgspec.UNSET else "null" if wire.content is None else "value"
    )
    return Skill(
        id=wire.id,
        name=wire.name,
        description=wire.description,
        file_count=wire.file_count,
        content=None if wire.content is msgspec.UNSET else wire.content,
        _wire_presence=(("content", presence),),
    )


def _skill_from_list_wire(wire: _SkillListWire) -> Skill:
    return Skill(
        id=wire.id,
        name=wire.name,
        description=wire.description,
        file_count=wire.file_count,
        _wire_presence=(("content", "missing"),),
    )


class SkillResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.files = SkillFileResource(transport, config)
        self.labels = SkillLabelResource(transport, config)

    def _set_client(self, client: MulticaClient) -> None:
        super()._set_client(client)
        self.labels._set_client(client)

    def _files_relation_command(self, skill_id: str) -> Command[tuple[SkillFile, ...]]:
        return self.files.list_command(skill_id, with_content=False)._map(_page_items)

    def _labels_relation_command(self, skill_id: str) -> Command[tuple[Label, ...]]:
        return self.labels.list_command(skill_id)._map(_page_items)

    def _add_label_command(
        self,
        skill_id: str,
        label_id: str,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[Page[Label]]:
        command = self.labels.add_command(skill_id, label_id, options=options)

        return command._map(_invalidate_result(invalidate))

    def _remove_label_command(
        self,
        skill_id: str,
        label_id: str,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[Page[Label] | ActionResult[None]]:
        command = self.labels.remove_command(skill_id, label_id, options=options)

        return command._map(_invalidate_result(invalidate))

    def _bind_skill_labels(self, skill: Skill, labels: tuple[_LabelWire, ...]) -> Skill:
        labels = _ensure_skill_scope(labels)
        values = tuple(
            Label(
                id=item.id,
                name=item.name,
                color=item.color,
                description=item.description,
                resource_type=item.resource_type,
                _client=self._client,
            )
            for item in labels
        )
        skill._set_runtime(
            "_labels",
            LazyCollection(
                lambda: values,
                initial=values,
                command_loader=lambda: self._labels_relation_command(skill.id),
            ),
        )
        return skill

    def _upsert_file_command(
        self,
        skill_id: str,
        path: str,
        content: str,
        *,
        invalidate: Callable[[SkillFile], SkillFile],
        options: OperationOptions | None,
    ) -> Command[SkillFile]:
        return self.files.upsert_command(skill_id, path, content, options=options)._map(invalidate)

    def _delete_file_command(
        self,
        skill_id: str,
        file_id: str,
        *,
        invalidate: Callable[[ActionResult[None]], ActionResult[None]],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        return self.files.delete_command(skill_id, file_id, options=options)._map(invalidate)

    def list_command(self, *, options: OperationOptions | None = None) -> Command[Page[Skill]]:
        return self._decoded_page_command(
            ("skill", "list"),
            _SkillListWire,
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(cast("object", SKILL_LIST_BINDING)),
        )._map(
            lambda page: Page(
                items=tuple(
                    self._bind_skill_labels(
                        _skill_from_list_wire(skill), skill.labels
                    )._with_client(self._client)
                    for skill in page.items
                ),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(self, *, options: OperationOptions | None = None) -> Page[Skill]:
        return self.list_command(options=options).run()

    def get_command(
        self, skill_id: str, *, options: OperationOptions | None = None
    ) -> Command[Skill]:
        validate_nonblank(skill_id)
        args = ["skill", "get", skill_id]
        args.append("--with-content")
        return self._decoded_command(tuple(args), _SkillWire, options=options)._map(
            lambda skill: _skill_from_wire(skill)._with_client(self._client)
        )

    def get(self, skill_id: str, *, options: OperationOptions | None = None) -> Skill:
        return self.get_command(skill_id, options=options).run()

    def create_command(
        self,
        *,
        name: str,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Skill]:
        validate_nonblank(name)
        _validate_optional_string(description, "description")
        args = ["skill", "create", "--name", name]
        if description is not None:
            args.extend(["--description", description])
        return self._decoded_command(tuple(args), _SkillWire, options=options)._map(
            lambda skill: _skill_from_wire(skill)._with_client(self._client)
        )

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Skill:
        return self.create_command(name=name, description=description, options=options).run()

    def update_command(
        self,
        skill_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Skill]:
        validate_nonblank(skill_id)
        if name is None:
            raise TypeError("name must be non-null")
        _validate_optional_string(name, "name")
        _validate_optional_string(description, "description")
        if name is Unset and description is Unset:
            return self.get_command(skill_id, options=options)
        args = ["skill", "update", skill_id]
        if name is not Unset:
            args.extend(["--name", name])
        if description is not Unset:
            args.extend(["--description", "" if description is None else description])
        return self._decoded_command(tuple(args), _SkillWire, options=options)._map(
            lambda skill: _skill_from_wire(skill)._with_client(self._client)
        )

    def update(
        self,
        skill_id: str,
        *,
        name: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Skill:
        return self.update_command(
            skill_id, name=name, description=description, options=options
        ).run()

    def refresh_command(
        self, skill_id: str, *, options: OperationOptions | None = None
    ) -> Command[Skill]:
        validate_nonblank(skill_id)
        return self._decoded_command(
            ("skill", "refresh", skill_id), _SkillWire, options=options
        )._map(lambda skill: _skill_from_wire(skill)._with_client(self._client))

    def refresh(self, skill_id: str, *, options: OperationOptions | None = None) -> Skill:
        return self.refresh_command(skill_id, options=options).run()

    @staticmethod
    def _decode_skill_search_result(stdout: bytes, command: str) -> SkillSearchResult:
        row = decode_json(stdout, _SkillSearchResultWire, command=command)
        return SkillSearchResult(
            name=row.name,
            url=row.url,
            source=row.source,
            install_count=row.install_count,
            description=row.description,
        )

    @staticmethod
    def _decode_skill_search_results(stdout: bytes, command: str) -> Page[SkillSearchResult]:
        rows = decode_json(stdout, list[_SkillSearchResultWire], command=command)
        items = tuple(
            SkillSearchResult(
                name=row.name,
                url=row.url,
                source=row.source,
                install_count=row.install_count,
                description=row.description,
            )
            for row in rows
        )
        return Page(items=items, total=len(items))

    def search_command(
        self, query: str, *, options: OperationOptions | None = None
    ) -> Command[Page[SkillSearchResult]]:
        validate_nonblank(query)
        return self._skill_search_page_command(("skill", "search", query), options=options)

    def search(
        self, query: str, *, options: OperationOptions | None = None
    ) -> Page[SkillSearchResult]:
        return self.search_command(query, options=options).run()

    def _skill_search_page_command(
        self, args: tuple[str, ...], *, options: OperationOptions | None
    ) -> Command[Page[SkillSearchResult]]:
        plan_args = (*args, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            return self._decode_skill_search_results(stdout, command)

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("Page[SkillSearchResult]", results[0]),
            options=options,
        )

    def delete_command(
        self, skill_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(skill_id)
        return self._action_command(("skill", "delete", skill_id), options=options)

    def delete(
        self, skill_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(skill_id, options=options).run()

    def import_from_url_command(
        self, url: str, *, options: OperationOptions | None = None
    ) -> Command[Skill]:
        return self._decoded_command(
            ("skill", "import", "--url", url), _SkillWire, options=options
        )._map(lambda skill: _skill_from_wire(skill)._with_client(self._client))

    def import_from_url(self, url: str, *, options: OperationOptions | None = None) -> Skill:
        return self.import_from_url_command(url, options=options).run()
