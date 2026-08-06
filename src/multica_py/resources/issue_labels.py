from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import (
    ISSUE_LABELS_ADD_BINDING,
    ISSUE_LABELS_LIST_BINDING,
    ISSUE_LABELS_REMOVE_BINDING,
)
from multica_py._internal.commands import Command, _Step
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import _LabelWire
from multica_py.config import ClientConfig
from multica_py.resources._base import BaseResource


class IssueLabelResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list_command(self, issue_id: str) -> Command[tuple[_LabelWire, ...]]:
        _ = cast("object", ISSUE_LABELS_LIST_BINDING)
        args, decode = self._plan_decode_list(("issue", "label", "list", issue_id), _LabelWire)

        def finalize(results: tuple[object, ...]) -> tuple[_LabelWire, ...]:
            return cast("tuple[_LabelWire, ...]", results[0])

        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=finalize,
        )

    def list(self, issue_id: str) -> tuple[_LabelWire, ...]:
        return self.list_command(issue_id).run()

    def add_command(self, issue_id: str, label_id: str) -> Command[tuple[_LabelWire, ...]]:
        _ = cast("object", ISSUE_LABELS_ADD_BINDING)
        args, decode = self._plan_decode_list(
            ("issue", "label", "add", issue_id, label_id), _LabelWire
        )

        def finalize(results: tuple[object, ...]) -> tuple[_LabelWire, ...]:
            return cast("tuple[_LabelWire, ...]", results[0])

        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=finalize,
        )

    def add(self, issue_id: str, label_id: str) -> tuple[_LabelWire, ...]:
        return self.add_command(issue_id, label_id).run()

    def remove_command(self, issue_id: str, label_id: str) -> Command[tuple[_LabelWire, ...]]:
        _ = cast("object", ISSUE_LABELS_REMOVE_BINDING)
        args, decode = self._plan_decode_list(
            ("issue", "label", "remove", issue_id, label_id), _LabelWire
        )

        def finalize(results: tuple[object, ...]) -> tuple[_LabelWire, ...]:
            return cast("tuple[_LabelWire, ...]", results[0])

        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=finalize,
        )

    def remove(self, issue_id: str, label_id: str) -> tuple[_LabelWire, ...]:
        return self.remove_command(issue_id, label_id).run()
