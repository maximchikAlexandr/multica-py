from __future__ import annotations

from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    AutopilotListWire,
    AutopilotRunListPageWire,
    AutopilotRunWire,
    AutopilotWire,
    autopilot_from_wire,
    autopilot_list_page_from_wire,
    autopilot_run_from_wire,
    autopilot_run_list_page_from_wire,
)
from multica_py.config import ClientConfig
from multica_py.enums import AutopilotExecutionMode
from multica_py.models.autopilots import (
    Autopilot,
    AutopilotListPage,
    AutopilotRun,
    AutopilotRunListPage,
)
from multica_py.resources._base import BaseResource
from multica_py.resources.autopilot_triggers import AutopilotTriggerResource


class AutopilotResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.triggers = AutopilotTriggerResource(transport, config)

    def list(self) -> AutopilotListPage:
        result = self._transport.run_bytes(("autopilot", "list", "--output", "json"))
        command = " ".join(result.argv)
        page = decode_json(result.stdout, AutopilotListWire, command=command)
        return autopilot_list_page_from_wire(page)

    def get(self, autopilot_id: str) -> Autopilot:
        return autopilot_from_wire(
            self._run_json_decode(("autopilot", "get", autopilot_id), AutopilotWire)
        )

    def create(
        self,
        title: str,
        *,
        description: str | None = None,
        agent: str,
        execution_mode: AutopilotExecutionMode,
        priority: str = "none",
        project_id: str | None = None,
        issue_title_template: str | None = None,
        subscribers: tuple[str, ...] = (),
    ) -> Autopilot:
        args = [
            "autopilot",
            "create",
            "--title",
            title,
            "--agent",
            agent,
            "--mode",
            execution_mode.value,
            "--priority",
            priority,
        ]
        if description is not None:
            args.extend(["--description", description])
        if project_id is not None:
            args.extend(["--project", project_id])
        if issue_title_template is not None:
            args.extend(["--issue-title-template", issue_title_template])
        if any(not ref.strip() for ref in subscribers):
            raise ValueError("subscribers must be nonblank")
        for ref in subscribers:
            args.extend(["--subscriber", ref])
        return autopilot_from_wire(self._run_json_decode(tuple(args), AutopilotWire))

    def update(
        self,
        autopilot_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        agent: str | None = None,
        project_id: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        execution_mode: AutopilotExecutionMode | None = None,
        issue_title_template: str | None = None,
        subscribers: tuple[str, ...] | None = None,
        clear_subscribers: bool = False,
    ) -> Autopilot:
        if clear_subscribers and subscribers is not None:
            raise ValueError("clear_subscribers and subscribers are mutually exclusive")
        if subscribers is not None and any(not ref.strip() for ref in subscribers):
            raise ValueError("subscribers must be nonblank")
        args = ["autopilot", "update", autopilot_id]
        if title is not None:
            args.extend(["--title", title])
        if description is not None:
            args.extend(["--description", description])
        if agent is not None:
            args.extend(["--agent", agent])
        if project_id is not None:
            args.extend(["--project", project_id])
        if priority is not None:
            args.extend(["--priority", priority])
        if status is not None:
            args.extend(["--status", status])
        if execution_mode is not None:
            args.extend(["--mode", execution_mode.value])
        if issue_title_template is not None:
            args.extend(["--issue-title-template", issue_title_template])
        if clear_subscribers:
            args.append("--clear-subscribers")
        elif subscribers is not None:
            for ref in subscribers:
                args.extend(["--subscriber", ref])
        return autopilot_from_wire(self._run_json_decode(tuple(args), AutopilotWire))

    def delete(self, autopilot_id: str) -> None:
        self._transport.run_text(("autopilot", "delete", autopilot_id))

    def run(self, autopilot_id: str) -> AutopilotRun:
        return autopilot_run_from_wire(
            self._run_json_decode(("autopilot", "run", autopilot_id), AutopilotRunWire)
        )

    def history(
        self,
        autopilot_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AutopilotRunListPage:
        if limit is not None and limit < 0:
            raise ValueError("limit must be nonnegative")
        if offset is not None and offset < 0:
            raise ValueError("offset must be nonnegative")
        args = ["autopilot", "runs", autopilot_id]
        if limit is not None:
            args.extend(["--limit", str(limit)])
        if offset is not None:
            args.extend(["--offset", str(offset)])
        page = self._run_json_decode(tuple(args), AutopilotRunListPageWire)
        return autopilot_run_list_page_from_wire(page, limit=limit, offset=offset)

    def get_run(self, run_id: str) -> AutopilotRun:
        return self._run_json_decode(("autopilot", "run", "get", run_id), AutopilotRun)
