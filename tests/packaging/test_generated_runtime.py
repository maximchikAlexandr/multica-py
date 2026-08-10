from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

import pytest


@pytest.mark.packaging
def test_artifacts_export_public_contract(tmp_path: pathlib.Path) -> None:
    root = pathlib.Path(__file__).parents[2]
    subprocess.run(["uv", "build"], cwd=root, check=True, env=_uv_env())
    wheels = sorted((root / "dist").glob("multica_py-*.whl"))
    sdists = sorted((root / "dist").glob("multica_py-*.tar.gz"))
    assert wheels and sdists

    for artifact in (*wheels, *sdists):
        empty = tmp_path / artifact.suffixes[-1].lstrip(".")
        empty.mkdir()
        venv = tmp_path / f"venv-{artifact.suffixes[-1].lstrip('.')}"
        subprocess.run(["uv", "venv", "--seed", str(venv)], cwd=root, check=True, env=_uv_env())
        python = venv / "bin" / "python"
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), "msgspec"],
            cwd=root,
            check=True,
            env=_uv_env(),
        )
        subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", str(artifact)],
            cwd=root,
            check=True,
            env=_uv_env(),
        )
        code = (
            "import pathlib, multica_py, multica_py.models as models, "
            "multica_py.enums, multica_py._generated.approved_sdk as generated; "
            "from multica_py.models.autopilots import AutopilotListPage, AutopilotRunListPage; "
            "from multica_py.models.issue_activity import MetadataPage; "
            "from multica_py.models.issues import IssueChildrenResult, IssueListFilter, IssueListPage; "
            "from multica_py.models.relations import CursorPage, OffsetPage; "
            "from multica_py.resources.cli import CliResult; "
            "assert hasattr(multica_py, 'Page') and hasattr(multica_py, 'ActionResult'); "
            "symbols = ('AutopilotListPage', 'AutopilotRunListPage', 'IssueChildrenResult', "
            "'IssueListFilter', 'IssueListPage', 'MetadataPage', 'CursorPage', 'OffsetPage'); "
            "assert all(hasattr(models, name) for name in symbols); "
            "assert all(not hasattr(multica_py, name) for name in symbols); "
            "assert not hasattr(multica_py, 'CliResult') and CliResult; "
            "assert (pathlib.Path(multica_py.__file__).parent / 'py.typed').is_file(); "
            "assert generated.IssueSort and generated.SortDirection; "
            "assert generated.TARGET_VERSION == generated.MIN_CLI_VERSION; "
            "assert generated.MAX_CLI_VERSION; "
            "assert generated.OPERATION_BINDINGS; "
            "assert all(hasattr(generated, name) for name in generated.__all__)"
        )
        subprocess.run(
            [str(python), "-c", code],
            cwd=empty,
            check=True,
            env={key: value for key, value in _uv_env().items() if key != "PYTHONPATH"},
        )


def _uv_env() -> dict[str, str]:
    env = dict(os.environ)
    env["UV_CACHE_DIR"] = str(pathlib.Path(tempfile.gettempdir()) / "multica-py-uv-cache")
    env.pop("PYTHONPATH", None)
    return env
