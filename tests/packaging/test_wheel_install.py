from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest


@pytest.mark.compat
def test_wheel_install_smoke(tmp_path: pathlib.Path) -> None:
    dist = pathlib.Path("dist")
    wheels = list(dist.glob("*.whl"))
    if not wheels:
        pytest.skip("No wheel found; run uv build before compat wheel install")
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    pip = venv / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
    install = subprocess.run(
        [str(pip), "install", str(wheels[0])],
        capture_output=True,
        text=True,
        check=False,
    )
    assert install.returncode == 0, install.stderr
    python = venv / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    verify = subprocess.run(
        [str(python), "-c", "import multica_py; print('ok')"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert verify.returncode == 0, verify.stderr
