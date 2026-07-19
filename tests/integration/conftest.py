from __future__ import annotations

import os
import pathlib

import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig


@pytest.fixture
def fake_cli_client(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> MulticaClient:
    fake_dir = str(pathlib.Path(request.config.rootpath) / "tests" / "fixtures")
    monkeypatch.setenv("PATH", fake_dir + ":" + os.environ.get("PATH", ""))
    config = ClientConfig(executable="fake_multica.py")
    return MulticaClient(config)
