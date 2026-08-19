from __future__ import annotations

import pathlib

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.resources.workspace_mcp import WorkspaceMcpResource


def test_add_requires_exactly_one_config_channel() -> None:
    resource = WorkspaceMcpResource(CliTransport(ClientConfig()), ClientConfig())
    with pytest.raises(ValueError, match="exactly one"):
        resource.add_command("server-1")
    with pytest.raises(ValueError, match="exactly one"):
        resource.add_command(
            "server-1",
            server_config='{"token":"inline"}',
            server_config_stdin=True,
        )


def test_update_rejects_mixed_config_channels() -> None:
    resource = WorkspaceMcpResource(CliTransport(ClientConfig()), ClientConfig())
    with pytest.raises(ValueError, match="only one"):
        resource.update_command(
            "mcp_001",
            server_config='{"token":"inline"}',
            server_config_file="/tmp/config.json",
        )


def test_add_with_config_file_omits_inline_server_config(
    tmp_path: pathlib.Path,
) -> None:
    config_path = tmp_path / "server-config.json"
    config_path.write_text('{"token":"file-config"}', encoding="utf-8")
    resource = WorkspaceMcpResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.add_command("server-1", server_config_file=config_path)
    argv = command._plan.steps[0].argv
    assert "--server-config-file" in argv
    assert "--server-config" not in argv
    assert "--server-config-stdin" not in argv


def test_update_with_name_only_omits_config_flags() -> None:
    resource = WorkspaceMcpResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.update_command("mcp_001", name="renamed")
    argv = command._plan.steps[0].argv
    assert argv == (
        "workspace",
        "mcp",
        "update",
        "mcp_001",
        "--name",
        "renamed",
        "--output",
        "json",
    )
