from __future__ import annotations

import pathlib

from multica_py._internal.upstream_contract.paths import SUPPORTED_CONTRACT_PATH

from .conftest import ContractCliRunner, json_object

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"


def test_quickstart_check(contract_cli: ContractCliRunner) -> None:
    result = contract_cli.run("check", "--format", "human")
    assert result.returncode in (0, 2, 3, 6)


def test_quickstart_collect(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
) -> None:
    out = tmp_path / "candidate.json"
    result = contract_cli.run(
        "collect",
        "--output",
        str(out),
    )
    assert result.returncode == 0
    payload = json_object(out.read_text())
    assert payload["schema_version"] == 2


def test_quickstart_diff(contract_cli: ContractCliRunner) -> None:
    result = contract_cli.run(
        "diff",
        "--from",
        str(SUPPORTED_CONTRACT_PATH),
        "--to",
        str(FIXTURES / "candidate-cli-contract-v2.json"),
        "--format",
        "human",
    )
    assert result.returncode in (2, 6)


def test_quickstart_prepare_upgrade(
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
        "--repo-root",
        str(fake_root),
        repo_root=fake_root,
    )
    assert result.returncode in (0, 2, 6)
    assert (out / "summary.md").exists()


def test_quickstart_observe_dry_run(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
) -> None:
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    result = contract_cli.run(
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
        repo_root=fake_root,
    )
    assert result.returncode == 0
