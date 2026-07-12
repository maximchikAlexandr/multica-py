from __future__ import annotations

import pathlib


def test_py_typed_in_package():
    pkg_dir = pathlib.Path("src/multica_py")
    assert (pkg_dir / "py.typed").exists()
