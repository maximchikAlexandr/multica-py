from __future__ import annotations

import os
import pathlib
import subprocess
import sys

from multica_py._internal.upstream_contract.paths import SUPPORTED_CONTRACT_PATH

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src"
FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"


def _run(
    args: list[str], repo_root: pathlib.Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "multica_py._internal.upstream_contract.cli",
            *args,
            "--repo-root",
            str(repo_root or ROOT),
        ],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(SRC)},
    )


def test_apply_manifest_suggestions_is_idempotent(tmp_path: pathlib.Path) -> None:
    out = tmp_path / "v0.4.2..v0.4.3"
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json").write_text(
        '{"schema_version": 1, "decisions": []}'
    )
    _run(
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
    args = [
        "apply-manifest-suggestions",
        "--bundle",
        str(out),
        "--repo-root",
        str(fake_root),
    ]
    first = _run(args, repo_root=fake_root)
    assert first.returncode == 0
    manifest_path = fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json"
    first_bytes = manifest_path.read_bytes()
    second = _run(args, repo_root=fake_root)
    assert second.returncode == 0
    assert manifest_path.read_bytes() == first_bytes


def test_apply_manifest_suggestions_dry_run_does_not_write(tmp_path: pathlib.Path) -> None:
    out = tmp_path / "v0.4.2..v0.4.3"
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    coverage_path = fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json"
    coverage_path.write_text('{"schema_version": 1, "decisions": []}')
    _run(
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
    before = coverage_path.read_text()
    _run(
        [
            "apply-manifest-suggestions",
            "--bundle",
            str(out),
            "--dry-run",
            "--repo-root",
            str(fake_root),
        ],
        repo_root=fake_root,
    )
    after = coverage_path.read_text()
    assert before == after
