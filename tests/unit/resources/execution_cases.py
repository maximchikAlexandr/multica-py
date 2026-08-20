from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ProcessFileSecretCase:
    id: str
    option: str
    payload: bytes
    equals: bool = False


PROCESS_FILE_SECRET_CASES: tuple[ProcessFileSecretCase, ...] = (
    ProcessFileSecretCase("credential-file", "--credential-file", b"credential\x00\xff-secret"),
    ProcessFileSecretCase(
        "server-config-file", "--server-config-file", b"server-config\x00\xfe-secret"
    ),
    ProcessFileSecretCase(
        "credential-file-equals", "--credential-file", b"credential-equals\x00\xff-secret", True
    ),
    ProcessFileSecretCase(
        "server-config-file-equals",
        "--server-config-file",
        b"server-config-equals\x00\xfe-secret",
        True,
    ),
)


@dataclass(frozen=True)
class FileSecretSurfaceCase:
    id: str
    file_secret: ProcessFileSecretCase
    payload: bytes
    partial: str
    command_prefix: tuple[str, ...]


FILE_SECRET_SURFACE_CASES: tuple[FileSecretSurfaceCase, ...] = (
    FileSecretSurfaceCase(
        "credential-file-text",
        PROCESS_FILE_SECRET_CASES[0],
        b"file-credential-token",
        "file-credential-token",
        ("plugin", "remote-mcp", "configure", "inst_001", "remote-mcp"),
    ),
    FileSecretSurfaceCase(
        "server-config-file-nested-json",
        PROCESS_FILE_SECRET_CASES[1],
        b'{"headers":{"X-API-Key":"file-nested-token"}}',
        "file-nested-token",
        ("workspace", "mcp", "add", "server-1"),
    ),
    FileSecretSurfaceCase(
        "credential-file-opaque",
        PROCESS_FILE_SECRET_CASES[0],
        b"file-credential\x00\xff-secret",
        "file-credential",
        ("plugin", "remote-mcp", "configure", "inst_001", "remote-mcp"),
    ),
    FileSecretSurfaceCase(
        "server-config-file-opaque-json",
        PROCESS_FILE_SECRET_CASES[1],
        b'{"headers":{"X-API-Key":"file-config\xff-secret"}}',
        "file-config",
        ("workspace", "mcp", "add", "server-1"),
    ),
    FileSecretSurfaceCase(
        "credential-file-equals-text",
        PROCESS_FILE_SECRET_CASES[2],
        b"equals-credential-token",
        "equals-credential-token",
        ("plugin", "remote-mcp", "configure", "inst_001", "remote-mcp"),
    ),
    FileSecretSurfaceCase(
        "server-config-file-equals-text",
        PROCESS_FILE_SECRET_CASES[3],
        b'{"headers":{"X-API-Key":"equals-config-token"}}',
        "equals-config-token",
        ("workspace", "mcp", "add", "server-1"),
    ),
)


def file_secret_args(case: ProcessFileSecretCase, path: str | os.PathLike[str]) -> tuple[str, ...]:
    path_text = os.fspath(path)
    return (f"{case.option}={path_text}",) if case.equals else (case.option, path_text)


@dataclass(frozen=True)
class RemoteFileSecretCase:
    id: str
    file_secret: ProcessFileSecretCase
    provider: Literal["ssh", "microsandbox"]
    phase: Literal["run-success", "spawn-success", "run-nonzero", "spawn-nonzero"]
    expected_argv: Callable[[str, ProcessFileSecretCase], tuple[str, ...]]
    expected_exit_code: int
    expected_current_files: int = 0
    expected_removed_paths: int = 1


def _expected_remote_file_argv(staged_path: str, case: ProcessFileSecretCase) -> tuple[str, ...]:
    option = f"{case.option}={staged_path}" if case.equals else case.option
    value = () if case.equals else (staged_path,)
    return ("multica", "workspace", "mcp", "add", "server-1", option, *value)


_CREDENTIAL_FILE = PROCESS_FILE_SECRET_CASES[0]
_SERVER_CONFIG_FILE = PROCESS_FILE_SECRET_CASES[1]
_CREDENTIAL_FILE_EQUALS = PROCESS_FILE_SECRET_CASES[2]
_SERVER_CONFIG_FILE_EQUALS = PROCESS_FILE_SECRET_CASES[3]


REMOTE_FILE_SECRET_CASES: tuple[RemoteFileSecretCase, ...] = (
    RemoteFileSecretCase(
        "ssh-credential-run", _CREDENTIAL_FILE, "ssh", "run-success", _expected_remote_file_argv, 0
    ),
    RemoteFileSecretCase(
        "ssh-credential-spawn",
        _CREDENTIAL_FILE,
        "ssh",
        "spawn-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "ssh-credential-equals-run",
        _CREDENTIAL_FILE_EQUALS,
        "ssh",
        "run-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "ssh-credential-equals-spawn",
        _CREDENTIAL_FILE_EQUALS,
        "ssh",
        "spawn-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "ssh-server-config-run",
        _SERVER_CONFIG_FILE,
        "ssh",
        "run-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "ssh-server-config-spawn",
        _SERVER_CONFIG_FILE,
        "ssh",
        "spawn-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "ssh-server-config-equals-run",
        _SERVER_CONFIG_FILE_EQUALS,
        "ssh",
        "run-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "ssh-server-config-equals-spawn",
        _SERVER_CONFIG_FILE_EQUALS,
        "ssh",
        "spawn-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "microsandbox-credential-run",
        _CREDENTIAL_FILE,
        "microsandbox",
        "run-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "microsandbox-credential-spawn",
        _CREDENTIAL_FILE,
        "microsandbox",
        "spawn-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "microsandbox-credential-equals-run",
        _CREDENTIAL_FILE_EQUALS,
        "microsandbox",
        "run-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "microsandbox-credential-equals-spawn",
        _CREDENTIAL_FILE_EQUALS,
        "microsandbox",
        "spawn-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "microsandbox-server-config-run",
        _SERVER_CONFIG_FILE,
        "microsandbox",
        "run-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "microsandbox-server-config-spawn",
        _SERVER_CONFIG_FILE,
        "microsandbox",
        "spawn-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "microsandbox-server-config-equals-run",
        _SERVER_CONFIG_FILE_EQUALS,
        "microsandbox",
        "run-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "microsandbox-server-config-equals-spawn",
        _SERVER_CONFIG_FILE_EQUALS,
        "microsandbox",
        "spawn-success",
        _expected_remote_file_argv,
        0,
    ),
    RemoteFileSecretCase(
        "ssh-credential-nonzero-run",
        _CREDENTIAL_FILE,
        "ssh",
        "run-nonzero",
        _expected_remote_file_argv,
        2,
    ),
    RemoteFileSecretCase(
        "ssh-credential-nonzero-spawn",
        _CREDENTIAL_FILE,
        "ssh",
        "spawn-nonzero",
        _expected_remote_file_argv,
        2,
    ),
    RemoteFileSecretCase(
        "microsandbox-credential-nonzero-run",
        _CREDENTIAL_FILE,
        "microsandbox",
        "run-nonzero",
        _expected_remote_file_argv,
        2,
    ),
    RemoteFileSecretCase(
        "microsandbox-credential-nonzero-spawn",
        _CREDENTIAL_FILE,
        "microsandbox",
        "spawn-nonzero",
        _expected_remote_file_argv,
        2,
    ),
)
