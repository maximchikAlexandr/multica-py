from __future__ import annotations

import pathlib

import pytest


def test_writing_ok_respects_check_and_dry_run() -> None:
    from multica_py._internal.upstream_contract import files

    assert files.writing_ok(check=True, dry_run=False) is False
    assert files.writing_ok(check=True, dry_run=False, output="/tmp/report.json") is True
    assert files.writing_ok(check=False, dry_run=True) is False
    assert files.writing_ok(check=False, dry_run=False) is True


def test_atomic_write_files_writes_all_paths(tmp_path: pathlib.Path) -> None:
    from multica_py._internal.upstream_contract import files

    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    files.atomic_write_files({first: b"{}", second: b"[]"})
    assert first.read_bytes() == b"{}"
    assert second.read_bytes() == b"[]"
