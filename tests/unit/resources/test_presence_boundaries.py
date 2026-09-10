from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.entities.autopilots import Autopilot
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.users import UserResource


def _transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    return transport


@pytest.mark.parametrize("bound", (False, True), ids=("direct", "bound"))
def test_trigger_update_empty_request_rejects_before_transport(bound: bool) -> None:
    transport = _transport()
    resource = AutopilotResource(transport, ClientConfig())
    if bound:
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
        with pytest.raises(ValueError, match="at least one trigger update field"):
            entity.trigger_update_command("tr1")
    else:
        with pytest.raises(ValueError, match="at least one trigger update field"):
            resource.trigger_update_command("a1", "tr1")

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()
