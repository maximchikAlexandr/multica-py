"""Programmable fake multica CLI.

Exposes :class:`FakeMultica` for tests that want to drive the fake CLI from
Python without touching the filesystem, plus the small set of helpers that the
contract tests still import (``_validate_record_path``).

Response/record fixtures live under :mod:`tests.fixtures.fake_multica.responses`
and conform to :data:`RESPONSE_V1_SCHEMA_PATH`. Schema keeps stdout/stderr as
base64-encoded UTF-8 bytes, mandates absolute paths in the record, and pins
the env allowlist to ``MULTICA_API_KEY``.

The matching executable lives at :mod:`tests.fixtures.fake_multica.__main__``.
"""

from __future__ import annotations

import base64
import datetime
import os
import pathlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

_PACKAGE_DIR = pathlib.Path(__file__).resolve().parent
SCHEMAS_DIR = _PACKAGE_DIR / "schemas"
RESPONSES_DIR = _PACKAGE_DIR / "responses"
RESPONSE_V1_SCHEMA_PATH = SCHEMAS_DIR / "response_v1.json"
RESPONSE_V1_SCHEMA = 1
# ponytail: MULTICA_FAKE_RECORD is intentionally NOT in the allowlist — including
# it would leak the recording path back into the captured record (spec §H6).
RECORD_ENV_ALLOWLIST: frozenset[str] = frozenset({"MULTICA_API_KEY"})
RECORD_DIR_NAME = "_tmp"
REDACTED = "***"
EXIT_USAGE = 64
FAKE_MULTICA_STDERR_PREFIX = "fake-multica:"

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


def _now_iso() -> str:
    return datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _abs(path: str | os.PathLike[str]) -> str:
    return str(pathlib.Path(os.fspath(path)).resolve())


def _env_allowlisted(env: Mapping[str, str]) -> dict[str, str]:
    captured = {k: v for k, v in env.items() if k in RECORD_ENV_ALLOWLIST}
    if captured.get("MULTICA_API_KEY"):
        captured["MULTICA_API_KEY"] = REDACTED
    return captured


def _validate_record_path(record_path: str | os.PathLike[str]) -> pathlib.Path:
    resolved = pathlib.Path(os.fspath(record_path)).resolve()
    record_root = (_PACKAGE_DIR.parent / RECORD_DIR_NAME).resolve()
    if not resolved.is_relative_to(record_root):
        raise ValueError(f"MULTICA_FAKE_RECORD must stay under {record_root}")
    return resolved


@dataclass(frozen=True)
class FakeCliRecord:
    argv: tuple[str, ...]
    cwd: str
    env: dict[str, str]
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "cwd": self.cwd,
            "env": dict(self.env),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class FakeCliResponse:
    """One fake-CLI response: base64-encoded stdout/stderr + exit code + record."""

    stdout_b64: str
    stderr_b64: str
    exit_code: int
    record: FakeCliRecord

    def decode_stdout(self) -> bytes:
        return base64.b64decode(self.stdout_b64.encode("ascii"), validate=True)

    def decode_stderr(self) -> bytes:
        return base64.b64decode(self.stderr_b64.encode("ascii"), validate=True)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": RESPONSE_V1_SCHEMA,
            "stdout_b64": self.stdout_b64,
            "stderr_b64": self.stderr_b64,
            "exit_code": self.exit_code,
            "record": self.record.to_dict(),
        }


