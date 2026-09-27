from __future__ import annotations

import datetime
import pathlib

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py.config import ClientConfig
from multica_py.enums import ProjectStatus
from multica_py.models.common import ActionResult
from multica_py.models.system import (
    DaemonLaunchOptions,
    RepositoryCheckoutResult,
    RuntimeDefinition,
    RuntimeProfiles,
    RuntimeUsage,
)
from multica_py.resources.agents import AgentResource
from multica_py.resources.auth import AuthResource
from multica_py.resources.daemon import DaemonResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.resources.projects import ProjectResource
from multica_py.resources.repositories import RepositoryResource
from multica_py.resources.runtime_profiles import RuntimeProfileResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.squads import SquadResource
from multica_py.resources.users import UserResource
from multica_py.resources.workspaces import WorkspaceResource
from tests.unit.resources._factories import make_transport


def test_repository_checkout_returns_frozen_path_result() -> None:
    transport = make_transport(text="/worktrees/acme\n")
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
    transport = make_transport(stdout={"MODE": "safe"})
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

    command = resource.env_set_command("agent-1", custom_env={"MODE": "safe"})
    assert command._plan.steps[0].argv == (
        "agent",
        "env",
        "set",
        "agent-1",
        "--custom-env",
        '{"MODE":"safe"}',
        "--output",
        "json",
    )
    assert command.commands == ("multica agent env set agent-1 --custom-env '***' --output json",)

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
    transport = make_transport(
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
    transport = make_transport(stdout={"id": "ws-1", "name": "Acme", "slug": "acme"})
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
    transport = make_transport(stdout={"id": "squad-1", "name": "Builders"})
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
    transport = make_transport(
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


def test_project_create_preserves_reviewed_fields() -> None:
    transport = make_transport(
        stdout={
            "id": "project-1",
            "title": "Parity",
            "status": "in_progress",
            "icon": "rocket",
            "lead_type": "member",
            "lead_id": "member-1",
            "start_date": "2026-09-01",
            "due_date": "2026-10-01",
            "resource_count": 2,
        }
    )
    resource = ProjectResource(transport, ClientConfig())
    project = resource.create(
        name="Parity",
        status=ProjectStatus.in_progress,
        icon="rocket",
        lead="member-1",
        start_date="2026-09-01",
        due_date="2026-10-01",
        repositories=("https://example.test/repo.git",),
    )
    assert project.icon == "rocket"
    assert project.lead_id == "member-1"
    assert project.resource_count == 2
    assert transport.run_bytes.call_args.args[0] == (
        "project",
        "create",
        "--title",
        "Parity",
        "--status",
        "in_progress",
        "--icon",
        "rocket",
        "--lead",
        "member-1",
        "--start-date",
        "2026-09-01",
        "--due-date",
        "2026-10-01",
        "--repo",
        "https://example.test/repo.git",
        "--output",
        "json",
    )


def test_project_update_preserves_explicit_clear_presence() -> None:
    transport = make_transport(stdout={"id": "project-1", "title": "Parity", "status": "paused"})
    resource = ProjectResource(transport, ClientConfig())
    resource.update("project-1", status=ProjectStatus.paused, due_date=None)
    assert transport.run_bytes.call_args.args[0] == (
        "project",
        "update",
        "project-1",
        "--status",
        "paused",
        "--due-date",
        "",
        "--output",
        "json",
    )


def test_project_resource_variants_labels_position_and_presence_are_mapped() -> None:
    transport = make_transport(
        stdout={
            "id": "resource-1",
            "project_id": "project-1",
            "resource_type": "github_repo",
            "resource_ref": {"url": "https://example.test/repo.git", "ref": "main"},
            "label": "primary",
            "position": 3,
        }
    )
    resource = ProjectResourceCollection(transport, ClientConfig())
    record = resource.add(
        "project-1",
        resource_type="github_repo",
        url="https://example.test/repo.git",
        ref={"url": "https://example.test/repo.git", "ref": "main"},
        label="primary",
    )
    assert record.resource_type == "github_repo"
    assert record.position == 3
    assert transport.run_bytes.call_args.args[0] == (
        "project",
        "resource",
        "add",
        "project-1",
        "--type",
        "github_repo",
        "--url",
        "https://example.test/repo.git",
        "--ref",
        '{"url":"https://example.test/repo.git","ref":"main"}',
        "--label",
        "primary",
        "--output",
        "json",
    )
    transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=msgspec.json.encode(
            {
                "id": "resource-1",
                "project_id": "project-1",
                "resource_type": "github_repo",
                "resource_ref": {"url": "https://example.test/repo.git"},
                "label": None,
                "position": 4,
            }
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    updated = resource.update("project-1", "resource-1", clear_label=True, position=4)
    assert updated.label is None and updated.position == 4
    with pytest.raises(ValueError, match="at least one"):
        resource.update_command("project-1", "resource-1")


def test_daemon_launch_log_and_auth_controls_preserve_presence() -> None:
    transport = make_transport(text="ok")
    daemon = DaemonResource(transport, ClientConfig())
    launch = DaemonLaunchOptions(
        daemon_id="daemon-1",
        device_name="Mac",
        runtime_name="Codex",
        workspaces_root="/var/lib/multica",
        ws_claim_poll_interval="10s",
        no_auto_update=True,
        no_auto_reload=True,
    )
    assert daemon.start_command(launch_options=launch).commands == (
        "multica daemon start --daemon-id daemon-1 --device-name Mac --runtime-name Codex "
        "--workspaces-root /var/lib/multica --ws-claim-poll-interval 10s "
        "--no-auto-update=true --no-auto-reload=true",
    )
    assert daemon.restart_command(launch_options=launch).commands == (
        "multica daemon restart --daemon-id daemon-1 --device-name Mac --runtime-name Codex "
        "--workspaces-root /var/lib/multica --ws-claim-poll-interval 10s "
        "--no-auto-update=true --no-auto-reload=true",
    )
    assert daemon.logs_command(lines=25, follow=True).commands == (
        "multica daemon logs --follow --lines 25",
    )
    auth = AuthResource(transport, ClientConfig())
    assert auth.login_command(callback_host="10.0.0.5").commands == (
        "multica login --callback-host 10.0.0.5",
    )
    assert auth.login_command(prompt_token=True).commands == ("multica login --token",)
    with pytest.raises(ValueError, match="nonblank"):
        auth.login_command(callback_host=" ")
    with pytest.raises(ValueError, match="combined"):
        auth.login_command("secret", prompt_token=True)


def test_runtime_rich_variants_decode_priced_usage_and_update_metadata() -> None:
    transport = make_transport(
        stdout=[
            {
                "id": "runtime-1",
                "name": "Codex",
                "provider": "openai",
                "profile_id": "profile-1",
                "device_name": "Mac",
                "status": "ready",
                "created_at": "2026-09-01T00:00:00Z",
            }
        ]
    )
    resource = RuntimeResource(transport, ClientConfig())
    definition = resource.list()[0]
    assert isinstance(definition, RuntimeDefinition)
    assert definition.profile_id == "profile-1"
    transport.run_bytes.return_value = RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=msgspec.json.encode(
            [
                {
                    "date": "2026-09-01",
                    "provider": "openai",
                    "model": "gpt-5",
                    "input_tokens": 1,
                    "output_tokens": 2,
                    "cache_read_tokens": 3,
                    "cache_write_tokens": 4,
                    "total_cost": 0.12,
                    "currency": "USD",
                }
            ]
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    usage = resource.usage("runtime-1")
    assert isinstance(usage[0], RuntimeUsage)
    assert usage[0].total_cost == 0.12 and usage[0].currency == "USD"


def test_user_profile_content_channels_preserve_safe_presence() -> None:
    resource = UserResource(make_transport(), ClientConfig())
    assert resource.profile_update_command(description_stdin="line one\nline two").commands == (
        "multica user profile update --description-stdin --output json",
    )
    assert resource.profile_update_command(
        description_file="profile.md", allow_external_file=True
    ).commands == (
        "multica user profile update --description-file "
        f"{pathlib.Path.cwd() / 'profile.md'} --allow-external-file --output json",
    )
    with pytest.raises(TypeError, match="combined"):
        resource.profile_update_command(description="inline", description_file="profile.md")
