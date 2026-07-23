from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
from collections.abc import Callable, Mapping
from typing import cast

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "upstream_contract.py"
STATE_REL = "src/multica_py/_generated/upstream_state.json"
CANDIDATE_CONTRACT_REL = "src/multica_py/_generated/upstream_candidate_contract.json"


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


_GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@e",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@e",
    "PATH": "/usr/bin:/bin:/usr/local/bin",
    "HOME": "/tmp",
}


@pytest.fixture
def repo_factory(tmp_path: pathlib.Path) -> Callable[..., pathlib.Path]:
    """Factory: (initial_commits=0, files=None) -> Path of fresh git repo."""

    def _make(
        initial_commits: int = 0,
        files: Mapping[str, str] | None = None,
    ) -> pathlib.Path:
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True, env=_GIT_ENV)
        for name, content in (files or {}).items():
            (repo / name).write_text(content)
        (repo / "README.md").write_text("init")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=_GIT_ENV)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True, env=_GIT_ENV)
        for i in range(initial_commits):
            (repo / f"file_{i}.txt").write_text(f"v{i}")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=_GIT_ENV)
            subprocess.run(
                ["git", "commit", "-q", "-m", f"c{i}"], cwd=repo, check=True, env=_GIT_ENV
            )
        return repo

    return _make


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
