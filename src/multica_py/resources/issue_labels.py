from __future__ import annotations

from multica_py._generated.approved_sdk import (
    ISSUE_LABELS_ADD_BINDING,
    ISSUE_LABELS_LIST_BINDING,
    ISSUE_LABELS_REMOVE_BINDING,
)
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.labels import LabelData
from multica_py.resources._base import BaseResource


class IssueLabelResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list(self, issue_id: str) -> tuple[LabelData, ...]:
        _ = ISSUE_LABELS_LIST_BINDING
        return self._run_json_decode_list(("issue", "label", "list", issue_id), LabelData)

    def add(self, issue_id: str, label_id: str) -> tuple[LabelData, ...]:
        _ = ISSUE_LABELS_ADD_BINDING
        return self._run_json_decode_list(("issue", "label", "add", issue_id, label_id), LabelData)

    def remove(self, issue_id: str, label_id: str) -> tuple[LabelData, ...]:
        _ = ISSUE_LABELS_REMOVE_BINDING
        return self._run_json_decode_list(
            ("issue", "label", "remove", issue_id, label_id), LabelData
        )
