from __future__ import annotations

import os
import shutil
from collections.abc import Iterator

import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy

_REQUIRED_ENVIRONMENT = (
    "MULTICA_LIVE_CLI",
    "MULTICA_LIVE_EXPECTED_VERSION",
    "MULTICA_LIVE_SERVER_URL",
    "MULTICA_LIVE_WORKSPACE_ID",
    "MULTICA_LIVE_PROFILE",
)


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise pytest.UsageError(f"{name} must be set for live smoke tests")
    return value


@pytest.fixture(scope="session")
def prepared_client() -> Iterator[MulticaClient]:
    values = {name: _required_environment(name) for name in _REQUIRED_ENVIRONMENT}
    executable = shutil.which(values["MULTICA_LIVE_CLI"])
    if executable is None:
        raise pytest.UsageError(
            f"MULTICA_LIVE_CLI is not an executable: {values['MULTICA_LIVE_CLI']}"
        )

    config = ClientConfig(
        executable=executable,
        server_url=values["MULTICA_LIVE_SERVER_URL"],
        workspace_id=values["MULTICA_LIVE_WORKSPACE_ID"],
        profile=values["MULTICA_LIVE_PROFILE"],
        compatibility=CompatibilityPolicy.strict,
    )
    with MulticaClient(config) as client:
        yield client
