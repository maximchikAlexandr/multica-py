from __future__ import annotations

import datetime
import pathlib
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.common import ActionResult
from multica_py.models.system import RepositoryCheckoutResult, RuntimeProfiles
from multica_py.resources.agents import AgentResource
from multica_py.resources.repositories import RepositoryResource
from multica_py.resources.runtime_profiles import RuntimeProfileResource
from multica_py.resources.squads import SquadResource
from multica_py.resources.workspaces import WorkspaceResource


def _transport(*, stdout: object = None, text: str = "") -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    payload = b"" if stdout is None else msgspec.json.encode(stdout)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = RawCommandResult(
        argv=(), exit_code=0, stdout=payload, stderr=b"", duration=datetime.timedelta()
    )
    transport.run_text.return_value = TextResult(text=text, stderr="", exit_code=0)
    return transport


def test_repository_checkout_returns_frozen_path_result() -> None:
    transport = _transport(text="/worktrees/acme\n")
    resource = RepositoryResource(transport, ClientConfig())

    result = resource.checkout("https://example.test/acme.git", ref="main", fresh=True)

    assert result == RepositoryCheckoutResult(path="/worktrees/acme")
    assert result.path == str(pathlib.Path(result))
    transport.run_text.assert_called_once_with(
        (
            "repo",
            "checkout",
            "https://example.test/acme.git",
            "--ref",
            "main",
            "--fresh",
        ),
        stdin=None,
        timeout=None,
        minimum_cli_version="0.5.3",
    )


def test_agent_env_and_atomic_skill_add_use_reviewed_json_channels() -> None:
    transport = _transport(stdout={"MODE": "safe"})
    resource = AgentResource(transport, ClientConfig())

    assert resource.env_get("agent-1") == {"MODE": "safe"}
    assert transport.run_bytes.call_args.args[0] == (
        "agent",
        "env",
        "get",
        "agent-1",
        "--output",
        "json",
    )

    command = resource.env_set_command("agent-1", custom_env={"API_TOKEN": "secret-value"})
    assert "secret-value" not in command.commands[0]
    assert "--custom-env" in command.commands[0]

    transport.run_bytes.return_value = RawCommandResult(
        argv=(), exit_code=0, stdout=b"{}", stderr=b"", duration=datetime.timedelta()
    )
    result = resource.skills_add("agent-1", skill_ids=("skill-a", "skill-b"))
    assert result == ActionResult(value=None)
    assert transport.run_bytes.call_args.args[0] == (
        "agent",
        "skills",
        "add",
        "agent-1",
        "--skill-ids",
        '["skill-a","skill-b"]',
        "--output",
        "json",
    )


def test_agent_wire_preserves_system_configuration_fields() -> None:
    transport = _transport(
        stdout={
            "id": "agent-1",
            "name": "Builder",
            "service_tier": "premium",
            "permission_mode": "sandbox",
            "public_to_workspace": False,
            "public_to_member_ids": ["member-1"],
            "max_concurrent_tasks": 3,
            "custom_args": ["--fast"],
        }
    )
    agent = AgentResource(transport, ClientConfig()).get("agent-1")

    assert agent.service_tier == "premium"
    assert agent.permission_mode == "sandbox"
    assert agent.public_to_workspace is False
    assert agent.public_to_member_ids == ("member-1",)
    assert agent.max_concurrent_tasks == 3
    assert agent.custom_args == ("--fast",)


def test_workspace_mutations_decode_and_bind_existing_entities() -> None:
    transport = _transport(stdout={"id": "ws-1", "name": "Acme", "slug": "acme"})
    resource = WorkspaceResource(transport, ClientConfig())

    workspace = resource.create(name="Acme", slug="acme", context="build")
    assert workspace.id == "ws-1"
    assert workspace.slug == "acme"
    assert transport.run_bytes.call_args.args[0] == (
        "workspace",
        "create",
        "--name",
        "Acme",
        "--slug",
        "acme",
        "--context",
        "build",
        "--output",
        "json",
    )

    transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=msgspec.json.encode({"id": "member-1", "name": "Ada", "role": "admin"}),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    member = resource.member_invite("ada@example.test", "ws-1", role="admin")
    assert member.id == "member-1"
    assert transport.run_bytes.call_args.args[0] == (
        "workspace",
        "member",
        "invite",
        "ada@example.test",
        "ws-1",
        "--role",
        "admin",
        "--output",
        "json",
    )


def test_squad_mutations_and_member_role_share_reviewed_args() -> None:
    transport = _transport(stdout={"id": "squad-1", "name": "Builders"})
    resource = SquadResource(transport, ClientConfig())

    squad = resource.create(name="Builders", leader="agent-1")
    assert squad.id == "squad-1"
    assert transport.run_bytes.call_args.args[0] == (
        "squad",
        "create",
        "--name",
        "Builders",
        "--leader",
        "agent-1",
        "--output",
        "json",
    )

    transport.run_bytes.return_value = RawCommandResult(
        argv=(), exit_code=0, stdout=b"{}", stderr=b"", duration=datetime.timedelta()
    )
    assert resource.member_set_role("squad-1", "agent-1", role="reviewer") == ActionResult(
        value=None
    )
    assert transport.run_bytes.call_args.args[0] == (
        "squad",
        "member",
        "set-role",
        "squad-1",
        "--member-id",
        "agent-1",
        "--member-type",
        "agent",
        "--role",
        "reviewer",
        "--output",
        "json",
    )


def test_runtime_profiles_support_list_create_update_and_path_validation() -> None:
    transport = _transport(
        stdout={
            "profiles": [
                {
                    "id": "profile-1",
                    "runtime_type": "local",
                    "command_name": "claude",
                    "display_name": "Claude",
                    "enabled": True,
                }
            ]
        }
    )
    resource = RuntimeProfileResource(transport, ClientConfig())

    profiles = resource.list()
    assert isinstance(profiles, RuntimeProfiles)
    assert profiles[0].id == "profile-1"

    transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=msgspec.json.encode(
            {"id": "profile-1", "command_name": "claude", "display_name": "Claude"}
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    created = resource.create(runtime_type="local", command_name="claude", display_name="Claude")
    assert created.id == "profile-1"
    assert transport.run_bytes.call_args.args[0] == (
        "runtime",
        "profile",
        "create",
        "--runtime-type",
        "local",
        "--command-name",
        "claude",
        "--display-name",
        "Claude",
        "--output",
        "json",
    )

    with pytest.raises(ValueError, match="absolute"):
        resource.set_path_command("profile-1", pathlib.Path("relative"))
