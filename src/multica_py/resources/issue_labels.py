from __future__ import annotations

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.labels import Label
from multica_py.resources._base import BaseResource


class IssueLabelResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list(self, issue_id: str) -> tuple[Label, ...]:
        return self._run_json_decode_list(("issue", "label", "list", issue_id), Label)

    def add(self, issue_id: str, label_id: str) -> tuple[Label, ...]:
        return self._run_json_decode_list(("issue", "label", "add", issue_id, label_id), Label)

    def remove(self, issue_id: str, label_id: str) -> tuple[Label, ...]:
        return self._run_json_decode_list(("issue", "label", "remove", issue_id, label_id), Label)
