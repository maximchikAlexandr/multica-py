from __future__ import annotations

import datetime
import pathlib
from collections.abc import Callable, Iterator
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.resources.cli import CliResource

_LAYER_MARKERS: dict[str, str] = {
    "tests/unit": "unit",
    "tests/contract": "contract",
    "tests/component": "component",
    "tests/packaging": "packaging",
}


def _repo_relative_path(path: pathlib.Path) -> str:
    tests_root = pathlib.Path(__file__).parent
    repo_root = tests_root.parent
    return path.relative_to(repo_root).as_posix()


def _layer_marker_for_path(path: pathlib.Path) -> str | None:
    normalized = _repo_relative_path(path)
    for prefix, marker in _LAYER_MARKERS.items():
        if normalized.startswith(prefix + "/") or normalized == prefix:
            return marker
    return None


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        layer_marker = _layer_marker_for_path(item.path)
        if layer_marker is not None:
            item.add_marker(getattr(pytest.mark, layer_marker))


@pytest.fixture
def mock_transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    from multica_py.execution import LocalExecutor

    transport.executor = LocalExecutor()
    return transport


@pytest.fixture
def raw_result() -> Callable[..., RawCommandResult]:
    def _raw_result(
        argv: tuple[str, ...] = (),
        *,
        stdout: bytes = b"",
        exit_code: int = 0,
        stderr: bytes = b"",
        duration: datetime.timedelta | None = None,
        secret_values: tuple[str, ...] = (),
        secret_bytes: tuple[bytes, ...] = (),
    ) -> RawCommandResult:
        return RawCommandResult(
            argv=argv,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration or datetime.timedelta(),
            secret_values=secret_values,
            secret_bytes=secret_bytes,
        )

    return _raw_result


@pytest.fixture
def client_with_transport(mock_transport: MagicMock) -> Iterator[tuple[MulticaClient, MagicMock]]:
    client = MulticaClient(ClientConfig())
    mock_transport._snapshot.side_effect = lambda _config: mock_transport
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client._transport = mock_transport
    for resource_name in (
        "issues",
        "projects",
        "agents",
        "squads",
        "autopilots",
    ):
        getattr(client, resource_name)._transport = mock_transport
    yield client, mock_transport
    client.close()


@pytest.fixture
def cli_resource_factory() -> Callable[..., tuple[CliResource, MagicMock]]:
    def _factory(config: ClientConfig | None = None) -> tuple[CliResource, MagicMock]:
        client = MulticaClient(config or ClientConfig())
        transport = MagicMock(spec=CliTransport)
        transport.build_full_argv.side_effect = lambda args: (
            str(client.config.executable),
            *args,
        )
        client.cli._transport = transport
        client.cli._config = client.config
        return client.cli, transport

    return _factory
