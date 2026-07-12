from __future__ import annotations

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.issue_activity import Subscriber
from multica_py.resources._base import BaseResource


class IssueSubscriberResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list(self, issue_id: str) -> tuple[Subscriber, ...]:
        return self._run_json_decode_list(("issue", "subscriber", "list", issue_id), Subscriber)

    def add(self, issue_id: str, user_id: str) -> Subscriber:
        return self._run_json_decode(
            ("issue", "subscriber", "add", issue_id, "--user-id", user_id), Subscriber
        )

    def remove(self, issue_id: str, user_id: str) -> None:
        self._transport.run_text(("issue", "subscriber", "remove", issue_id, "--user-id", user_id))
