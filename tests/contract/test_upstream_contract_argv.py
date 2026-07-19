from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import uuid
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import cast

import pytest

from tests.fixtures.fake_multica import _validate_record_path

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
FAKE_BINARY = ROOT / "tests" / "fixtures" / "fake_multica.py"
RECORD_ROOT = FAKE_BINARY.parent / "_tmp"


@contextmanager
def _record_file(tmp_path: pathlib.Path, name: str) -> Generator[pathlib.Path, None, None]:
    parent_dir = RECORD_ROOT / tmp_path.name
    record_dir = parent_dir / uuid.uuid4().hex[:8]
    record_dir.mkdir(parents=True, exist_ok=True)
    record = record_dir / name
    record.unlink(missing_ok=True)
    _validate_record_path(str(record))
    try:
        yield record
    finally:
        record.unlink(missing_ok=True)
        record_dir.rmdir()
        parent_dir.rmdir()


def _run_argv(
    argv: Sequence[str],
    record: pathlib.Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    e = {"PATH": "/usr/bin:/bin", "MULTICA_FAKE_RECORD": str(record)}
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, str(FAKE_BINARY), *argv],
        check=False,
        capture_output=True,
        text=True,
        env=e,
    )


def test_argv_contract_simple_invocation(tmp_path: pathlib.Path) -> None:
    with _record_file(tmp_path, "argv_record.jsonl") as record:
        result = _run_argv(["auth", "status"], record)
        assert result.returncode == 0
        lines = record.read_text().strip().splitlines()
        assert lines, "expected at least one invocation"
        inv = cast("dict[str, object]", json.loads(lines[0]))
        assert inv.get("argv") == [str(FAKE_BINARY), "auth", "status"]
        assert inv.get("env") == {"MULTICA_FAKE_RECORD": str(record)}


def test_argv_contract_does_not_interpolate_shell(tmp_path: pathlib.Path) -> None:
    with _record_file(tmp_path, "argv_record2.jsonl") as record:
        _run_argv(["auth", "login", "; rm -rf /tmp/x"], record)
        inv = cast("dict[str, object]", json.loads(record.read_text().strip()))
        argv = cast("list[str]", inv.get("argv"))
        assert argv[-1] == "; rm -rf /tmp/x"


def test_argv_record_uses_sequence_not_str(tmp_path: pathlib.Path) -> None:
    argv_seq: list[str] = ["issue", "list", "--status", "open"]
    assert isinstance(argv_seq, list)
    with _record_file(tmp_path, "argv_record3.jsonl") as record:
        subprocess.run(
            [sys.executable, str(FAKE_BINARY), *argv_seq],
            check=False,
            env={"MULTICA_FAKE_RECORD": str(record)},
        )
        inv = cast("dict[str, object]", json.loads(record.read_text().strip()))
        argv = cast("list[str]", inv.get("argv"))
        assert argv[-2:] == ["--status", "open"]


def test_argv_record_rejects_path_outside_fixture_dir() -> None:
    with pytest.raises(ValueError, match="MULTICA_FAKE_RECORD must stay under"):
        _validate_record_path("/tmp/outside.jsonl")
