"""Artifact test: verify dist/ contains exactly one wheel and one sdist with expected contents.

No-skip invariant: deleting dist/ before this test must fail it.
"""

from __future__ import annotations

import pathlib
import subprocess
import tarfile
import zipfile

import pytest

pytestmark = [pytest.mark.packaging]


def test_dist_contains_one_wheel_and_one_sdist() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    dist = repo_root / "dist"
    if not dist.is_dir() or not list(dist.glob("*.whl")):
        subprocess.run(["uv", "build"], cwd=repo_root, check=True)
    assert dist.is_dir(), "dist/ directory not found - run `uv build` first"

    wheels = list(dist.glob("*.whl"))
    sdists = list(dist.glob("*.tar.gz"))
    assert len(wheels) == 1, f"expected exactly 1 wheel, found {len(wheels)}"
    assert len(sdists) == 1, f"expected exactly 1 sdist, found {len(sdists)}"

    wheel_path = wheels[0]
    sdist_path = sdists[0]

    with zipfile.ZipFile(wheel_path) as zf:
        wheel_names = zf.namelist()
    assert any("multica_py" in n for n in wheel_names), "wheel must include multica_py package"

    with tarfile.open(sdist_path) as tf:
        sdist_names = tf.getnames()
    assert any("src/multica_py" in n for n in sdist_names), "sdist must include src/multica_py"
