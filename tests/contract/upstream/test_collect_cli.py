"""Boundary test for the upstream `collect` CLI subcommand.

Representative smoke tests: deterministic collect, on-disk trust
registration, and custom output paths. Exhaustive coverage of the
collect pipeline lives in `tests/unit/test_upstream_contract_*.py`.
"""

from __future__ import annotations

import pathlib
from collections.abc import Callable

from tests.contract.conftest import ContractCliRunner, candidate_field, json_object

CANDIDATE_CONTRACT_REL = "src/multica_py/_generated/upstream_candidate_contract.json"


def _init_generated(fake_root: pathlib.Path) -> pathlib.Path:
    gen = fake_root / "src" / "multica_py" / "_generated"
    gen.mkdir(parents=True)
    (gen / "upstream_state.json").write_text('{"schema_version": 1, "supported": null}')
    return gen


def test_collect_writes_canonical_candidate_contract(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
    repo_factory: Callable[..., pathlib.Path],
) -> None:
    fake_root = repo_factory(files={"README.md": "init"})
    _init_generated(fake_root)
    out = tmp_path / "candidate.json"
    result = contract_cli.run("collect", "--output", str(out), repo_root=fake_root)
    assert result.returncode == 0, result.stderr
    payload = json_object(out.read_text())
    assert payload["schema_version"] == 2
    assert (fake_root / CANDIDATE_CONTRACT_REL).is_file()


def test_collect_registers_verified_trust_level(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
    repo_factory: Callable[..., pathlib.Path],
) -> None:
    fake_root = repo_factory(files={"README.md": "init"})
    gen = _init_generated(fake_root)
    out = tmp_path / "candidate.json"
    result = contract_cli.run("collect", "--output", str(out), repo_root=fake_root)
    assert result.returncode == 0, result.stderr
    state = json_object((gen / "upstream_state.json").read_text(encoding="utf-8"))
    assert candidate_field(state, "trust_level") == "verified"
    assert candidate_field(state, "contract_ref") == CANDIDATE_CONTRACT_REL


def test_collect_is_deterministic(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
    repo_factory: Callable[..., pathlib.Path],
) -> None:
    fake_root = repo_factory(files={"README.md": "init"})
    _init_generated(fake_root)
    out = tmp_path / "candidate.json"
    first = contract_cli.run("collect", "--output", str(out), repo_root=fake_root)
    assert first.returncode == 0, first.stderr
    payload_a = json_object(out.read_text())
    out.unlink(missing_ok=True)
    second = contract_cli.run("collect", "--output", str(out), repo_root=fake_root)
    assert second.returncode == 0, second.stderr
    payload_b = json_object(out.read_text())
    payload_a.pop("observation", None)
    payload_b.pop("observation", None)
    assert payload_a == payload_b


def test_collect_custom_output_matches_canonical(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
    repo_factory: Callable[..., pathlib.Path],
) -> None:
    fake_root = repo_factory(files={"README.md": "init"})
    _init_generated(fake_root)
    out = fake_root / "artifacts" / "boundary-candidate.json"
    result = contract_cli.run("collect", "--output", str(out), repo_root=fake_root)
    assert result.returncode == 0, result.stderr
    canonical = json_object((fake_root / CANDIDATE_CONTRACT_REL).read_text(encoding="utf-8"))
    custom = json_object(out.read_text())
    canonical.pop("observation", None)
    custom.pop("observation", None)
    assert canonical == custom
