from __future__ import annotations

import pathlib

from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import IssueWire, issue_from_wire
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.models.issue_activity import IssueUsage, RunMessage, TaskRun
from multica_py.models.issues import (
    FileDescription,
    InlineDescription,
    Issue,
    IssueAssignmentRequest,
    IssueChildStageGroup,
    IssueCreateRequest,
    IssueListFilter,
    IssueReorderRequest,
    IssueSummary,
    IssueUpdateRequest,
    LinkedPullRequest,
    StdinDescription,
)
from multica_py.resources._base import BaseResource
from multica_py.resources.issue_comments import IssueCommentResource
from multica_py.resources.issue_labels import IssueLabelResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issue_subscribers import IssueSubscriberResource


class IssueResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.comments = IssueCommentResource(transport, config)
        self.metadata = IssueMetadataResource(transport, config)
        self.subscribers = IssueSubscriberResource(transport, config)
        self.labels = IssueLabelResource(transport, config)

    def list(self, filter: IssueListFilter | None = None) -> tuple[IssueSummary, ...]:
        args = ["issue", "list"]
        if filter is not None:
            if filter.status is not None:
                args.extend(["--status", filter.status.value])
            if filter.priority is not None:
                args.extend(["--priority", filter.priority])
            if filter.assignee_id is not None:
                args.extend(["--assignee-id", filter.assignee_id])
            if filter.label is not None:
                args.extend(["--label", filter.label])
            if filter.cursor is not None:
                args.extend(["--cursor", filter.cursor])
            if filter.limit is not None:
                args.extend(["--limit", str(filter.limit)])
        return self._run_json_decode_list(tuple(args), IssueSummary)

    def get(self, issue_id: str) -> Issue:
        return issue_from_wire(self._run_json_decode(("issue", "get", issue_id), IssueWire))

    def pull_requests(self, issue_id: str) -> tuple[LinkedPullRequest, ...]:
        args = ("issue", "pull-requests", issue_id)
        return self._run_json_decode_list((args), LinkedPullRequest)

    def children(self, issue_id: str) -> tuple[IssueChildStageGroup, ...]:
        return self._run_json_decode_list(("issue", "children", issue_id), IssueChildStageGroup)

    def create(self, request: IssueCreateRequest) -> Issue:
        args = ["issue", "create", "--title", request.title]
        desc = request.description_input
        if isinstance(desc, InlineDescription):
            args.extend(["--description", desc.text])
        elif isinstance(desc, FileDescription):
            args.extend(["--description-file", str(pathlib.Path(desc.path).resolve())])
        elif isinstance(desc, StdinDescription):  # type: ignore[misc]
            args.append("--description-stdin")
        if request.priority is not None:
            args.extend(["--priority", request.priority])
        if request.assignee_id is not None:
            args.extend(["--assignee-id", request.assignee_id])
        for label in request.label:
            args.extend(["--label", label])
        return issue_from_wire(self._run_json_decode(tuple(args), IssueWire))

    def update(self, issue_id: str, request: IssueUpdateRequest) -> Issue:
        args = ["issue", "update", issue_id]
        if request.title is not None:
            args.extend(["--title", request.title])
        if request.description is not None:
            args.extend(["--description", request.description])
        if request.priority is not None:
            args.extend(["--priority", request.priority])
        if request.assignee_id is not None:
            args.extend(["--assignee-id", request.assignee_id])
        return issue_from_wire(self._run_json_decode(tuple(args), IssueWire))

    def assign(self, request: IssueAssignmentRequest) -> Issue:
        args = ["issue", "assign", request.issue_id]
        if request.member_id is not None:
            args.extend(["--member-id", request.member_id])
        elif request.agent_id is not None:
            args.extend(["--agent-id", request.agent_id])
        elif request.squad_id is not None:
            args.extend(["--squad-id", request.squad_id])
        elif request.unassign:
            args.append("--unassign")
        return issue_from_wire(self._run_json_decode(tuple(args), IssueWire))

    def set_status(self, issue_id: str, status: IssueStatus) -> Issue:
        return issue_from_wire(
            self._run_json_decode(
                ("issue", "set-status", issue_id, "--status", status.value), IssueWire
            )
        )

    def deprioritize(self, issue_id: str) -> str:
        return self._transport.run_text(("issue", "deprioritize", issue_id)).text

    def reorder(self, request: IssueReorderRequest) -> Issue:
        args = ["issue", "reorder", request.issue_id]
        if request.before_id is not None:
            args.extend(["--before", request.before_id])
        elif request.after_id is not None:
            args.extend(["--after", request.after_id])
        elif request.top:
            args.append("--top")
        elif request.bottom:
            args.append("--bottom")
        return issue_from_wire(self._run_json_decode(tuple(args), IssueWire))

    def search(self, query: str) -> tuple[IssueSummary, ...]:
        return self._run_json_decode_list(("issue", "search", query), IssueSummary)

    def runs(self, issue_id: str) -> tuple[TaskRun, ...]:
        return self._run_json_decode_list(("issue", "runs", issue_id), TaskRun)

    def run_messages(self, issue_id: str, run_id: str) -> tuple[RunMessage, ...]:
        return self._run_json_decode_list(
            ("issue", "run-messages", issue_id, "--run-id", run_id), RunMessage
        )

    def usage(self, issue_id: str) -> IssueUsage:
        return self._run_json_decode(("issue", "usage", issue_id), IssueUsage)

    def rerun(self, issue_id: str, run_id: str) -> None:
        self._transport.run_text(("issue", "rerun", issue_id, "--run-id", run_id))

    def cancel_task(self, issue_id: str, run_id: str) -> None:
        self._transport.run_text(("issue", "cancel-task", issue_id, "--run-id", run_id))
