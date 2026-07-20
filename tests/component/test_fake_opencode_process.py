"""Component tests for the fake OpenCode executable subprocess contract."""

from __future__ import annotations

import os
import pathlib
import subprocess

import pytest

from tests.fixtures.fake_opencode_helpers import (
    InstructionPayload,
    canonical_argv,
    prepare_instruction_workspace,
)

pytestmark = [pytest.mark.component, pytest.mark.process]

_RUN_ID = "b" * 32


def test_subprocess_success_with_canonical_argv(tmp_path: pathlib.Path) -> None:
    """The executable accepts canonical argv, flushes stdout, and replaces target.txt."""
    payload = prepare_instruction_workspace(tmp_path, _RUN_ID)
    result = subprocess.run(
        canonical_argv(tmp_path, payload.prompt()),
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        '{"type":"step_start","sessionID":"multica-test","part":{}}',
        '{"type":"text","sessionID":"multica-test","part":{"text":"Applied MULTICA_TEST_ACTION"}}',
        '{"type":"step_finish","sessionID":"multica-test","part":{"reason":"stop","tokens":{"input":0,"output":0}}}',
    ]
    assert (tmp_path / "target.txt").read_text(encoding="utf-8") == f"after:{_RUN_ID}\n"
    assert (tmp_path / "control.txt").read_text(encoding="utf-8") == "control\n"


def test_subprocess_error_mode_exits_one_without_mutation(tmp_path: pathlib.Path) -> None:
    """Error mode emits one JSONL error and leaves workspace files unchanged."""
    payload = prepare_instruction_workspace(tmp_path, _RUN_ID)
    env = os.environ.copy()
    env["MULTICA_TEST_AGENT_MODE"] = "error"
    result = subprocess.run(
        canonical_argv(tmp_path, payload.prompt()),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        '{"type":"error","sessionID":"multica-test","error":{"name":"MulticaTestInstructionError","message":"agent mode error"}}',
    ]
    assert (tmp_path / "target.txt").read_text(encoding="utf-8") == f"before:{_RUN_ID}\n"


def test_subprocess_timeout_mode_is_terminable(tmp_path: pathlib.Path) -> None:
    """Timeout mode emits step_start, blocks until killed, and leaves files unchanged."""
    payload = prepare_instruction_workspace(tmp_path, _RUN_ID)
    env = os.environ.copy()
    env["MULTICA_TEST_AGENT_MODE"] = "timeout"
    process = subprocess.Popen(
        canonical_argv(tmp_path, payload.prompt()),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        stdout, stderr = process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate(timeout=2)
    assert process.returncode != 0
    assert stdout.splitlines() == [
        '{"type":"step_start","sessionID":"multica-test","part":{}}',
    ]
    assert stderr == ""
    assert (tmp_path / "target.txt").read_text(encoding="utf-8") == f"before:{_RUN_ID}\n"


def test_subprocess_wrong_edit_mode_writes_unexpected_content(tmp_path: pathlib.Path) -> None:
    """Wrong-edit mode writes unexpected content and still exits zero."""
    payload = prepare_instruction_workspace(tmp_path, _RUN_ID)
    env = os.environ.copy()
    env["MULTICA_TEST_AGENT_MODE"] = "wrong-edit"
    result = subprocess.run(
        canonical_argv(tmp_path, payload.prompt()),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert len(result.stdout.splitlines()) == 3
    assert (tmp_path / "target.txt").read_text(encoding="utf-8") == f"unexpected:{_RUN_ID}\n"


def test_subprocess_unknown_mode_exits_sixty_four(tmp_path: pathlib.Path) -> None:
    """Unknown agent modes exit 64 without touching workspace files."""
    payload = prepare_instruction_workspace(tmp_path, _RUN_ID)
    env = os.environ.copy()
    env["MULTICA_TEST_AGENT_MODE"] = "invalid-mode"
    result = subprocess.run(
        canonical_argv(tmp_path, payload.prompt()),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 64
    assert result.stdout == ""
    assert (tmp_path / "target.txt").read_text(encoding="utf-8") == f"before:{_RUN_ID}\n"