class FakeMultica:
    """Programmable fake multica CLI.

    Tests can construct :class:`FakeMultica` and either invoke it as a
    subprocess replacement via :meth:`run_argv`, or load a JSON fixture from
    :data:`RESPONSES_DIR` via :meth:`load_response`.
    """

    def __init__(
        self,
        *,
        responses_dir: pathlib.Path = RESPONSES_DIR,
        env_allowlist: frozenset[str] = RECORD_ENV_ALLOWLIST,
        record_root: pathlib.Path | None = None,
    ) -> None:
        self.responses_dir = responses_dir
        self.env_allowlist = env_allowlist
        self.record_root = record_root or (_PACKAGE_DIR.parent / RECORD_DIR_NAME)

    def build_record(
        self,
        argv: tuple[str, ...],
        *,
        cwd: str | os.PathLike[str] | None = None,
        env: Mapping[str, str] | None = None,
        timestamp: str | None = None,
    ) -> FakeCliRecord:
        abs_argv: tuple[str, ...] = (_abs(argv[0]),) + tuple(argv[1:]) if argv else ()
        if not all(p for p in abs_argv):
            raise ValueError("argv must be non-empty with absolute argv[0]")
        return FakeCliRecord(
            argv=abs_argv,
            cwd=_abs(cwd) if cwd is not None else _abs(os.getcwd()),
            env=_env_allowlisted(env if env is not None else os.environ),
            timestamp=timestamp or _now_iso(),
        )

    def build_response(
        self,
        *,
        stdout: bytes | str = b"",
        stderr: bytes | str = b"",
        exit_code: int = 0,
        argv: tuple[str, ...] = (),
        cwd: str | os.PathLike[str] | None = None,
        env: Mapping[str, str] | None = None,
    ) -> FakeCliResponse:
        if not 0 <= exit_code <= 255:
            raise ValueError(f"exit_code must fit in [0, 255], got {exit_code!r}")
        stdout_b = stdout.encode("utf-8") if isinstance(stdout, str) else stdout
        stderr_b = stderr.encode("utf-8") if isinstance(stderr, str) else stderr
        return FakeCliResponse(
            stdout_b64=base64.b64encode(stdout_b).decode("ascii"),
            stderr_b64=base64.b64encode(stderr_b).decode("ascii"),
            exit_code=exit_code,
            record=self.build_record(argv, cwd=cwd, env=env),
        )

    def load_response(self, name: str) -> FakeCliResponse:
        """Load a JSON fixture from :data:`responses_dir` and decode it.

        ``name`` may be a stem (``auth_status``) or a full filename
        (``auth_status.json``); both resolve to the same path.
        """
        file_name = name if name.endswith(".json") else f"{name}.json"
        path = (self.responses_dir / file_name).resolve()
        if not path.is_relative_to(self.responses_dir.resolve()):
            raise ValueError(f"response {name!r} must stay under {self.responses_dir}")
        if not path.is_file():
            raise FileNotFoundError(f"no fake-multica response at {path}")
        raw = path.read_bytes()
        return self._from_json(raw)

    def _from_json(self, raw: bytes) -> FakeCliResponse:
        import json

        loaded: object = json.loads(raw)
        if not isinstance(loaded, dict):
            raise ValueError("response payload must be a JSON object")
        payload = cast("dict[str, object]", loaded)
        for required in ("schema", "stdout_b64", "stderr_b64", "exit_code", "record"):
            if required not in payload:
                raise ValueError(f"response payload missing {required!r}")
        if payload["schema"] != RESPONSE_V1_SCHEMA:
            raise ValueError(
                f"response payload schema must be {RESPONSE_V1_SCHEMA}, got {payload['schema']!r}"
            )
        record_loaded = payload["record"]
        if not isinstance(record_loaded, dict):
            raise ValueError("record payload must be a JSON object")
        record_payload = cast("dict[str, object]", record_loaded)
        for required in ("argv", "cwd", "env", "timestamp"):
            if required not in record_payload:
                raise ValueError(f"record payload missing {required!r}")
        timestamp = record_payload["timestamp"]
        if not isinstance(timestamp, str) or not _TIMESTAMP_RE.match(timestamp):
            raise ValueError(f"invalid timestamp {timestamp!r}")
        record = FakeCliRecord(
            argv=tuple(cast("list[str]", record_payload["argv"])),
            cwd=str(record_payload["cwd"]),
            env=dict(cast("dict[str, str]", record_payload["env"])),
            timestamp=timestamp,
        )
        return FakeCliResponse(
            stdout_b64=str(payload["stdout_b64"]),
            stderr_b64=str(payload["stderr_b64"]),
            exit_code=int(str(payload["exit_code"])),
            record=record,
        )


__all__ = [
    "EXIT_USAGE",
    "FAKE_MULTICA_STDERR_PREFIX",
    "RECORD_DIR_NAME",
    "RECORD_ENV_ALLOWLIST",
    "RESPONSES_DIR",
    "RESPONSE_V1_SCHEMA",
    "RESPONSE_V1_SCHEMA_PATH",
    "SCHEMAS_DIR",
    "FakeCliRecord",
    "FakeCliResponse",
    "FakeMultica",
    "_validate_record_path",
]
