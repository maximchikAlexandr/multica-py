"""Packaging test fixtures: ensure dist/ exists before artifact tests run.

No-skip invariant: if uv build fails, tests fail (not skip).
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DIST = REPO_ROOT / "dist"


def _has_artifacts() -> bool:
    return bool(DIST.is_dir() and DIST.glob("*.whl") and DIST.glob("*.tar.gz"))


@pytest.fixture(scope="session", autouse=True)
def _ensure_dist() -> None:
    if _has_artifacts():
        return
    if shutil.which("uv") is None:
        raise RuntimeError("uv not on PATH; cannot build dist/")
    DIST.mkdir(parents=True, exist_ok=True)
    for stale in DIST.glob("*"):
        stale.unlink()
    result = subprocess.run(
        ["uv", "build"],
        cwd=REPO_ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("uv build failed; packaging tests cannot run")
