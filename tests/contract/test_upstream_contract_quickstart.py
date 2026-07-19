from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
from typing import cast

from multica_py._internal.upstream_contract.paths import SUPPORTED_CONTRACT_PATH

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "upstream_contract.py"
FIXTURES = ROOT / "tests" / "fixtures" / "upstream_contract" / "golden"


def _run(
    args: list[str], repo_root: pathlib.Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo-root", str(repo_root or ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )


def _sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_quickstart_check(tmp_path: pathlib.Path) -> None:
    result = _run(["check", "--format", "human"])
    assert result.returncode in (0, 2, 3, 6)


def test_quickstart_collect(tmp_path: pathlib.Path) -> None:
    fake = tmp_path / "fake_multica"
    fake.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "__contract" ]; then\n'
        '  echo \'{"commands":[{"path":["a"],"use":"b","flags":[]}]}\'\n'
        'elif [ "$1" = "--help" ]; then\n'
        "  echo Available Commands:\n"
        "  echo a\n"
        "else\n"
        "  echo Usage\n"
        "fi\n"
    )
    fake.chmod(0o755)
    sha = _sha256_of(fake)
    out = tmp_path / "candidate.json"
    result = _run(
        [
            "collect",
            "--binary",
            str(fake),
            "--version",
            "0.4.3",
            "--tag",
            "v0.4.3",
            "--commit",
            "abc1234567890abcdef1234567890abcdef12345",
            "--asset-name",
            "x",
            "--sha256",
            sha,
            "--os",
            "linux",
            "--arch",
            "amd64",
            "--version-output",
            "multica 0.4.3",
            "--output",
            str(out),
        ]
    )
    assert result.returncode == 0
    payload = cast("dict[str, object]", json.loads(out.read_text()))
    assert payload["schema_version"] == 2


def test_quickstart_diff(tmp_path: pathlib.Path) -> None:
    result = _run(
        [
            "diff",
            "--from",
            str(SUPPORTED_CONTRACT_PATH),
            "--to",
            str(FIXTURES / "candidate-cli-contract-v2.json"),
            "--format",
            "human",
        ]
    )
    assert result.returncode in (2, 6)


def test_quickstart_prepare_upgrade(tmp_path: pathlib.Path) -> None:
    out = tmp_path / "v0.4.2..v0.4.3"
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json").write_text(
        '{"schema_version": 1, "decisions": []}'
    )
    result = _run(
        [
            "prepare-upgrade",
            "--candidate",
            str(FIXTURES / "candidate-cli-contract-v2.json"),
            "--output-dir",
            str(out),
            "--supported",
            str(SUPPORTED_CONTRACT_PATH),
            "--repo-root",
            str(fake_root),
        ],
        repo_root=fake_root,
    )
    assert result.returncode in (0, 2, 6)
    assert (out / "summary.md").exists()


def test_quickstart_observe_dry_run(tmp_path: pathlib.Path) -> None:
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
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
            "--repo-root",
            str(fake_root),
        ],
        repo_root=fake_root,
    )
    assert result.returncode == 0
