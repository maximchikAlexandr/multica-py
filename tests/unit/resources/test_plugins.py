from __future__ import annotations

import pathlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal
from unittest.mock import MagicMock

import pytest

from multica_py._internal.redaction import (
    collect_diagnostic_secret_bytes,
    collect_secret_values,
)
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.execution import ExecutionRequest, ExecutionResult, LocalExecutor
from multica_py.resources.plugins import PluginResource
from multica_py.resources.workspace_mcp import WorkspaceMcpResource


@dataclass(frozen=True)
class SecretChannelResourceCase:
    id: str
    resource: Literal["plugin", "workspace"]
    channel: Literal["stdin", "file"]
    payload: bytes


_SECRET_CHANNEL_RESOURCE_CASES: tuple[SecretChannelResourceCase, ...] = (
    SecretChannelResourceCase("plugin-credential-stdin", "plugin", "stdin", b"plugin-stdin"),
    SecretChannelResourceCase("plugin-credential-file", "plugin", "file", b"plugin-file"),
    SecretChannelResourceCase("workspace-config-stdin", "workspace", "stdin", b"mcp-stdin"),
    SecretChannelResourceCase("workspace-config-file", "workspace", "file", b"mcp-file"),
)


@pytest.mark.parametrize("case", _SECRET_CHANNEL_RESOURCE_CASES, ids=lambda case: case.id)
def test_secret_channel_resources_use_frozen_full_argv_and_run_bytes(
    case: SecretChannelResourceCase,
    tmp_path: pathlib.Path,
    mock_transport: MagicMock,
    raw_result: Callable[..., RawCommandResult],
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    config = ClientConfig()
    path = tmp_path / f"{case.id}.bin"
    path.write_bytes(case.payload)
    stdin = case.payload if case.channel == "stdin" else None
    expected: tuple[str, ...]

    if case.resource == "plugin":
        plugin_resource = PluginResource(mock_transport, config)
        if case.channel == "stdin":
            plugin_command = plugin_resource.configure_remote_mcp_command(
                "inst_001",
                "remote-mcp",
                endpoint="https://mcp.example.com",
                credential_stdin=case.payload,
            )
            expected = (
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
        else:
            plugin_command = plugin_resource.configure_remote_mcp_command(
                "inst_001",
                "remote-mcp",
                endpoint="https://mcp.example.com",
                credential_file=path,
            )
            expected = (
                "plugin",
                "remote-mcp",
                "configure",
                "inst_001",
                "remote-mcp",
                "--endpoint",
                "https://mcp.example.com",
                "--output",
                "json",
                "--credential-file",
                str(path),
            )
        mock_transport.run_bytes.return_value = raw_result(stdout=b"{}")
        assert plugin_command.run() == {}
    else:
        workspace_resource = WorkspaceMcpResource(mock_transport, config)
        if case.channel == "stdin":
            workspace_command = workspace_resource.add_command(
                "server-1", server_config_stdin=case.payload
            )
            expected = (
                "workspace",
                "mcp",
                "add",
                "server-1",
                "--server-config-stdin",
                "--output",
                "json",
            )
        else:
            workspace_command = workspace_resource.add_command("server-1", server_config_file=path)
            expected = (
                "workspace",
                "mcp",
                "add",
                "server-1",
                "--server-config-file",
                str(path),
                "--output",
                "json",
            )
        mock_transport.run_bytes.return_value = raw_result(stdout=b"[]")
        assert workspace_command.run().items == ()

    mock_transport.run_bytes.assert_called_once_with(expected, stdin=stdin, timeout=None)


@dataclass(frozen=True)
class TypedDecodeSecretCase:
    id: str
    resource: Literal["plugin", "workspace"]
    channel: Literal["stdin", "file"]
    payload: bytes


_TYPED_DECODE_SECRET_CASES: tuple[TypedDecodeSecretCase, ...] = (
    TypedDecodeSecretCase("plugin-stdin", "plugin", "stdin", b"plugin-typed-stdin"),
    TypedDecodeSecretCase("plugin-file", "plugin", "file", b"plugin-typed-file"),
    TypedDecodeSecretCase("workspace-stdin", "workspace", "stdin", b"mcp-typed-stdin"),
    TypedDecodeSecretCase("workspace-file", "workspace", "file", b"mcp-typed-file"),
)


class _JsonExecutor(LocalExecutor):
    def __init__(self, stdout: bytes) -> None:
        self.stdout = stdout
        self.requests: list[ExecutionRequest] = []

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        self.requests.append(request)
        return ExecutionResult(0, self.stdout, b"")


@pytest.mark.parametrize("case", _TYPED_DECODE_SECRET_CASES, ids=lambda case: case.id)
def test_typed_decoders_receive_unredacted_success_json_for_secret_channels(
    case: TypedDecodeSecretCase, tmp_path: pathlib.Path
) -> None:
    config = ClientConfig(
        environment=(
            ("API_TOKEN", "1"),
            ("MULTICA_TOKEN", "abc123"),
            ("THIRD_PARTY_API_KEY", "abc"),
        )
    )
    output = (
        b'{"count":1,"name":"' + case.payload + b'","overlap":"abc123"}'
        if case.resource == "plugin"
        else b'[{"id":"1","name":"' + case.payload + b'","transport":"abc123","enabled":true}]'
    )
    executor = _JsonExecutor(output)
    transport = CliTransport(config, executor=executor)
    path = tmp_path / f"{case.id}.bin"
    path.write_bytes(case.payload)
    expected: tuple[str, ...]

    if case.resource == "plugin":
        plugin_resource = PluginResource(transport, config)
        if case.channel == "stdin":
            plugin_command = plugin_resource.configure_remote_mcp_command(
                "inst_001",
                "remote-mcp",
                endpoint="https://mcp.example.com",
                credential_stdin=case.payload,
            )
            expected = (
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
        else:
            plugin_command = plugin_resource.configure_remote_mcp_command(
                "inst_001",
                "remote-mcp",
                endpoint="https://mcp.example.com",
                credential_file=path,
            )
            expected = (
                "plugin",
                "remote-mcp",
                "configure",
                "inst_001",
                "remote-mcp",
                "--endpoint",
                "https://mcp.example.com",
                "--output",
                "json",
                "--credential-file",
                str(path),
            )
        plugin_result = plugin_command.run()
        assert plugin_result == {
            "count": 1,
            "name": case.payload.decode(),
            "overlap": "abc123",
        }
    else:
        workspace_resource = WorkspaceMcpResource(transport, config)
        if case.channel == "stdin":
            workspace_command = workspace_resource.add_command(
                "server-1", server_config_stdin=case.payload
            )
            expected = (
                "workspace",
                "mcp",
                "add",
                "server-1",
                "--server-config-stdin",
                "--output",
                "json",
            )
        else:
            workspace_command = workspace_resource.add_command("server-1", server_config_file=path)
            expected = (
                "workspace",
                "mcp",
                "add",
                "server-1",
                "--server-config-file",
                str(path),
                "--output",
                "json",
            )
        workspace_result = workspace_command.run()
        assert workspace_result.items[0].id == "1"
        assert workspace_result.items[0].name == case.payload.decode()
        assert workspace_result.items[0].transport == "abc123"

    assert executor.requests[0].argv == ("multica", *expected)
    assert executor.requests[0].stdin == (case.payload if case.channel == "stdin" else None)


def test_file_secret_channels_are_not_read_during_preview(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    config = ClientConfig()
    plugin = PluginResource(CliTransport(config), config)
    workspace_mcp = WorkspaceMcpResource(CliTransport(config), config)

    def fail_open(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("preview performed file I/O")

    monkeypatch.setattr("builtins.open", fail_open)
    credential_path = tmp_path / "missing-credential.bin"
    server_config_path = tmp_path / "missing-server-config.bin"
    plugin_command = plugin.configure_remote_mcp_command(
        "inst_001",
        "remote-mcp",
        endpoint="https://mcp.example.com",
        credential_file=credential_path,
    )
    workspace_command = workspace_mcp.add_command("server-1", server_config_file=server_config_path)

    assert plugin_command.commands == (
        "multica plugin remote-mcp configure inst_001 remote-mcp --endpoint "
        "https://mcp.example.com --output json --credential-file "
        f"{credential_path}",
    )
    assert workspace_command.commands == (
        f"multica workspace mcp add server-1 --server-config-file {server_config_path} --output json",
    )


def test_configure_remote_mcp_rejects_mixed_credential_channels() -> None:
    resource = PluginResource(CliTransport(ClientConfig()), ClientConfig())
    with pytest.raises(ValueError, match="mutually exclusive"):
        resource.configure_remote_mcp_command(
            "inst_001",
            "remote-mcp",
            endpoint="https://mcp.example.com",
            credential_file="/tmp/credential.txt",
            credential_stdin=b"stdin-credential",
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


def test_collect_binary_file_secret_is_best_effort_text_and_exact_bytes(
    tmp_path: pathlib.Path,
) -> None:
    credential_path = tmp_path / "credential.bin"
    payload = b"binary-file-secret\x00\xff"
    credential_path.write_bytes(payload)
    argv = ("plugin", "remote-mcp", "configure", "--credential-file", str(credential_path))

    assert collect_secret_values(argv) == ("binary-file-secret\x00\ufffd",)
    assert collect_diagnostic_secret_bytes(argv) == (payload,)


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
    assert secrets == ('{"token":"file-config-secret"}', "file-config-secret")
    assert str(config_path) not in secrets


def test_collect_secret_values_reads_server_config_stdin_contents() -> None:
    argv = ("workspace", "mcp", "add", "server-1", "--server-config-stdin")
    assert collect_secret_values(argv, stdin=b'{"token":"stdin-config"}') == (
        '{"token":"stdin-config"}',
        "stdin-config",
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
    assert collect_secret_values(argv) == ('{"token":"inline-config"}', "inline-config")


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


def test_secret_channels_are_redacted_from_public_command_previews(
    tmp_path: pathlib.Path,
) -> None:
    config = ClientConfig()
    plugin = PluginResource(CliTransport(config), config)
    workspace_mcp = WorkspaceMcpResource(CliTransport(config), config)
    file_path = tmp_path / "server-config.json"
    file_path.write_text('{"headers":{"X-API-Key":"file-preview-token"}}', encoding="utf-8")
    cases = (
        (
            plugin.configure_remote_mcp_command(
                "inst_001",
                "remote-mcp",
                endpoint="https://mcp.example.com",
                credential_stdin=b"stdin-preview-token",
            ),
            "stdin-preview-token",
        ),
        (
            plugin.configure_remote_mcp_command(
                "inst_001",
                "remote-mcp",
                endpoint="https://mcp.example.com",
                auth_header="X-API-Key: header-preview-token",
            ),
            "header-preview-token",
        ),
        (
            workspace_mcp.add_command(
                "server-1",
                server_config='{"headers":{"X-API-Key":"inline-preview-token"}}',
            ),
            "inline-preview-token",
        ),
        (
            workspace_mcp.add_command("server-1", server_config_file=file_path),
            "file-preview-token",
        ),
    )
    for command, secret in cases:
        rendered = " ".join(command.commands)
        assert secret not in rendered
        assert secret not in repr(command)


def test_binary_file_secret_channels_do_not_break_command_preview(
    tmp_path: pathlib.Path,
) -> None:
    config = ClientConfig()
    plugin = PluginResource(CliTransport(config), config)
    workspace_mcp = WorkspaceMcpResource(CliTransport(config), config)
    credential_path = tmp_path / "credential.bin"
    server_config_path = tmp_path / "server-config.bin"
    credential_path.write_bytes(b"credential-preview\x00\xff")
    server_config_path.write_bytes(b"server-config-preview\x00\xff")

    commands = (
        plugin.configure_remote_mcp_command(
            "inst_001",
            "remote-mcp",
            endpoint="https://mcp.example.com",
            credential_file=credential_path,
        ),
        workspace_mcp.add_command("server-1", server_config_file=server_config_path),
    )
    for command in commands:
        rendered = " ".join(command.commands)
        assert "credential-preview" not in rendered
        assert "server-config-preview" not in rendered


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
        credential_stdin=b"stdin-credential",
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
