from __future__ import annotations

import subprocess
import sys

import pytest

import multica_py


@pytest.mark.compat
def test_import_multica_py_compat() -> None:
    assert hasattr(multica_py, "MulticaClient")


@pytest.mark.compat
def test_bare_import_in_subprocess_compat() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import multica_py; print('ok')"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
