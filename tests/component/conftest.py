from __future__ import annotations

import os
import pathlib
from collections.abc import Callable
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from tests.fixtures.fake_multica import FakeMultica

FAKE_CLI_EXECUTABLE = "fake_multica"

_TOP_LEVEL_ATTRS: tuple[str, ...] = (
    "auth",
    "setup",
    "daemon",
    "workspaces",
    "issues",
    "projects",
    "labels",
    "agents",
    "skills",
    "autopilots",
    "repositories",
    "runtimes",
    "attachments",
    "configuration",
    "squads",
    "users",
    "maintenance",
)

_NESTED_ATTRS: dict[str, tuple[str, ...]] = {
    "agents": ("skills",),
    "autopilots": ("triggers",),
    "issues": ("comments", "labels", "metadata", "subscribers"),
    "projects": ("resources",),
    "skills": ("files",),
}


def _fake_cli_executable(fixtures_dir: pathlib.Path) -> str:
    return str(fixtures_dir / "fake_multica" / "__main__.py")


@pytest.fixture
def fake_cli() -> FakeMultica:
    """A programmable :class:`FakeMultica` for the current test.

    The fixture is per-test: each test gets a fresh instance with no shared
    mutable state. Tests drive the fake CLI by registering responses with
    :meth:`FakeMultica.build_response` and assert on them via the SDK
    transport mock.
    """
    return FakeMultica()


@pytest.fixture
def fake_cli_path() -> pathlib.Path:
    """Filesystem path of the ``fixtures`` directory containing ``fake_multica``."""
    return pathlib.Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def client_factory(
    monkeypatch: pytest.MonkeyPatch,
    fake_cli_path: pathlib.Path,
) -> Callable[..., MulticaClient]:
    """Factory for :class:`MulticaClient` configured against the fake CLI."""
    fixtures_dir = str(fake_cli_path)
    monkeypatch.setenv("PATH", fixtures_dir + ":" + os.environ.get("PATH", ""))

    def _make(**overrides: object) -> MulticaClient:
        config = ClientConfig(executable=_fake_cli_executable(fake_cli_path))
        if overrides:
            config = msgspec.structs.replace(config, **overrides)
        return MulticaClient(config)

    return _make


@pytest.fixture
def client(client_factory: Callable[..., MulticaClient]) -> MulticaClient:
    """A :class:`MulticaClient` wired to the fake CLI subprocess."""
    return client_factory()


@pytest.fixture
def fake_cli_client(client: MulticaClient) -> MulticaClient:
    """Back-compat alias for :func:`client`.

    Several pre-existing test modules were written against the older
    ``fake_cli_client`` fixture name; the new canonical name is ``client``.
    """
    return client


@pytest.fixture
def transport() -> MagicMock:
    """A mocked :class:`CliTransport` for unit-style assertions.

    Tests inject this on a :class:`MulticaClient` via
    :func:`install_transport` instead of relying on recursive private
    mutation.
    """
    return MagicMock(spec=CliTransport)


def install_transport(client: MulticaClient, transport: MagicMock) -> None:
    """Install a transport mock on every resource under ``client``.

    The :class:`MulticaClient` keeps a single transport, but the resource
    tree still holds nested resources that captured the real transport at
    construction time. This helper walks the known nested-resource structure
    (no recursive ``dir()`` walks) and rewires each one in one place.
    """
    setattr(client, "_transport", transport)
    for attr in (*_NESTED_ATTRS, *_TOP_LEVEL_ATTRS):
        resource = getattr(client, attr, None)
        if resource is None:
            continue
        setattr(resource, "_transport", transport)
        for nested in _NESTED_ATTRS.get(attr, ()):
            child = getattr(resource, nested, None)
            if child is not None:
                setattr(child, "_transport", transport)


def patch_client_transport(client: MulticaClient, transport: MagicMock) -> None:
    """Install a transport mock on the client and every nested resource."""
    install_transport(client, transport)
