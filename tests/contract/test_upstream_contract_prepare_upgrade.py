from __future__ import annotations

import json
import pathlib
import shutil
from typing import cast

from multica_py._internal.upstream_contract.paths import COVERAGE_PATH, SUPPORTED_CONTRACT_PATH

from .conftest import ContractCliRunner

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"


def _read_tree(root: pathlib.Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = path.read_bytes()
    return out


def test_prepare_upgrade_writes_mandatory_layout(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
) -> None:
    out = tmp_path / "v0.4.2..v0.4.3"
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json").write_text(
        '{"schema_version": 1, "decisions": []}'
    )
    result = contract_cli.run(
        "prepare-upgrade",
        "--candidate",
        str(FIXTURES / "candidate-cli-contract-v2.json"),
        "--output-dir",
        str(out),
        "--supported",
        str(SUPPORTED_CONTRACT_PATH),
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


def test_prepare_upgrade_is_idempotent(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
) -> None:
    out = tmp_path / "v0.4.2..v0.4.3"
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json").write_text(
        '{"schema_version": 1, "decisions": []}'
    )
    args = (
        "prepare-upgrade",
        "--candidate",
        str(FIXTURES / "candidate-cli-contract-v2.json"),
        "--output-dir",
        str(out),
        "--supported",
        str(SUPPORTED_CONTRACT_PATH),
    )
    first = contract_cli.run(*args, repo_root=fake_root)
    assert first.returncode in (0, 2, 6)
    snapshot_a = _read_tree(out)
    second = contract_cli.run(*args, repo_root=fake_root)
    assert second.returncode in (0, 2, 6)
    snapshot_b = _read_tree(out)
    assert snapshot_a == snapshot_b


def test_local_upgrade_directory_layout_matches_oracle(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
) -> None:
    out = tmp_path / "v0.4.2..v0.4.3"
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json").write_text(
        '{"schema_version": 1, "decisions": []}'
    )
    contract_cli.run(
        "prepare-upgrade",
        "--candidate",
        str(FIXTURES / "candidate-cli-contract-v2.json"),
        "--output-dir",
        str(out),
        "--supported",
        str(SUPPORTED_CONTRACT_PATH),
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


def test_apply_manifest_suggestions_keeps_rows_incomplete(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
) -> None:
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
    contract_cli.run(
        "prepare-upgrade",
        "--candidate",
        str(FIXTURES / "candidate-cli-contract-v2.json"),
        "--output-dir",
        str(out),
        "--supported",
        str(SUPPORTED_CONTRACT_PATH),
        repo_root=fake_root,
    )
    result = contract_cli.run(
        "apply-manifest-suggestions",
        "--bundle",
        str(out),
        repo_root=fake_root,
    )
    assert result.returncode in (0, 2, 6)
    coverage = cast(
        "dict[str, object]",
        json.loads(
            (fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json").read_text()
        ),
    )
    decisions = coverage.get("decisions")
    assert isinstance(decisions, list)
    incomplete = [
        item
        for item in decisions
        if isinstance(item, dict) and str(item.get("coverage_level")) == "incomplete"
    ]
    assert incomplete
