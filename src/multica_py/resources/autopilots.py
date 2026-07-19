from __future__ import annotations

from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import AutopilotListWire
from multica_py.config import ClientConfig
from multica_py.exceptions import OutputShapeError
from multica_py.models.autopilots import Autopilot, AutopilotRun
from multica_py.resources._base import BaseResource
from multica_py.resources.autopilot_triggers import AutopilotTriggerResource


class AutopilotResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.triggers = AutopilotTriggerResource(transport, config)

    def list(self) -> tuple[Autopilot, ...]:
        result = self._transport.run_bytes(("autopilot", "list", "--output", "json"))
        command = " ".join(result.argv)
        try:
            page = decode_json(result.stdout, AutopilotListWire, command=command)
        except OutputShapeError:
            items = decode_json(result.stdout, list[Autopilot], command=command)
            return tuple(items)
        else:
            return page.autopilots

    def get(self, autopilot_id: str) -> Autopilot:
        return self._run_json_decode(("autopilot", "get", autopilot_id), Autopilot)

    def create(self, name: str) -> Autopilot:
        return self._run_json_decode(("autopilot", "create", "--name", name), Autopilot)

    def update(
        self, autopilot_id: str, name: str | None = None, enabled: bool | None = None
    ) -> Autopilot:
        args = ["autopilot", "update", autopilot_id]
        if name is not None:
            args.extend(["--name", name])
        if enabled is not None:
            args.extend(["--enabled", str(enabled).lower()])
        return self._run_json_decode(tuple(args), Autopilot)

    def delete(self, autopilot_id: str) -> None:
        self._transport.run_text(("autopilot", "delete", autopilot_id))

    def run(self, autopilot_id: str) -> AutopilotRun:
        return self._run_json_decode(("autopilot", "run", autopilot_id), AutopilotRun)

    def history(self, autopilot_id: str) -> tuple[AutopilotRun, ...]:
        return self._run_json_decode_list(("autopilot", "history", autopilot_id), AutopilotRun)

    def get_run(self, run_id: str) -> AutopilotRun:
        return self._run_json_decode(("autopilot", "run", "get", run_id), AutopilotRun)
