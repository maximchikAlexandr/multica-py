from __future__ import annotations

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.entities.labels import Label
from multica_py.models.common import ActionResult, Page
from multica_py.resources._base import BaseResource, _validate_optional_string
from multica_py.sentinels import Unset, UnsetType

__all__ = ["Label", "LabelResource"]


class LabelResource(BaseResource):
    def list_command(self, *, options: OperationOptions | None = None) -> Command[Page[Label]]:
        return self._decoded_page_command(("label", "list"), Label, options=options)._map(
            lambda page: Page(
                items=tuple(item._with_client(self._client) for item in page.items),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(self, *, options: OperationOptions | None = None) -> Page[Label]:
        return self.list_command(options=options).run()

    def get_command(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> Command[Label]:
        return self._decoded_command(("label", "get", label_id), Label, options=options)._map(
            lambda label: label._with_client(self._client)
        )

    def get(self, label_id: str, *, options: OperationOptions | None = None) -> Label:
        return self.get_command(label_id, options=options).run()

    def create_command(
        self, name: str, color: str | None = None, *, options: OperationOptions | None = None
    ) -> Command[Label]:
        args = ["label", "create", "--name", name]
        if color is not None:
            args.extend(["--color", color])
        return self._decoded_command(tuple(args), Label, options=options)._map(
            lambda label: label._with_client(self._client)
        )

    def create(
        self, name: str, color: str | None = None, *, options: OperationOptions | None = None
    ) -> Label:
        return self.create_command(name, color, options=options).run()

    def update_command(
        self,
        label_id: str,
        *,
        name: str | UnsetType = Unset,
        color: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Label]:
        validate_nonblank(label_id)
        if name is None or color is None:
            raise TypeError("label update values must be non-null")
        _validate_optional_string(name, "name")
        _validate_optional_string(color, "color")
        if name is Unset and color is Unset:
            return self._decoded_command(("label", "get", label_id), Label, options=options)._map(
                lambda label: label._with_client(self._client)
            )
        args = ["label", "update", label_id]
        if name is not Unset:
            args.extend(["--name", name])
        if color is not Unset:
            args.extend(["--color", color])
        return self._decoded_command(tuple(args), Label, options=options)._map(
            lambda label: label._with_client(self._client)
        )

    def update(
        self,
        label_id: str,
        *,
        name: str | UnsetType = Unset,
        color: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Label:
        return self.update_command(label_id, name=name, color=color, options=options).run()

    def delete_command(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("label", "delete", label_id), options=options)

    def delete(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(label_id, options=options).run()
