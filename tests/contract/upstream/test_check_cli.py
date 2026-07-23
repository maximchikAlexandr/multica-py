"""Boundary test for the upstream `check` CLI subcommand.

Representative smoke tests: end-to-end subprocess invocation against the
real script entry point, with a fake upstream binary. Exhaustive coverage
of `check` internals lives in `tests/unit/test_upstream_contract_*.py`.
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable
from typing import cast

from tests.contract.conftest import ContractCliRunner

ROOT = pathlib.Path(__file__).resolve().parents[3]


def test_check_human_clean_exits_zero(contract_cli: ContractCliRunner) -> None:
    result = contract_cli.run("check", "--format", "human")
    assert result.returncode == 0
    assert "Multica upstream coverage" in result.stdout
    assert "Failures: total=0" in result.stdout


def test_check_json_writes_report(tmp_path: pathlib.Path, contract_cli: ContractCliRunner) -> None:
    target = tmp_path / "report.json"
    result = contract_cli.run("check", "--format", "json", output=target)
    assert result.returncode == 0
    payload = cast("dict[str, object]", json.loads(target.read_text()))
    assert payload["status"] == "clean"
    assert "coverage" in payload


def test_check_invalid_state_artifact_exits_three(
    tmp_path: pathlib.Path, contract_cli: ContractCliRunner
) -> None:
    fake_root = tmp_path
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 999, "supported": null}'
    )
    result = contract_cli.run("check", "--format", "human", repo_root=fake_root)
    assert result.returncode == 3


def test_check_check_flag_does_not_write_when_no_output(
    contract_cli: ContractCliRunner, tmp_path: pathlib.Path
) -> None:
    target = tmp_path / "report.json"
    result = contract_cli.run("check", "--format", "json", "--check")
    assert result.returncode == 0
    assert result.stdout == ""
    assert not target.exists()


def test_check_missing_coverage_manifest_exits_three(
    tmp_path: pathlib.Path, contract_cli: ContractCliRunner
) -> None:
    fake_root = tmp_path / "repo"
    generated = fake_root / "src" / "multica_py" / "_generated"
    generated.mkdir(parents=True)
    import shutil

    shutil.copy(
        ROOT / "src" / "multica_py" / "_generated" / "upstream_state.json",
        generated / "upstream_state.json",
    )
    shutil.copy(
        ROOT / "src" / "multica_py" / "_generated" / "upstream_supported_contract.json",
        generated / "upstream_supported_contract.json",
    )
    result = contract_cli.run("check", "--format", "human", repo_root=fake_root)
    assert result.returncode == 3


def test_check_with_candidate_missing_file_exits_three(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
    repo_factory: Callable[..., pathlib.Path],
) -> None:
    fake_root = repo_factory(files={"README.md": "init"})
    gen = fake_root / "src" / "multica_py" / "_generated"
    gen.mkdir(parents=True)
    state = {
        "schema_version": 1,
        "supported": None,
        "candidate": {
            "version": "0.4.3",
            "tag": "v0.4.3",
            "commit": "abc1234567890abcdef1234567890abcdef12345",
            "semantic_hash": "sha256:abc",
            "contract_ref": "artifacts/missing-candidate.json",
            "trust_level": "verified",
        },
    }
    (gen / "upstream_state.json").write_text(json.dumps(state))
    result = contract_cli.run("check", "--format", "human", "--with-candidate", repo_root=fake_root)
    assert result.returncode == 3
