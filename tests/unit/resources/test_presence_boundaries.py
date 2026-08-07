from __future__ import annotations

from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import OutputShapeError
from multica_py.models.autopilots import AutopilotTriggerUpdate
from multica_py.resources.autopilots import Autopilot, AutopilotResource
from multica_py.resources.users import UserResource


def _transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    return transport


def test_trigger_update_empty_request_reads_autopilot_and_extracts_trigger() -> None:
    transport = _transport()
    resource = AutopilotResource(transport, ClientConfig())
    request = AutopilotTriggerUpdate()
    object_command = resource.trigger_update_command("a1", "tr1", request)
    direct_command = resource.trigger_update_command("a1", "tr1")

    assert (
        object_command.commands
        == direct_command.commands
        == ("multica autopilot get a1 --output json",)
    )
    transport.run_bytes.return_value = MagicMock(
        stdout=msgspec.json.encode(
            {
                "autopilot": {
                    "id": "a1",
                    "workspace_id": "w1",
                    "title": "AP",
                    "assignee_type": "member",
                    "assignee_id": "u1",
                    "status": "active",
                    "execution_mode": "create_issue",
                    "created_by_type": "member",
                    "created_by_id": "u1",
                },
                "triggers": [{"id": "tr1", "type": "webhook", "config": {}}],
            }
        ),
        argv=("autopilot", "get", "a1", "--output", "json"),
    )

    assert object_command.run().id == "tr1"
    transport.run_bytes.assert_called_once()


def test_trigger_update_empty_request_raises_typed_output_error_for_missing_trigger() -> None:
    transport = _transport()
    resource = AutopilotResource(transport, ClientConfig())
    transport.run_bytes.return_value = MagicMock(
        stdout=msgspec.json.encode(
            {
                "autopilot": {
                    "id": "a1",
                    "workspace_id": "w1",
                    "title": "AP",
                    "assignee_type": "member",
                    "assignee_id": "u1",
                    "status": "active",
                    "execution_mode": "create_issue",
                    "created_by_type": "member",
                    "created_by_id": "u1",
                },
                "triggers": [],
            }
        ),
        argv=("autopilot", "get", "a1", "--output", "json"),
    )

    with pytest.raises(OutputShapeError, match="trigger 'tr1' was not found"):
        resource.trigger_update_command("a1", "tr1").run()


def test_bound_trigger_empty_update_delegates_to_autopilot_get() -> None:
    transport = _transport()
    resource = AutopilotResource(transport, ClientConfig())
    client = MagicMock()
    client.autopilots = resource
    entity = Autopilot(
        id="a1",
        workspace_id="w1",
        title="AP",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        _client=client,
    )

    assert entity.trigger_update_command("tr1").commands == (
        "multica autopilot get a1 --output json",
    )
