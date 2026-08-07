from __future__ import annotations

from typing import cast, overload

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py.models._bound import _BoundEntity
from multica_py.models.common import Page
from multica_py.models.labels import LabelUpdateRequest
from multica_py.resources._base import BaseResource, _resolve_request
from multica_py.sentinels import Unset, UnsetType


class Label(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    color: str | None = None

    _PUBLIC_FIELDS = ("id", "name", "color")


class LabelResource(BaseResource):
    def list_command(self) -> Command[Page[Label]]:
        return self._decoded_page_command(("label", "list"), Label)._map(
            lambda page: Page(
                items=tuple(item._with_client(self._client) for item in page.items),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(self) -> Page[Label]:
        return self.list_command().run()

    def get_command(self, label_id: str) -> Command[Label]:
        return self._decoded_command(("label", "get", label_id), Label)._map(
            lambda label: label._with_client(self._client)
        )

    def get(self, label_id: str) -> Label:
        return self.get_command(label_id).run()

    def create_command(self, name: str, color: str | None = None) -> Command[Label]:
        args = ["label", "create", "--name", name]
        if color is not None:
            args.extend(["--color", color])
        return self._decoded_command(tuple(args), Label)._map(
            lambda label: label._with_client(self._client)
        )

    def create(self, name: str, color: str | None = None) -> Label:
        return self.create_command(name, color).run()

    @overload
    def update_command(self, label_id: str, request: LabelUpdateRequest, /) -> Command[Label]: ...

    @overload
    def update_command(
        self,
        label_id: str,
        *,
        name: str | UnsetType = Unset,
        color: str | UnsetType = Unset,
    ) -> Command[Label]: ...

    def update_command(  # type: ignore[misc]
        self, label_id: str, request: LabelUpdateRequest | None = None, /, **kwargs: object
    ) -> Command[Label]:
        validate_nonblank(label_id)
        request = _resolve_request(request, kwargs, LabelUpdateRequest, allow_empty=True)
        if request.name is Unset and request.color is Unset:
            return self.get_command(label_id)
        args = ["label", "update", label_id]
        if request.name is not Unset:
            args.extend(["--name", request.name])
        if request.color is not Unset:
            args.extend(["--color", request.color])
        return self._decoded_command(tuple(args), Label)._map(
            lambda label: label._with_client(self._client)
        )

    @overload
    def update(self, label_id: str, request: LabelUpdateRequest, /) -> Label: ...

    @overload
    def update(
        self,
        label_id: str,
        *,
        name: str | UnsetType = Unset,
        color: str | UnsetType = Unset,
    ) -> Label: ...

    def update(  # type: ignore[misc]
        self, label_id: str, request: LabelUpdateRequest | None = None, /, **kwargs: object
    ) -> Label:
        return self.update_command(label_id, cast("LabelUpdateRequest", request), **kwargs).run()

    def delete_command(self, label_id: str) -> Command[None]:
        return self._none_command(("label", "delete", label_id))

    def delete(self, label_id: str) -> None:
        self.delete_command(label_id).run()
