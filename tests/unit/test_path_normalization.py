from __future__ import annotations

import pathlib

import pytest

from multica_py.models.project_resources import LocalDirectoryResourceRef


@pytest.mark.compat
def test_local_directory_resource_ref_requires_absolute_path() -> None:
    with pytest.raises(ValueError, match="local_path must be an absolute path"):
        LocalDirectoryResourceRef(
            local_path="relative/path",
            daemon_id="daemon-001",
        )


@pytest.mark.compat
def test_local_directory_resource_ref_accepts_canonical_absolute_path() -> None:
    canonical = str(pathlib.Path("/tmp/sandbox").resolve())
    ref = LocalDirectoryResourceRef(
        local_path=canonical,
        daemon_id="daemon-001",
    )
    assert ref.local_path == canonical
