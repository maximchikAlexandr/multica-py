from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

import multica_py


def test_import_multica_py():
    assert hasattr(multica_py, "MulticaClient")


def test_bare_import_in_subprocess():
    result = subprocess.run(
        [sys.executable, "-c", "import multica_py; print('ok')"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"


def test_wheel_install_and_run(tmp_path: pathlib.Path) -> None:
    dist = pathlib.Path("dist")
    wheels = list(dist.glob("*.whl"))
    if not wheels:
        pytest.skip("No wheel found")
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=False)
    pip = venv / "bin" / "pip"
    result = subprocess.run(
        [str(pip), "install", str(wheels[0])],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"pip install failed: {result.stderr}"
    result = subprocess.run(
        [str(venv / "bin" / "python"), "-c", "import multica_py; print('ok')"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Import after install failed: {result.stderr}"
