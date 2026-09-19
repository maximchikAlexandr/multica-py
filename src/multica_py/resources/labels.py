from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import (
    LABEL_LIST_BINDING,
    LABELS_CREATE_MANUAL_BINDING,
    LABELS_UPDATE_MANUAL_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.entities.labels import Label
from multica_py.enums import LabelResourceType
from multica_py.models.common import ActionResult, Page
from multica_py.resources._base import (
    BaseResource,
    _operation_minimum_cli_version,
    _validate_optional_string,
)
from multica_py.sentinels import Unset, UnsetType

__all__ = ["Label", "LabelResource"]


def _normalize_resource_type(value: LabelResourceType | str) -> LabelResourceType:
    if isinstance(value, LabelResourceType):
        return value
    if type(value) is str:
        try:
            return LabelResourceType(value)
        except ValueError as error:
            raise ValueError("resource_type must be 'issue' or 'skill'") from error
    raise TypeError("resource_type must be a LabelResourceType or exact resource string")


def _bind_label(label: Label, client: object | None) -> Label:
    return label._with_client(client)  # type: ignore[arg-type]


class LabelResource(BaseResource):
    def list_command(
        self,
        resource_type: LabelResourceType | str | None = None,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Page[Label]]:
        args = ["label", "list"]
        if resource_type is not None:
            args.extend(["--resource-type", _normalize_resource_type(resource_type).value])
        return self._decoded_page_command(
            tuple(args),
            Label,
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(cast("object", LABEL_LIST_BINDING)),
        )._map(
            lambda page: Page(
                items=tuple(_bind_label(item, self._client) for item in page.items),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(
        self,
        resource_type: LabelResourceType | str | None = None,
        *,
        options: OperationOptions | None = None,
    ) -> Page[Label]:
        return self.list_command(resource_type, options=options).run()

    def get_command(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> Command[Label]:
        validate_nonblank(label_id)
        return self._decoded_command(("label", "get", label_id), Label, options=options)._map(
            lambda label: _bind_label(label, self._client)
        )

    def get(self, label_id: str, *, options: OperationOptions | None = None) -> Label:
        return self.get_command(label_id, options=options).run()

    def create_command(
        self,
        name: str,
        color: str | None = None,
        *,
        resource_type: LabelResourceType | str = LabelResourceType.issue,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Label]:
        validate_nonblank(name)
        if color is not None:
            _validate_optional_string(color, "color")
        _validate_optional_string(description, "description")
        if description == "":
            raise ValueError("description must be non-empty when provided")
        normalized_type = _normalize_resource_type(resource_type)
        args = ["label", "create", "--name", name]
        if color is not None:
            args.extend(["--color", color])
        args.extend(["--resource-type", normalized_type.value])
        if description is not None:
            args.extend(["--description", description])
        return self._decoded_command(
            tuple(args),
            Label,
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(
                cast("object", LABELS_CREATE_MANUAL_BINDING)
            ),
        )._map(lambda label: _bind_label(label, self._client))

    def create(
        self,
        name: str,
        color: str | None = None,
        *,
        resource_type: LabelResourceType | str = LabelResourceType.issue,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Label:
        return self.create_command(
            name,
            color,
            resource_type=resource_type,
            description=description,
            options=options,
        ).run()

    def update_command(
        self,
        label_id: str,
        *,
        name: str | UnsetType = Unset,
        color: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Label]:
        validate_nonblank(label_id)
        if name is None or color is None:
            raise TypeError("label update values must be non-null")
        _validate_optional_string(name, "name")
        _validate_optional_string(color, "color")
        _validate_optional_string(description, "description")
        if name is Unset and color is Unset and description is Unset:
            return self._decoded_command(("label", "get", label_id), Label, options=options)._map(
                lambda label: _bind_label(label, self._client)
            )
        args = ["label", "update", label_id]
        if name is not Unset:
            args.extend(["--name", name])
        if color is not Unset:
            args.extend(["--color", color])
        if description is not Unset:
            args.extend(["--description", "" if description is None else description])
        return self._decoded_command(
            tuple(args),
            Label,
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(
                cast("object", LABELS_UPDATE_MANUAL_BINDING)
            ),
        )._map(lambda label: _bind_label(label, self._client))

    def update(
        self,
        label_id: str,
        *,
        name: str | UnsetType = Unset,
        color: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Label:
        return self.update_command(
            label_id, name=name, color=color, description=description, options=options
        ).run()

    def delete_command(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("label", "delete", label_id), options=options)

    def delete(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(label_id, options=options).run()
