from __future__ import annotations

import os
import pathlib

import pytest


@pytest.fixture
def fake_multica_path() -> str:
    return str(pathlib.Path(__file__).parent / "fixtures")


@pytest.fixture
def fake_env(fake_multica_path: str) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = fake_multica_path + os.pathsep + env.get("PATH", "")
    return env
