"""Protocol tests for the :mod:`tests.fixtures.fake_multica` subprocess.

Each test invokes the real ``__main__.py`` entry point in a subprocess and
asserts on its stdout, stderr, exit code, and the JSONL record it appends.
These tests pin the contract that the SDK transport relies on; changing the
executable's behaviour without updating these tests will break the component
round-trip.
"""

from __future__ import annotations

import base64
import datetime
import json
import os
import pathlib
import subprocess
import sys

import pytest

from multica_py._internal.processes import run_with_timeout
from tests.fixtures.fake_multica import (
    EXIT_USAGE,
    FAKE_MULTICA_STDERR_PREFIX,
    RECORD_DIR_NAME,
    RECORD_ENV_ALLOWLIST,
    RESPONSE_V1_SCHEMA_PATH,
    FakeMultica,
)

pytestmark = [pytest.mark.component, pytest.mark.process]

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_FIXTURES_DIR = _REPO_ROOT / "tests" / "fixtures"
_FAKE_CLI_MAIN = _FIXTURES_DIR / "fake_multica" / "__main__.py"
_RECORD_ROOT = _FIXTURES_DIR / RECORD_DIR_NAME

_BASIC_PAYLOAD: dict[str, object] = {
    "schema": 1,
    "stdout_b64": base64.b64encode(b"hello\n").decode("ascii"),
    "stderr_b64": base64.b64encode(b"").decode("ascii"),
    "exit_code": 0,
    "record": {
        "argv": [str(_FAKE_CLI_MAIN), "noop"],
        "cwd": str(_REPO_ROOT),
        "env": {},
        "timestamp": "2024-01-01T00:00:00Z",
    },
}


