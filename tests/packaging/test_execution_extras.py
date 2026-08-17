from __future__ import annotations

import pathlib
import tomllib

import pytest

pytestmark = [pytest.mark.packaging]


def test_execution_provider_extras_are_opt_in_and_version_bounded() -> None:
    pyproject = pathlib.Path(__file__).resolve().parents[2] / "pyproject.toml"
    metadata = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = metadata["project"]
    dependencies = project["dependencies"]
    extras = project["optional-dependencies"]

    assert all("microsandbox" not in dependency.lower() for dependency in dependencies)
    assert all("paramiko" not in dependency.lower() for dependency in dependencies)
    assert extras["microsandbox"] == ["microsandbox>=0.6,<0.7"]
    assert extras["vps"] == ["paramiko>=3,<4"]
