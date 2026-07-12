from __future__ import annotations

from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.resources._base import BaseResource


class IssueLabelResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list(self, issue_id: str) -> tuple[str, ...]:
        result = self._transport.run_bytes(("issue", "label", "list", issue_id, "--output", "json"))
        return tuple(decode_json(result.stdout, list[str]))

    def add(self, issue_id: str, label: str) -> None:
        self._transport.run_text(("issue", "label", "add", issue_id, "--label", label))

    def remove(self, issue_id: str, label: str) -> None:
        self._transport.run_text(("issue", "label", "remove", issue_id, "--label", label))
