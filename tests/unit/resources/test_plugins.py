from __future__ import annotations

import pathlib

import pytest

from multica_py._internal.redaction import collect_secret_values
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.resources.plugins import PluginResource


def test_configure_remote_mcp_credential_stdin_inherits_without_fixture_bytes() -> None:
    resource = PluginResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.configure_remote_mcp_command(
        "inst_001",
        "remote-mcp",
        endpoint="https://mcp.example.com",
        credential_stdin=True,
    )
    step = command._plan.steps[0]
    assert step.stdin is None
    assert "--credential-stdin" in step.argv
    assert "secret-token" not in step.argv


def test_configure_remote_mcp_rejects_mixed_credential_channels() -> None:
    resource = PluginResource(CliTransport(ClientConfig()), ClientConfig())
    with pytest.raises(ValueError, match="mutually exclusive"):
        resource.configure_remote_mcp_command(
            "inst_001",
            "remote-mcp",
            endpoint="https://mcp.example.com",
            credential_file="/tmp/credential.txt",
            credential_stdin=True,
        )


def test_collect_secret_values_reads_credential_file_contents_not_path(
    tmp_path: pathlib.Path,
) -> None:
    credential_path = tmp_path / "credential.txt"
    credential_path.write_text("file-secret-token", encoding="utf-8")
    argv = (
        "plugin",
        "remote-mcp",
        "configure",
        "inst_001",
        "remote-mcp",
        "--credential-file",
        str(credential_path),
    )
    secrets = collect_secret_values(argv)
    assert secrets == ("file-secret-token",)
    assert str(credential_path) not in secrets


def test_collect_secret_values_reads_credential_stdin_contents() -> None:
    argv = ("plugin", "remote-mcp", "configure", "inst_001", "remote-mcp", "--credential-stdin")
    assert collect_secret_values(argv, stdin=b"stdin-secret") == ("stdin-secret",)
    assert collect_secret_values(argv, stdin=None) == ()


def test_collect_secret_values_reads_server_config_file_contents_not_path(
    tmp_path: pathlib.Path,
) -> None:
    config_path = tmp_path / "server-config.json"
    config_path.write_text('{"token":"file-config-secret"}', encoding="utf-8")
    argv = (
        "workspace",
        "mcp",
        "add",
        "server-1",
        "--server-config-file",
        str(config_path),
    )
    secrets = collect_secret_values(argv)
    assert secrets == ('{"token":"file-config-secret"}',)
    assert str(config_path) not in secrets


def test_collect_secret_values_reads_server_config_stdin_contents() -> None:
    argv = ("workspace", "mcp", "add", "server-1", "--server-config-stdin")
    assert collect_secret_values(argv, stdin=b'{"token":"stdin-config"}') == (
        '{"token":"stdin-config"}',
    )
    assert collect_secret_values(argv, stdin=None) == ()


def test_collect_secret_values_reads_inline_server_config() -> None:
    argv = (
        "workspace",
        "mcp",
        "add",
        "server-1",
        "--server-config",
        '{"token":"inline-config"}',
    )
    assert collect_secret_values(argv) == ('{"token":"inline-config"}',)


def test_collect_secret_values_ignores_plaintext_credential_flag() -> None:
    argv = (
        "plugin",
        "remote-mcp",
        "configure",
        "inst_001",
        "remote-mcp",
        "--credential",
        "inline-credential",
    )
    assert collect_secret_values(argv) == ()


def test_plugin_install_builds_exact_argv_without_local_refusal() -> None:
    resource = PluginResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.install_command("/tmp/plugin-bundle")
    assert command._plan.steps[0].argv == (
        "plugin",
        "install",
        "/tmp/plugin-bundle",
        "--output",
        "json",
    )


def test_remote_mcp_configure_builds_exact_argv_without_local_refusal() -> None:
    resource = PluginResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.configure_remote_mcp_command(
        "inst_001",
        "remote-mcp",
        endpoint="https://mcp.example.com",
        credential_stdin=True,
    )
    assert command._plan.steps[0].argv == (
        "plugin",
        "remote-mcp",
        "configure",
        "inst_001",
        "remote-mcp",
        "--endpoint",
        "https://mcp.example.com",
        "--output",
        "json",
        "--credential-stdin",
    )


def test_plugin_validate_rejects_blank_source_before_transport() -> None:
    resource = PluginResource(CliTransport(ClientConfig()), ClientConfig())
    with pytest.raises(ValueError, match="nonblank"):
        resource.validate_command("   ")


def test_plugin_approve_remote_mcp_requires_tools_before_transport() -> None:
    resource = PluginResource(CliTransport(ClientConfig()), ClientConfig())
    with pytest.raises(ValueError, match="tools"):
        resource.approve_remote_mcp_command("inst_001", "remote-mcp", tools=())
