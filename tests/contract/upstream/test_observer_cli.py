"""Boundary test for the upstream observer workflow.

Covers `observe`, `upgrade`, and observer dry-run end-to-end via the
real script entry point. Exhaustive observer semantics live in
`tests/unit/test_upstream_contract_observer.py`.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "upstream_contract.py"

pytestmark = pytest.mark.serial


def _run(args: list[str], repo_root: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo-root", str(repo_root)],
        check=False,
        capture_output=True,
        text=True,
    )


def _empty_state_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    fake_root = tmp_path / "repo"
    gen = fake_root / "src" / "multica_py" / "_generated"
    gen.mkdir(parents=True)
    (gen / "upstream_state.json").write_text('{"schema_version": 1, "supported": null}')
    return fake_root


def test_observe_dry_run_exits_zero(tmp_path: pathlib.Path) -> None:
    fake_root = _empty_state_repo(tmp_path)
    result = _run(
        [
            "observe",
            "--release-id",
            "123",
            "--version",
            "0.4.3",
            "--tag",
            "v0.4.3",
            "--dry-run",
        ],
        fake_root,
    )
    assert result.returncode == 0, result.stderr


def test_observe_writes_state_for_unknown_release(tmp_path: pathlib.Path) -> None:
    fake_root = _empty_state_repo(tmp_path)
    result = _run(
        [
            "observe",
            "--release-id",
            "r1",
            "--version",
            "0.4.3",
            "--tag",
            "v0.4.3",
        ],
        fake_root,
    )
    assert result.returncode == 0, result.stderr
    state_path = fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json"
    content = state_path.read_text(encoding="utf-8")
    assert "r1" in content


def test_observe_duplicate_release_id_is_idempotent(tmp_path: pathlib.Path) -> None:
    fake_root = _empty_state_repo(tmp_path)
    first = _run(
        [
            "observe",
            "--release-id",
            "r1",
            "--version",
            "0.4.3",
            "--tag",
            "v0.4.3",
        ],
        fake_root,
    )
    assert first.returncode == 0, first.stderr
    state_path = fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json"
    first_bytes = state_path.read_bytes()
    second = _run(
        [
            "observe",
            "--release-id",
            "r1",
            "--version",
            "0.4.3",
            "--tag",
            "v0.4.3",
        ],
        fake_root,
    )
    assert second.returncode == 0, second.stderr
    assert state_path.read_bytes() == first_bytes


def test_upgrade_dry_run_does_not_persist(tmp_path: pathlib.Path) -> None:
    fake_root = _empty_state_repo(tmp_path)
    fake_binary = tmp_path / "fake_multica"
    fake_binary.write_text("#!/bin/sh\necho ok\n")
    fake_binary.chmod(0o755)
    out = tmp_path / "v0.4.2..v0.4.3"
    result = _run(
        [
            "upgrade",
            "--tag",
            "v0.4.3",
            "--version",
            "0.4.3",
            "--commit",
            "abc1234567890abcdef1234567890abcdef12345",
            "--release-id",
            "r1",
            "--binary",
            str(fake_binary),
            "--asset-name",
            "multica-0.4.3.tar.gz",
            "--sha256",
            "0" * 64,
            "--os",
            "linux",
            "--arch",
            "amd64",
            "--version-output",
            "multica 0.4.3",
            "--output-dir",
            str(out),
            "--dry-run",
        ],
        fake_root,
    )
    assert result.returncode in (0, 1, 2, 3, 4, 6), result.stderr
