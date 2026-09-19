from __future__ import annotations

from typing import cast

import msgspec

from multica_py._generated.approved_sdk import (
    SKILL_LABELS_ADD_BINDING,
    SKILL_LABELS_LIST_BINDING,
    SKILL_LABELS_REMOVE_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.issue_wires import _LabelWire
from multica_py.config import OperationOptions
from multica_py.entities.labels import Label
from multica_py.exceptions import JsonOutputError, OutputShapeError
from multica_py.models.common import ActionResult, Page
from multica_py.resources._base import BaseResource, _operation_minimum_cli_version

__all__ = ["SkillLabelResource"]


class _DetachedWire(msgspec.Struct, frozen=True, kw_only=True):
    detached: bool


def _ensure_skill_scope(rows: tuple[_LabelWire, ...]) -> tuple[_LabelWire, ...]:
    """Reject known issue labels while keeping response scope open for new values."""
    if any(row.resource_type == "issue" for row in rows):
        raise OutputShapeError("skill label response contained an issue-scoped label")
    return rows


class SkillLabelResource(BaseResource):
    def _bind_page(self, page: Page[_LabelWire]) -> Page[Label]:
        rows = _ensure_skill_scope(page.items)
        return Page(
            items=tuple(
                Label(
                    id=item.id,
                    name=item.name,
                    color=item.color,
                    description=item.description,
                    resource_type=item.resource_type,
                    _client=self._client,
                )
                for item in rows
            ),
            limit=page.limit,
            offset=page.offset,
            total=page.total,
            has_more=page.has_more,
            next_cursor=page.next_cursor,
        )

    def _page_command(
        self,
        args: tuple[str, ...],
        *,
        options: OperationOptions | None = None,
        minimum_cli_version: str | None = None,
    ) -> Command[Page[Label]]:
        command = self._decoded_page_command(
            args,
            _LabelWire,
            options=options,
            minimum_cli_version=minimum_cli_version,
        )
        return command._map(self._bind_page)

    def list_command(
        self, skill_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[Label]]:
        validate_nonblank(skill_id)
        return self._page_command(
            ("skill", "label", "list", skill_id),
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(
                cast("object", SKILL_LABELS_LIST_BINDING)
            ),
        )

    def list(self, skill_id: str, *, options: OperationOptions | None = None) -> Page[Label]:
        return self.list_command(skill_id, options=options).run()

    def add_command(
        self, skill_id: str, label_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[Label]]:
        validate_nonblank(skill_id)
        validate_nonblank(label_id)
        return self._page_command(
            ("skill", "label", "add", skill_id, label_id),
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(
                cast("object", SKILL_LABELS_ADD_BINDING)
            ),
        )

    def add(
        self, skill_id: str, label_id: str, *, options: OperationOptions | None = None
    ) -> Page[Label]:
        return self.add_command(skill_id, label_id, options=options).run()

    def remove_command(
        self, skill_id: str, label_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[Label] | ActionResult[None]]:
        validate_nonblank(skill_id)
        validate_nonblank(label_id)

        def decode(stdout: bytes, command: str) -> object:
            try:
                page = decode_json(stdout, list[_LabelWire], command=command)
            except (JsonOutputError, OutputShapeError):
                detached = decode_json(stdout, _DetachedWire, command=command)
                if not detached.detached:
                    raise ValueError("skill label remove response was not detached")
                return ActionResult[None]()
            return self._bind_page(Page(items=tuple(page), total=len(page)))

        return self._plan(
            steps=(
                # The remove response is normally the refreshed label list;
                # the detached object is the reviewed success fallback.
                _Step(
                    ("skill", "label", "remove", skill_id, label_id, "--output", "json"),
                    "run_bytes",
                    decode=decode,
                ),
            ),
            finalize=lambda results: cast("Page[Label] | ActionResult[None]", results[0]),
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(
                cast("object", SKILL_LABELS_REMOVE_BINDING)
            ),
        )

    def remove(
        self, skill_id: str, label_id: str, *, options: OperationOptions | None = None
    ) -> Page[Label] | ActionResult[None]:
        return self.remove_command(skill_id, label_id, options=options).run()
