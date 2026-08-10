from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.models.common import ActionResult, Page
from multica_py.models.issue_activity import Subscriber
from multica_py.resources._base import BaseResource


class IssueSubscriberResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[Subscriber]]:
        return self._decoded_page_command(
            ("issue", "subscriber", "list", issue_id), Subscriber, options=options
        )

    def list(self, issue_id: str, *, options: OperationOptions | None = None) -> Page[Subscriber]:
        return self.list_command(issue_id, options=options).run()

    def add_command(
        self, issue_id: str, user_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(
            ("issue", "subscriber", "add", issue_id, "--user-id", user_id), options=options
        )

    def add(
        self, issue_id: str, user_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.add_command(issue_id, user_id, options=options).run()

    def remove_command(
        self, issue_id: str, user_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(
            ("issue", "subscriber", "remove", issue_id, "--user-id", user_id), options=options
        )

    def remove(
        self, issue_id: str, user_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.remove_command(issue_id, user_id, options=options).run()
