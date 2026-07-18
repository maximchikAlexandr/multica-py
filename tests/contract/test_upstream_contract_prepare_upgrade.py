from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src"

from multica_py._internal.upstream_contract.paths import COVERAGE_PATH, SUPPORTED_CONTRACT_PATH

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


def test_prepare_upgrade_writes_mandatory_layout(tmp_path: pathlib.Path) -> None:
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
        ],
        repo_root=fake_root,
    )
    assert result.returncode in (0, 2, 6), result.stderr
    expected = [
        "summary.md",
        "upstream-diff.json",
        "impact-map.json",
        "candidate-contract.json",
        "manifest-suggestions.json",
        "implementation-tasks.md",
        "changelog-fragment.md",
        "test-suggestions/argv-contracts.patch",
        "test-suggestions/output-fixtures.todo.json",
    ]
    for relative in expected:
        assert (out / relative).exists(), f"missing {relative}"


def test_prepare_upgrade_is_idempotent(tmp_path: pathlib.Path) -> None:
    out = tmp_path / "v0.4.2..v0.4.3"
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json").write_text(
        '{"schema_version": 1, "decisions": []}'
    )
    args = [
        "prepare-upgrade",
        "--candidate",
        str(FIXTURES / "candidate-cli-contract-v2.json"),
        "--output-dir",
        str(out),
        "--supported",
        str(SUPPORTED_CONTRACT_PATH),
    ]
    first = _run(args, repo_root=fake_root)
    assert first.returncode in (0, 2, 6)
    snapshot_a = _read_tree(out)
    second = _run(args, repo_root=fake_root)
    assert second.returncode in (0, 2, 6)
    snapshot_b = _read_tree(out)
    assert snapshot_a == snapshot_b


def _read_tree(root: pathlib.Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = path.read_bytes()
    return out


def test_local_upgrade_directory_layout_matches_oracle(tmp_path: pathlib.Path) -> None:
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
        ],
        repo_root=fake_root,
    )
    expected = [
        "summary.md",
        "upstream-diff.json",
        "impact-map.json",
        "candidate-contract.json",
        "manifest-suggestions.json",
        "implementation-tasks.md",
        "changelog-fragment.md",
        "test-suggestions/argv-contracts.patch",
        "test-suggestions/output-fixtures.todo.json",
    ]
    for relative in expected:
        assert (out / relative).is_file(), f"missing {relative}"


def test_apply_manifest_suggestions_keeps_rows_incomplete(tmp_path: pathlib.Path) -> None:
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    shutil.copy(
        COVERAGE_PATH,
        fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json",
    )
    out = tmp_path / "v0.4.2..v0.4.3"
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
    result = _run(
        [
            "apply-manifest-suggestions",
            "--bundle",
            str(out),
            "--repo-root",
            str(fake_root),
        ],
        repo_root=fake_root,
    )
    assert result.returncode in (0, 2, 6)
    coverage = json.loads(
        (fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json").read_text()
    )
    incomplete = [d for d in coverage["decisions"] if d["coverage_level"] == "incomplete"]
    assert incomplete
