"""Opt-in smoke tests for real execution backends; never part of the offline suite."""

from __future__ import annotations

import datetime
import os
from collections.abc import Iterator

import pytest

from multica_py.execution import ExecutionRequest

pytestmark = [pytest.mark.live, pytest.mark.live_executor, pytest.mark.serial]


def _setting(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        pytest.skip(f"{name} is not configured for this opt-in executor smoke test")
    return value


def _request(
    *argv: str,
    cwd: str | None = None,
    environment: tuple[tuple[str, str], ...] = (),
) -> ExecutionRequest:
    return ExecutionRequest(
        argv=argv,
        cwd=cwd,
        environment=environment,
        timeout=datetime.timedelta(seconds=30),
    )


def _assert_run_stage_and_environment(executor: object) -> None:
    run = getattr(executor, "run")
    stage = getattr(executor, "stage")
    result = run(_request("sh", "-c", "printf out; printf err >&2"))
    assert (result.exit_code, result.stdout, result.stderr) == (0, b"out", b"err")

    environment = run(
        _request(
            "sh", "-c", 'printf %s "$MULTICA_PY_SMOKE"', environment=(("MULTICA_PY_SMOKE", "set"),)
        )
    )
    assert environment.stdout == b"set"
    cwd = run(_request("sh", "-c", "pwd", cwd="/tmp"))
    assert cwd.stdout.rstrip(b"\n") == b"/tmp"

    with stage("smoke.bin", b"exact\x00bytes") as target_path:
        staged = run(_request("sh", "-c", 'cat "$1"', "sh", target_path))
        assert staged.stdout == b"exact\x00bytes"
    absent = run(_request("sh", "-c", 'test ! -e "$1"', "sh", target_path))
    assert absent.exit_code == 0


def _assert_spawn_and_control(executor: object) -> None:
    spawn = getattr(executor, "spawn")
    streamed = spawn(_request("sh", "-c", "printf line; sleep 1; printf err >&2"))
    assert list(streamed.stdout_lines()) == ["line"]
    assert list(streamed.stderr_lines()) == ["err"]

    buffered = spawn(_request("sh", "-c", "printf buffered"))
    assert buffered.collect().stdout == b"buffered"

    controlled = spawn(_request("sh", "-c", "sleep 20"))
    controlled.terminate()
    controlled.kill()
    controlled.close()


@pytest.fixture
def ssh_executor() -> Iterator[object]:
    from multica_py.execution.ssh import SshExecutor

    with SshExecutor(
        host=_setting("MULTICA_LIVE_SSH_HOST"),
        username=_setting("MULTICA_LIVE_SSH_USERNAME"),
        password=os.environ.get("MULTICA_LIVE_SSH_PASSWORD") or None,
        key_filename=os.environ.get("MULTICA_LIVE_SSH_KEY_FILENAME") or None,
    ) as executor:
        yield executor


def test_ssh_executor_against_real_backend(ssh_executor: object) -> None:
    _assert_run_stage_and_environment(ssh_executor)
    _assert_spawn_and_control(ssh_executor)


@pytest.fixture
def microsandbox_executor() -> Iterator[object]:
    from multica_py.execution.microsandbox import MicrosandboxExecutor

    with MicrosandboxExecutor(_setting("MULTICA_LIVE_MICROSANDBOX")) as executor:
        yield executor


def test_microsandbox_executor_against_real_backend(microsandbox_executor: object) -> None:
    _assert_run_stage_and_environment(microsandbox_executor)
    _assert_spawn_and_control(microsandbox_executor)
