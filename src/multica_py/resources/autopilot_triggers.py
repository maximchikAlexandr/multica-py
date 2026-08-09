from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py._internal.wire_models import _AutopilotTriggerWire, trigger_from_wire
from multica_py.models.autopilots import (
    AutopilotTrigger,
)
from multica_py.models.common import ActionResult
from multica_py.resources._base import BaseResource


class AutopilotTriggerResource(BaseResource):
    def list(self, autopilot_id: str) -> tuple[AutopilotTrigger, ...]:
        wires = self._run_json_decode_list(
            ("autopilot", "trigger", "list", autopilot_id), _AutopilotTriggerWire
        )
        return tuple(trigger_from_wire(wire) for wire in wires)

    def create(
        self, autopilot_id: str, trigger_type: str, config: dict[str, str] | None = None
    ) -> AutopilotTrigger:
        args = ["autopilot", "trigger", "create", autopilot_id, "--type", trigger_type]
        if config:
            for k, v in config.items():
                args.extend(["--config", f"{k}={v}"])
        return trigger_from_wire(self._run_json_decode(tuple(args), _AutopilotTriggerWire))

    def delete_command(self, autopilot_id: str, trigger_id: str) -> Command[ActionResult[None]]:
        return self._action_command(
            ("autopilot", "trigger", "delete", autopilot_id, "--trigger-id", trigger_id)
        )

    def delete(self, autopilot_id: str, trigger_id: str) -> ActionResult[None]:
        return self.delete_command(autopilot_id, trigger_id).run()
