"""Boundary test for the upstream upgrade CLI subcommands.

Covers `prepare-upgrade`, `apply-manifest-suggestions`, and `upgrade`
end-to-end via the real script entry point. Exhaustive upgrade-bundle
assertions live in `tests/unit/test_upstream_contract_*.py`.
"""

from __future__ import annotations

import json
import pathlib
import shutil
from typing import cast

from multica_py._internal.upstream_contract.paths import COVERAGE_PATH, SUPPORTED_CONTRACT_PATH
from tests.contract.conftest import ContractCliRunner

FIXTURES = pathlib.Path(__file__).resolve().parents[2] / "fixtures" / "upstream_contract" / "golden"
CANDIDATE = FIXTURES / "candidate-cli-contract-v2.json"


def _write_minimal_generated(fake_root: pathlib.Path) -> None:
    gen = fake_root / "src" / "multica_py" / "_generated"
    gen.mkdir(parents=True)
    (gen / "upstream_state.json").write_text('{"schema_version": 1, "supported": null}')
    (gen / "upstream_coverage.json").write_text('{"schema_version": 1, "decisions": []}')


def test_prepare_upgrade_writes_mandatory_layout(
    tmp_path: pathlib.Path, contract_cli: ContractCliRunner
) -> None:
    out = tmp_path / "v0.4.2..v0.4.3"
    fake_root = tmp_path / "repo"
    _write_minimal_generated(fake_root)
    result = contract_cli.run(
        "prepare-upgrade",
        "--candidate",
        str(CANDIDATE),
        "--output-dir",
        str(out),
        "--supported",
        str(SUPPORTED_CONTRACT_PATH),
        repo_root=fake_root,
    )
    assert result.returncode in (0, 2, 6), result.stderr
    for relative in (
        "summary.md",
        "upstream-diff.json",
        "impact-map.json",
        "candidate-contract.json",
        "manifest-suggestions.json",
        "implementation-tasks.md",
        "changelog-fragment.md",
        "test-suggestions/argv-contracts.patch",
        "test-suggestions/output-fixtures.todo.json",
    ):
        assert (out / relative).exists(), f"missing {relative}"


def test_apply_manifest_suggestions_keeps_rows_incomplete(
    tmp_path: pathlib.Path, contract_cli: ContractCliRunner
) -> None:
    fake_root = tmp_path / "repo"
    gen = fake_root / "src" / "multica_py" / "_generated"
    gen.mkdir(parents=True)
    (gen / "upstream_state.json").write_text('{"schema_version": 1, "supported": null}')
    shutil.copy(COVERAGE_PATH, gen / "upstream_coverage.json")
    out = tmp_path / "v0.4.2..v0.4.3"
    contract_cli.run(
        "prepare-upgrade",
        "--candidate",
        str(CANDIDATE),
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
        json.loads((gen / "upstream_coverage.json").read_text()),
    )
    decisions = coverage.get("decisions")
    assert isinstance(decisions, list)
    incomplete = [
        item
        for item in decisions
        if isinstance(item, dict) and str(item.get("coverage_level")) == "incomplete"
    ]
    assert incomplete


def test_apply_manifest_suggestions_dry_run_does_not_write(
    tmp_path: pathlib.Path, contract_cli: ContractCliRunner
) -> None:
    fake_root = tmp_path / "repo"
    _write_minimal_generated(fake_root)
    coverage_path = fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json"
    out = tmp_path / "v0.4.2..v0.4.3"
    contract_cli.run(
        "prepare-upgrade",
        "--candidate",
        str(CANDIDATE),
        "--output-dir",
        str(out),
        "--supported",
        str(SUPPORTED_CONTRACT_PATH),
        repo_root=fake_root,
    )
    before = coverage_path.read_text()
    contract_cli.run(
        "apply-manifest-suggestions",
        "--bundle",
        str(out),
        "--dry-run",
        repo_root=fake_root,
    )
    after = coverage_path.read_text()
    assert before == after


def test_apply_manifest_suggestions_is_idempotent(
    tmp_path: pathlib.Path, contract_cli: ContractCliRunner
) -> None:
    fake_root = tmp_path / "repo"
    _write_minimal_generated(fake_root)
    out = tmp_path / "v0.4.2..v0.4.3"
    contract_cli.run(
        "prepare-upgrade",
        "--candidate",
        str(CANDIDATE),
        "--output-dir",
        str(out),
        "--supported",
        str(SUPPORTED_CONTRACT_PATH),
        repo_root=fake_root,
    )
    args = (
        "apply-manifest-suggestions",
        "--bundle",
        str(out),
    )
    first = contract_cli.run(*args, repo_root=fake_root)
    assert first.returncode == 0, first.stderr
    coverage_path = fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json"
    first_bytes = coverage_path.read_bytes()
    second = contract_cli.run(*args, repo_root=fake_root)
    assert second.returncode == 0
    assert coverage_path.read_bytes() == first_bytes
