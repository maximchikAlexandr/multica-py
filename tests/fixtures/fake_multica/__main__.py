#!/usr/bin/env python3
"""Executable entry point for the fake multica CLI.

Invoke as ``python -m fake_multica <subcommand> [...]`` (the file also runs
standalone and prepends the fixtures dir to ``sys.path``).

Env vars:
  - MULTICA_FAKE_RECORD: JSONL file under tests/fixtures/_tmp/; exit 64 if invalid.
  - MULTICA_FAKE_ENV_KEYS: comma-separated extra env keys to record.
  - MULTICA_FAKE_RESPONSES: override the responses dir.

Stubs (`version`, `auth status`, `--help`) are emitted when no fixture matches;
unknown commands write ``fake-multica: Unknown command: ...`` to stderr and
exit 64.
"""

from __future__ import annotations

import base64
import binascii
import datetime
import json
import os
import pathlib
import sys
from typing import IO, cast

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from tests.fixtures.fake_multica import (
    EXIT_USAGE,
    FAKE_MULTICA_STDERR_PREFIX,
    _env_allowlisted,
    _validate_record_path,
)


def _abs_argv(argv: tuple[str, ...]) -> tuple[str, ...]:
    if not argv:
        return argv
    return (str(pathlib.Path(os.fspath(argv[0])).resolve()),) + tuple(argv[1:])


def _parse_extra_env_keys(raw: str | None) -> frozenset[str]:
    if not raw:
        return frozenset()
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


_SECRET_KEY_MARKERS = ("SECRET", "PASSWORD", "TOKEN", "KEY")


def _is_secret_key(key: str) -> bool:
    upper = key.upper()
    return any(marker in upper for marker in _SECRET_KEY_MARKERS)


def _record_invocation(record_path: pathlib.Path, extra_env_keys: frozenset[str]) -> bool:
    """Append the current invocation to the JSONL record file.

    Returns True on success, False if the path exists but cannot be appended
    to (corrupt, unwritable). The caller converts that into ``EXIT_USAGE``.
    """
    try:
        argv_tuple: tuple[str, ...] = tuple(sys.argv)
        env = _env_allowlisted(os.environ)
        for key in extra_env_keys:
            if key in os.environ and key not in env:
                env[key] = "***" if _is_secret_key(key) else os.environ[key]
        record: dict[str, object] = {
            "argv": list(_abs_argv(argv_tuple)),
            "cwd": str(pathlib.Path(os.getcwd()).resolve()),
            "env": env,
            "timestamp": datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with open(record_path, "a", encoding="utf-8") as fh:
            json.dump(record, fh)
            fh.write("\n")
    except OSError:
        return False
    return True


def _load_response(name: str) -> tuple[bytes, bytes, int] | None:
    package_dir = pathlib.Path(__file__).resolve().parent
    responses_dir_env = os.environ.get("MULTICA_FAKE_RESPONSES")
    if responses_dir_env:
        responses_dir = pathlib.Path(responses_dir_env).resolve()
    else:
        responses_dir = (package_dir / "responses").resolve()
    candidate = (responses_dir / f"{name}.json").resolve()
    if not candidate.is_relative_to(responses_dir) or not candidate.is_file():
        return None
    loaded: object = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("response payload must be a JSON object")
    payload = cast("dict[str, object]", loaded)
    return (
        base64.b64decode(str(payload["stdout_b64"]), validate=True),
        base64.b64decode(str(payload["stderr_b64"]), validate=True),
        int(str(payload["exit_code"])),
    )


def _emit_stub(argv: tuple[str, ...]) -> int:
    if "--help" in argv:
        sys.stdout.write("Fake multica CLI\nUsage: multica <command>\n")
        return 0
    if len(argv) >= 2 and argv[1] == "version":
        version: dict[str, object] = {
            "version": "0.1.0",
            "commit": "abc1234",
            "buildDate": "2026-01-01",
            "goVersion": "go1.22",
            "os": "linux",
            "arch": "amd64",
        }
        sys.stdout.write(json.dumps(version))
        return 0
    if len(argv) >= 3 and argv[1] == "auth" and argv[2] == "status":
        auth_status: dict[str, object] = {
            "authenticated": False,
            "user_id": None,
            "token_type": None,
        }
        sys.stdout.write(json.dumps(auth_status))
        return 0
    sys.stderr.write(f"{FAKE_MULTICA_STDERR_PREFIX} Unknown command: {' '.join(argv[1:])}\n")
    return EXIT_USAGE


def main(argv: tuple[str, ...] | None = None) -> int:
    argv = tuple(argv if argv is not None else sys.argv)
    extra_env_keys = _parse_extra_env_keys(os.environ.get("MULTICA_FAKE_ENV_KEYS"))
    record_env = os.environ.get("MULTICA_FAKE_RECORD")
    if record_env:
        try:
            record_path = _validate_record_path(record_env)
        except ValueError:
            return EXIT_USAGE
        if not _record_invocation(record_path, extra_env_keys):
            return EXIT_USAGE

    name = argv[1] if len(argv) > 1 else ""
    fixture: tuple[bytes, bytes, int] | None
    if not name:
        fixture = None
    else:
        try:
            fixture = _load_response(name)
        except (binascii.Error, ValueError):
            return EXIT_USAGE
    if fixture is None:
        return _emit_stub(argv)

    stdout_b, stderr_b, exit_code = fixture
    if stdout_b:
        cast("IO[bytes]", sys.stdout.buffer).write(stdout_b)
    if stderr_b:
        cast("IO[bytes]", sys.stderr.buffer).write(stderr_b)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
