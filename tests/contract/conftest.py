from __future__ import annotations

import fcntl
import hashlib
import json
import pathlib
import subprocess
import sys
from collections.abc import Iterator
from typing import cast

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "upstream_contract.py"
STATE_REL = "src/multica_py/_generated/upstream_state.json"
CANDIDATE_CONTRACT_REL = "src/multica_py/_generated/upstream_candidate_contract.json"
GENERATED_LOCK_REL = "src/multica_py/_generated/.upstream_test.lock"


def json_object(raw: str) -> dict[str, object]:
    return cast("dict[str, object]", json.loads(raw))


def candidate_field(state: dict[str, object], field: str) -> object:
    candidate = state["candidate"]
    assert isinstance(candidate, dict)
    return candidate[field]


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@pytest.fixture
def fake_upstream_cli(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "fake_multica"
    p.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "__contract" ]; then\n'
        "  cat <<JSON\n"
        '{"commands":[{"path":["agent"],"use":"list","flags":[]}]}\n'
        "JSON\n"
        'elif [ "$1" = "--help" ]; then\n'
        "  echo Available Commands:\n"
        "  echo agent\n"
        "else\n"
        "  echo Usage\n"
        "fi\n"
    )
    p.chmod(0o755)
    return p


_BINARY_SUBCOMMANDS = frozenset({"collect", "upgrade"})


class ContractCliRunner:
    DEFAULT_VERSION = "0.4.3"
    DEFAULT_TAG = "v0.4.3"
    DEFAULT_COMMIT = "abc1234567890abcdef1234567890abcdef12345"
    DEFAULT_ASSET_NAME = "multica-0.4.3.tar.gz"
    DEFAULT_OS = "linux"
    DEFAULT_ARCH = "amd64"
    DEFAULT_VERSION_OUTPUT = "multica 0.4.3"

    def __init__(self, binary: pathlib.Path) -> None:
        self._binary = binary
        self._sha256 = sha256_of(binary)

    def binary_args(self) -> list[str]:
        return [
            "--binary",
            str(self._binary),
            "--version",
            self.DEFAULT_VERSION,
            "--tag",
            self.DEFAULT_TAG,
            "--commit",
            self.DEFAULT_COMMIT,
            "--asset-name",
            self.DEFAULT_ASSET_NAME,
            "--sha256",
            self._sha256,
            "--os",
            self.DEFAULT_OS,
            "--arch",
            self.DEFAULT_ARCH,
            "--version-output",
            self.DEFAULT_VERSION_OUTPUT,
        ]

    def run(
        self,
        subcommand: str,
        *extra: str,
        output: pathlib.Path | None = None,
        repo_root: pathlib.Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        argv: list[str] = [
            sys.executable,
            str(SCRIPT),
            subcommand,
            *(self.binary_args() if subcommand in _BINARY_SUBCOMMANDS else ()),
            *extra,
            "--repo-root",
            str(repo_root or ROOT),
        ]
        if output is not None:
            argv.extend(["--output", str(output)])
        return subprocess.run(argv, check=False, capture_output=True, text=True)


@pytest.fixture
def contract_cli(fake_upstream_cli: pathlib.Path) -> ContractCliRunner:
    return ContractCliRunner(fake_upstream_cli)


@pytest.fixture
def preserved_generated_state() -> Iterator[None]:
    lock_path = ROOT / GENERATED_LOCK_REL
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    state_path = ROOT / STATE_REL
    generated = ROOT / CANDIDATE_CONTRACT_REL
    with lock_path.open("w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        original_state = state_path.read_text(encoding="utf-8")
        generated_existed = generated.is_file()
        generated_bytes = generated.read_bytes() if generated_existed else b""
        try:
            yield
        finally:
            state_path.write_text(original_state, encoding="utf-8")
            if generated_existed:
                generated.write_bytes(generated_bytes)
            elif generated.exists():
                generated.unlink()
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
