#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TypedDict, cast

_FIXTURE_ROOT = Path(__file__).resolve().parent
_RECORD_ENV_ALLOWLIST = frozenset({"MULTICA_FAKE_RECORD"})
_RECORD_DIR = _FIXTURE_ROOT / "_tmp"
_FIXTURE_DIR = (_FIXTURE_ROOT / "json").resolve()


class FixtureRecord(TypedDict):
    stdout: str | dict[str, object] | list[object]
    stderr: str | dict[str, object] | list[object]
    exit_code: int


class RecordedInvocation(TypedDict):
    argv: list[str]
    cwd: str
    env: dict[str, str]


class VersionPayload(TypedDict):
    version: str
    commit: str
    buildDate: str
    goVersion: str
    os: str
    arch: str


class AuthStatusPayload(TypedDict):
    authenticated: bool
    user_id: str | None
    token_type: str | None


_FIXTURE_PREFIXES: dict[str, str] = {
    "workspace": "workspaces",
    "project": "projects",
    "issue": "issues",
    "auth": "auth",
    "daemon": "daemon",
    "label": "labels",
    "agent": "agents",
    "skill": "skills",
    "autopilot": "autopilots",
    "repo": "repositories",
    "runtime": "runtimes",
    "attachment": "attachments",
    "config": "configuration",
    "squad": "squads",
    "user": "users",
}


def _record_env() -> dict[str, str]:
    return {key: os.environ[key] for key in _RECORD_ENV_ALLOWLIST if key in os.environ}


def _validate_record_path(record_path: str) -> Path:
    resolved = Path(record_path).resolve()
    record_root = _RECORD_DIR.resolve()
    if resolved.is_relative_to(record_root):
        return resolved
    raise ValueError(f"MULTICA_FAKE_RECORD must stay under {record_root}")


def _find_fixture(argv: list[str]) -> FixtureRecord | None:
    cmd = argv[1] if len(argv) > 1 else ""
    subdir = _FIXTURE_PREFIXES.get(cmd, cmd)
    positional: list[str] = []
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                i += 2
                continue
            i += 1
            continue
        positional.append(arg)
        i += 1
    key = "_".join(positional)
    fixture_dir = (_FIXTURE_DIR / subdir).resolve()
    if not fixture_dir.is_relative_to(_FIXTURE_DIR) or not fixture_dir.exists():
        return None
    for f in fixture_dir.iterdir():
        fixture_file = f.resolve()
        if not fixture_file.is_relative_to(_FIXTURE_DIR):
            continue
        if key == f.stem and f.suffix == ".json":
            with open(fixture_file, encoding="utf-8") as fh:
                return cast("FixtureRecord", json.load(fh))
    return None


def main() -> int:
    record_path = os.environ.get("MULTICA_FAKE_RECORD")
    if record_path:
        record_file = _validate_record_path(record_path)
        record: RecordedInvocation = {
            "argv": list(sys.argv),
            "cwd": os.getcwd(),
            "env": _record_env(),
        }
        with open(record_file, "a", encoding="utf-8") as f:
            json.dump(record, f)
            f.write("\n")

    fixture = _find_fixture(sys.argv)
    if fixture is not None:
        output = fixture.get("stdout", "")
        if isinstance(output, str):
            sys.stdout.write(output)
        else:
            json.dump(output, sys.stdout)
        stderr = fixture.get("stderr", "")
        if stderr:
            sys.stderr.write(stderr if isinstance(stderr, str) else json.dumps(stderr))
    else:
        if "--help" in sys.argv:
            sys.stdout.write("Fake multica CLI\nUsage: multica <command>\n")
        elif sys.argv[1:2] == ["version"]:
            version_payload: VersionPayload = {
                "version": "0.1.0",
                "commit": "abc1234",
                "buildDate": "2026-01-01",
                "goVersion": "go1.22",
                "os": "linux",
                "arch": "amd64",
            }
            sys.stdout.write(json.dumps(version_payload))
        elif sys.argv[1:2] == ["auth"] and sys.argv[2:3] == ["status"]:
            auth_status: AuthStatusPayload = {
                "authenticated": False,
                "user_id": None,
                "token_type": None,
            }
            json.dump(auth_status, sys.stdout)
        else:
            print(f"Unknown command: {' '.join(sys.argv[1:])}", file=sys.stderr)
            return 1

    if fixture is None:
        return 0
    ec = fixture.get("exit_code", 0)
    return ec if isinstance(ec, int) else 0


if __name__ == "__main__":
    sys.exit(main())
