from __future__ import annotations

import pathlib
import subprocess
import sys
import tarfile

import pytest

import multica_py


def test_py_typed_exists():
    py_typed = pathlib.Path("src/multica_py/py.typed")
    assert py_typed.exists(), "py.typed marker must exist for PEP 561"


def test_package_importable():
    assert hasattr(multica_py, "MulticaClient")


def test_uvx_import():
    result = subprocess.run(
        [sys.executable, "-c", "import multica_py; print('ok')"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"


def test_sdist_contains_py_typed():
    dist = pathlib.Path("dist")
    sdists = list(dist.glob("*.tar.gz"))
    if not sdists:
        pytest.skip("No sdist found — build first")
    result = subprocess.run(
        ["tar", "-tzf", str(sdists[0])],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "py.typed" in result.stdout, "sdist missing py.typed"


def test_wheel_contains_py_typed():
    dist = pathlib.Path("dist")
    wheels = list(dist.glob("*.whl"))
    if not wheels:
        pytest.skip("No wheel found — build first")
    result = subprocess.run(
        ["python3", "-m", "zipfile", "-l", str(wheels[0])],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "multica_py/py.typed" in result.stdout


def test_sdist_excludes_local_tool_state(tmp_path: pathlib.Path) -> None:
    out_dir = tmp_path / "dist"
    out_dir.mkdir()
    result = subprocess.run(
        ["uv", "build", "--sdist", "--out-dir", str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    sdists = list(out_dir.glob("*.tar.gz"))
    assert sdists, "No sdist produced"

    with tarfile.open(sdists[0], "r:gz") as archive:
        names = archive.getnames()

    forbidden = (".opencode/", ".devlocal/", ".codebase-memory/", ".speckit-chat/", "node_modules/")
    for name in names:
        assert not any(part in name for part in forbidden), (
            f"sdist contains forbidden local tool state: {name}"
        )
