from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile

import pytest

pytestmark = [pytest.mark.packaging, pytest.mark.timeout(120)]

_ARTIFACT_PATTERNS = {
    "wheel": "multica_py-*.whl",
    "sdist": "multica_py-*.tar.gz",
}


@pytest.fixture(scope="module")
def built_artifacts() -> dict[str, pathlib.Path]:
    root = pathlib.Path(__file__).parents[2]
    subprocess.run(["uv", "build"], cwd=root, check=True, env=_uv_env())
    matches = {
        kind: sorted((root / "dist").glob(pattern)) for kind, pattern in _ARTIFACT_PATTERNS.items()
    }
    assert all(matches.values())
    return {kind: paths[-1] for kind, paths in matches.items()}


@pytest.fixture(scope="module", params=tuple(_ARTIFACT_PATTERNS), ids=tuple(_ARTIFACT_PATTERNS))
def installed_artifact(
    request: pytest.FixtureRequest,
    built_artifacts: dict[str, pathlib.Path],
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[pathlib.Path, pathlib.Path]:
    kind = request.param
    artifact = built_artifacts[kind]
    empty = tmp_path_factory.mktemp(f"probe-{kind}")
    venv = empty / "venv"
    root = pathlib.Path(__file__).parents[2]
    subprocess.run(["uv", "venv", str(venv)], cwd=root, check=True, env=_uv_env())
    python = venv / "bin" / "python"
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            "--no-deps",
            "msgspec",
            str(artifact),
        ],
        cwd=root,
        check=True,
        env=_uv_env(),
    )
    return python, empty


@pytest.mark.parametrize("kind", tuple(_ARTIFACT_PATTERNS), ids=tuple(_ARTIFACT_PATTERNS))
def test_artifacts_are_exported(kind: str, built_artifacts: dict[str, pathlib.Path]) -> None:
    assert built_artifacts[kind].is_file()


def test_installed_artifact_visibility(
    installed_artifact: tuple[pathlib.Path, pathlib.Path],
) -> None:
    python, cwd = installed_artifact
    _run_probe(
        python,
        cwd,
        """
import pathlib

import multica_py
import multica_py.enums
import multica_py.models as models
from multica_py.models.autopilots import AutopilotListPage, AutopilotRunListPage
from multica_py.models.issue_activity import MetadataPage
from multica_py.models.issues import IssueChildrenResult, IssueListFilter, IssueListPage
from multica_py.models.relations import CursorPage, OffsetPage
from multica_py.resources.cli import CliResult

symbols = (
    "AutopilotListPage", "AutopilotRunListPage", "IssueChildrenResult", "IssueListFilter",
    "IssueListPage", "MetadataPage", "CursorPage", "OffsetPage",
)
assert hasattr(multica_py, "Page") and hasattr(multica_py, "ActionResult")
assert all(hasattr(models, name) for name in symbols)
assert all(not hasattr(multica_py, name) for name in symbols)
assert not hasattr(multica_py, "CliResult") and CliResult
assert (pathlib.Path(multica_py.__file__).parent / "py.typed").is_file()
""",
    )


def test_installed_artifact_version(
    installed_artifact: tuple[pathlib.Path, pathlib.Path],
) -> None:
    python, cwd = installed_artifact
    _run_probe(
        python,
        cwd,
        """
from multica_py._generated import approved_sdk as generated

assert generated.TARGET_VERSION == "0.5.3"
assert generated.MIN_CLI_VERSION == "0.4.42"
assert generated.MAX_CLI_VERSION == "0.5.4"
""",
    )


def test_installed_artifact_bindings(
    installed_artifact: tuple[pathlib.Path, pathlib.Path],
) -> None:
    python, cwd = installed_artifact
    _run_probe(
        python,
        cwd,
        """
from multica_py._generated import approved_sdk as generated

assert generated.OPERATION_BINDINGS
assert not any(name.startswith("PLUGIN_") for name in generated.__all__)
assert all(
    mapping.python_path != "priority"
    for binding in generated.OPERATION_BINDINGS
    for mapping in binding.mappings
    if binding.operation_id.startswith("autopilots.")
)
assert all(hasattr(generated, name) for name in generated.__all__)
""",
    )


def _run_probe(python: pathlib.Path, cwd: pathlib.Path, code: str) -> None:
    subprocess.run([str(python), "-c", code], cwd=cwd, check=True, env=_uv_env())


def _uv_env() -> dict[str, str]:
    env = dict(os.environ)
    env["UV_CACHE_DIR"] = str(pathlib.Path(tempfile.gettempdir()) / "multica-py-uv-cache")
    env.pop("PYTHONPATH", None)
    return env
