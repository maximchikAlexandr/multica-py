from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from collections.abc import Sequence
from typing import cast

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
FAKE_BINARY = ROOT / "tests" / "fixtures" / "fake_multica.py"


def _run_argv(
    argv: Sequence[str], env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    e = {"PATH": "/usr/bin:/bin"}
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, str(FAKE_BINARY), *argv],
        check=False,
        capture_output=True,
        text=True,
        env=e,
    )


def test_argv_contract_simple_invocation() -> None:
    record = ROOT / "tmp_argv_record.jsonl"
    record.unlink(missing_ok=True)
    result = _run_argv(["auth", "status"], env={"MULTICA_FAKE_RECORD": str(record)})
    assert result.returncode == 0
    lines = record.read_text().strip().splitlines()
    assert lines, "expected at least one invocation"
    inv = cast("dict[str, object]", json.loads(lines[0]))
    assert inv.get("argv") == [str(FAKE_BINARY), "auth", "status"]
    record.unlink()


def test_argv_contract_does_not_interpolate_shell() -> None:
    record = ROOT / "tmp_argv_record2.jsonl"
    record.unlink(missing_ok=True)
    _run_argv(
        ["auth", "login", "; rm -rf /tmp/x"],
        env={"MULTICA_FAKE_RECORD": str(record)},
    )
    inv = cast("dict[str, object]", json.loads(record.read_text().strip()))
    argv = cast("list[str]", inv.get("argv"))
    assert argv[-1] == "; rm -rf /tmp/x"
    record.unlink()


def test_argv_record_uses_sequence_not_str() -> None:
    record = ROOT / "tmp_argv_record3.jsonl"
    record.unlink(missing_ok=True)
    argv_seq: list[str] = ["issue", "list", "--status", "open"]
    assert isinstance(argv_seq, list)
    subprocess.run(
        [sys.executable, str(FAKE_BINARY), *argv_seq],
        check=False,
        env={"MULTICA_FAKE_RECORD": str(record)},
    )
    inv = cast("dict[str, object]", json.loads(record.read_text().strip()))
    argv = cast("list[str]", inv.get("argv"))
    assert argv[-2:] == ["--status", "open"]
    record.unlink()
