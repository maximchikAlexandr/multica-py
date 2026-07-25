from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest


@pytest.mark.packaging
def test_wheel_exports_generated_runtime(tmp_path: pathlib.Path) -> None:
    root = pathlib.Path(__file__).parents[2]
    subprocess.run(["uv", "build"], cwd=root, check=True, env=_uv_env())
    empty = tmp_path / "empty"
    empty.mkdir()
    venv = tmp_path / "venv"
    subprocess.run(["uv", "venv", "--seed", str(venv)], cwd=root, check=True, env=_uv_env())
    wheels = sorted((root / "dist").glob("multica_py-*.whl"))
    assert wheels
    python = venv / "bin" / "python"
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), "msgspec"],
        cwd=root,
        check=True,
        env=_uv_env(),
    )
    subprocess.run(
        [str(python), "-m", "pip", "install", "--no-deps", str(wheels[-1])],
        cwd=root,
        check=True,
        env=_uv_env(),
    )
    code = (
        "import multica_py, multica_py.enums, multica_py._generated.approved_sdk as generated; "
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
    env["UV_CACHE_DIR"] = "/private/tmp/multica-py-uv-cache"
    env.pop("PYTHONPATH", None)
    return env
