from __future__ import annotations

import pathlib

from multica_py._internal.upstream_contract.paths import SUPPORTED_CONTRACT_PATH

from .conftest import ContractCliRunner

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"


def test_apply_manifest_suggestions_is_idempotent(
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
        "--repo-root",
        str(fake_root),
        repo_root=fake_root,
    )
    args = (
        "apply-manifest-suggestions",
        "--bundle",
        str(out),
        "--repo-root",
        str(fake_root),
    )
    first = contract_cli.run(*args, repo_root=fake_root)
    assert first.returncode == 0
    manifest_path = fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json"
    first_bytes = manifest_path.read_bytes()
    second = contract_cli.run(*args, repo_root=fake_root)
    assert second.returncode == 0
    assert manifest_path.read_bytes() == first_bytes


def test_apply_manifest_suggestions_dry_run_does_not_write(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
) -> None:
    out = tmp_path / "v0.4.2..v0.4.3"
    fake_root = tmp_path / "repo"
    (fake_root / "src" / "multica_py" / "_generated").mkdir(parents=True)
    (fake_root / "src" / "multica_py" / "_generated" / "upstream_state.json").write_text(
        '{"schema_version": 1, "supported": null}'
    )
    coverage_path = fake_root / "src" / "multica_py" / "_generated" / "upstream_coverage.json"
    coverage_path.write_text('{"schema_version": 1, "decisions": []}')
    contract_cli.run(
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
    before = coverage_path.read_text()
    contract_cli.run(
        "apply-manifest-suggestions",
        "--bundle",
        str(out),
        "--dry-run",
        "--repo-root",
        str(fake_root),
        repo_root=fake_root,
    )
    after = coverage_path.read_text()
    assert before == after
