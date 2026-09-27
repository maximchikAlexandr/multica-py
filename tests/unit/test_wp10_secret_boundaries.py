from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import _autopilot_from_wire, _AutopilotWire
from multica_py.config import ClientConfig
from multica_py.entities.autopilots import Autopilot
from multica_py.execution import CommandExecutor, ProcessHandle
from multica_py.models.autopilots import AutopilotTriggerRotateURL
from multica_py.resources.agents import AgentResource

TERMINAL_COMMAND_CASES = (
    ("login", "--token"),
    ("setup", "cloud"),
    ("setup", "self-host", "--url", "https://example.test"),
)


def test_autopilot_secrets_are_hidden_from_ordinary_entity_surfaces() -> None:
    secret = "webhook-token-sentinel"
    ordinary = Autopilot(
        id="autopilot-1",
        workspace_id="workspace-1",
        title="Build",
        assignee_type="agent",
        assignee_id="agent-1",
        status="active",
        execution_mode="manual",
        created_by_type="member",
        created_by_id="member-1",
        webhook_token=secret,
        webhook_path="/hooks/sentinel",
        webhook_url="https://example.test/hooks/sentinel",
    )

    assert ordinary.webhook_token is None
    assert secret not in repr(ordinary)
    assert secret not in repr(ordinary.to_dict())

    wire = _AutopilotWire(
        id="autopilot-1",
        workspace_id="workspace-1",
        title="Build",
        assignee_type="agent",
        assignee_id="agent-1",
        status="active",
        execution_mode="manual",
        created_by_type="member",
        created_by_id="member-1",
        webhook_token=secret,
        webhook_path="/hooks/sentinel",
        webhook_url="https://example.test/hooks/sentinel",
    )
    approved = _autopilot_from_wire(wire)
    assert approved.webhook_token == secret
    assert secret not in repr(approved)
    assert secret not in repr(approved.to_dict())


def test_rotate_url_model_redacts_secret_projection_and_repr() -> None:
    secret = "rotate-url-sentinel"
    result = AutopilotTriggerRotateURL(
        autopilot_id="autopilot-1",
        url=f"https://example.test/{secret}",
        path=f"/{secret}",
        token=secret,
    )

    assert secret not in repr(result)
    assert secret not in repr(result.to_dict())


@pytest.mark.parametrize("args", TERMINAL_COMMAND_CASES, ids=lambda args: args[0])
def test_interactive_auth_and_setup_commands_use_executor_terminal(
    args: tuple[str, ...],
) -> None:
    executor = MagicMock(spec=CommandExecutor)
    executor.terminal.return_value = MagicMock(spec=ProcessHandle)
    transport = CliTransport(ClientConfig(), executor=executor)

    process = transport.spawn(args)
    process.close()

    executor.terminal.assert_called_once()
    assert executor.terminal.call_args.args[0].argv == ("multica", *args)
    assert executor.spawn.call_count == 0


def test_secret_environment_result_masks_repr_but_preserves_approved_lookup() -> None:
    from multica_py.models.agents import SecretEnvironment

    secret = "environment-sentinel"
    result = SecretEnvironment({"API_TOKEN": secret})

    assert result["API_TOKEN"] == secret
    assert secret not in repr(result)
    assert secret not in str(result)
    assert isinstance(result, dict)


def test_secret_agent_env_rejects_before_io_with_redacted_diagnostic() -> None:
    secret = "agent-env-secret-sentinel"
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = AgentResource(transport, ClientConfig())

    with pytest.raises(ValueError, match=r"no safe input channel.*\*\*\*") as error:
        resource.env_set_command("agent-1", custom_env={"API_TOKEN": secret})

    assert secret not in str(error.value)
    transport.build_full_argv.assert_not_called()
    transport.run_bytes.assert_not_called()
    transport.spawn.assert_not_called()
    transport.terminal.assert_not_called()
