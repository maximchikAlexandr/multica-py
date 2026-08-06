from __future__ import annotations

from typing import cast

from multica_py._internal.commands import Command, _Step
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.issue_activity import Subscriber
from multica_py.resources._base import BaseResource


class IssueSubscriberResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list_command(self, issue_id: str) -> Command[tuple[Subscriber, ...]]:
        args, decode = self._plan_decode_list(("issue", "subscriber", "list", issue_id), Subscriber)

        def finalize(results: tuple[object, ...]) -> tuple[Subscriber, ...]:
            return cast("tuple[Subscriber, ...]", results[0])

        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=finalize,
        )

    def list(self, issue_id: str) -> tuple[Subscriber, ...]:
        return self.list_command(issue_id).run()

    def add_command(self, issue_id: str, user_id: str) -> Command[None]:
        return self._plan(
            steps=(
                _Step(("issue", "subscriber", "add", issue_id, "--user-id", user_id), "run_text"),
            ),
            finalize=lambda results: None,
        )

    def add(self, issue_id: str, user_id: str) -> None:
        self.add_command(issue_id, user_id).run()

    def remove_command(self, issue_id: str, user_id: str) -> Command[None]:
        return self._plan(
            steps=(
                _Step(
                    ("issue", "subscriber", "remove", issue_id, "--user-id", user_id),
                    "run_text",
                ),
            ),
            finalize=lambda results: None,
        )

    def remove(self, issue_id: str, user_id: str) -> None:
        self.remove_command(issue_id, user_id).run()