def _write_response(
    responses_dir: pathlib.Path, name: str, payload: dict[str, object]
) -> pathlib.Path:
    path = responses_dir / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _invoke(
    *args: str,
    cwd: pathlib.Path | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    argv: tuple[str, ...] = (sys.executable, str(_FAKE_CLI_MAIN), *args)
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return run_with_timeout(argv, cwd=str(cwd) if cwd else None, env=env)


def test_response_schema(tmp_path: pathlib.Path) -> None:
    """A successful invocation returns a payload that conforms to response_v1.json."""
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    name = "schema_probe"
    _write_response(responses_dir, name, _BASIC_PAYLOAD)

    fake = FakeMultica(responses_dir=responses_dir)
    response = fake.load_response(name)

    schema = json.loads(RESPONSE_V1_SCHEMA_PATH.read_text(encoding="utf-8"))
    required_top = set(schema["required"])
    response_dict = response.to_dict()
    assert required_top.issubset(response_dict.keys()), (
        f"missing top-level keys: {required_top - set(response_dict.keys())}"
    )
    record_required = set(schema["properties"]["record"]["required"])
    record_dict_raw = response_dict["record"]
    assert isinstance(record_dict_raw, dict)
    assert record_required.issubset(record_dict_raw.keys())
    argv_raw = record_dict_raw["argv"]
    assert isinstance(argv_raw, list)
    assert len(argv_raw) >= 1
    env_raw = record_dict_raw["env"]
    assert isinstance(env_raw, dict)


def test_stderr_capture(tmp_path: pathlib.Path) -> None:
    """stderr from the response is written to the child's stderr pipe."""
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    name = "with_stderr"
    payload = dict(_BASIC_PAYLOAD)
    payload["stderr_b64"] = base64.b64encode(b"warn-line\n").decode("ascii")
    _write_response(responses_dir, name, payload)

    result = _invoke(name, env_extra={"MULTICA_FAKE_RESPONSES": str(responses_dir)})
    assert result.returncode == 0
    assert result.stdout == b"hello\n"
    assert result.stderr == b"warn-line\n"


def test_exit_code_propagation(tmp_path: pathlib.Path) -> None:
    """The response's exit_code is the subprocess returncode."""
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    name = "nonzero"
    payload = dict(_BASIC_PAYLOAD)
    payload["exit_code"] = 7
    payload["stdout_b64"] = base64.b64encode(b"").decode("ascii")
    _write_response(responses_dir, name, payload)

    result = _invoke(name, env_extra={"MULTICA_FAKE_RESPONSES": str(responses_dir)})
    assert result.returncode == 7


def test_record_written(tmp_path: pathlib.Path) -> None:
    """With MULTICA_FAKE_RECORD, the child appends a JSONL record."""
    record_dir = _RECORD_ROOT / "test_record_written"
    record_dir.mkdir(parents=True, exist_ok=True)
    record_file = record_dir / "record.jsonl"
    argv: tuple[str, ...] = (sys.executable, str(_FAKE_CLI_MAIN), "version")
    run_with_timeout(argv, env={**os.environ, "MULTICA_FAKE_RECORD": str(record_file)})

    assert record_file.is_file()
    record = json.loads(record_file.read_text(encoding="utf-8").splitlines()[-1])
    assert "argv" in record
    assert "cwd" in record
    assert "env" in record
    assert "timestamp" in record
    ts = record["timestamp"]
    assert isinstance(ts, str)
    datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def test_invalid_path_returns_exit_64(tmp_path: pathlib.Path) -> None:
    """A MULTICA_FAKE_RECORD path outside the record root returns 64."""
    bogus = tmp_path / "outside" / "record.jsonl"
    argv: tuple[str, ...] = (sys.executable, str(_FAKE_CLI_MAIN), "version")
    result = run_with_timeout(argv, env={**os.environ, "MULTICA_FAKE_RECORD": str(bogus)})
    assert result.returncode == EXIT_USAGE


def test_invalid_base64_returns_exit_64(tmp_path: pathlib.Path) -> None:
    """A response with invalid base64 in stdout returns 64."""
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    name = "bad_b64"
    payload = dict(_BASIC_PAYLOAD)
    payload["stdout_b64"] = "@@@not-base64@@@"
    _write_response(responses_dir, name, payload)

    result = _invoke(name, env_extra={"MULTICA_FAKE_RESPONSES": str(responses_dir)})
    assert result.returncode == EXIT_USAGE


def test_env_allowlist(tmp_path: pathlib.Path) -> None:
    """The record's env contains only the allowlisted variables."""
    record_dir = _RECORD_ROOT / "test_env_allowlist"
    record_dir.mkdir(parents=True, exist_ok=True)
    record_file = record_dir / "record.jsonl"
    argv: tuple[str, ...] = (sys.executable, str(_FAKE_CLI_MAIN), "version")
    env = {
        **os.environ,
        "MULTICA_FAKE_RECORD": str(record_file),
        "MULTICA_API_KEY": "secret-key",
        "RANDOM_GARBAGE_VAR": "should-be-dropped",
    }
    run_with_timeout(argv, env=env)

    record = json.loads(record_file.read_text(encoding="utf-8").splitlines()[-1])
    captured_env = record["env"]
    assert set(captured_env) <= set(RECORD_ENV_ALLOWLIST)
    if "MULTICA_API_KEY" in captured_env:
        assert captured_env["MULTICA_API_KEY"] == "***"


def test_absolute_paths_only(tmp_path: pathlib.Path) -> None:
    """All paths in the record are absolute."""
    record_dir = _RECORD_ROOT / "test_absolute_paths"
    record_dir.mkdir(parents=True, exist_ok=True)
    record_file = record_dir / "record.jsonl"
    argv: tuple[str, ...] = (sys.executable, str(_FAKE_CLI_MAIN), "version")
    run_with_timeout(
        argv, cwd=str(tmp_path), env={**os.environ, "MULTICA_FAKE_RECORD": str(record_file)}
    )

    record = json.loads(record_file.read_text(encoding="utf-8").splitlines()[-1])
    assert pathlib.Path(record["argv"][0]).is_absolute(), (
        f"non-absolute argv[0]: {record['argv'][0]!r}"
    )
    assert pathlib.Path(record["cwd"]).is_absolute()


def test_no_response_returns_exit_64(tmp_path: pathlib.Path) -> None:
    """Invoking an unknown operation_id with no stub match returns 64."""
    isolated = tmp_path / "isolated"
    isolated.mkdir()

    argv: tuple[str, ...] = (sys.executable, str(_FAKE_CLI_MAIN), "definitely_not_a_command")
    result = run_with_timeout(argv, cwd=str(isolated), env=os.environ.copy())
    assert result.returncode == EXIT_USAGE
    assert FAKE_MULTICA_STDERR_PREFIX.encode("ascii") in result.stderr
