from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from .conftest import ContractCliRunner, candidate_field, json_object

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
STATE_REL = "src/multica_py/_generated/upstream_state.json"
CANDIDATE_CONTRACT_REL = "src/multica_py/_generated/upstream_candidate_contract.json"
SCRIPT = ROOT / "scripts" / "upstream_contract.py"

pytestmark = pytest.mark.serial


@pytest.mark.parametrize(
    "output_rel",
    [
        pytest.param(None, id="tmp"),
        pytest.param(
            "artifacts/upstream-upgrades/determinism-candidate.json",
            id="custom",
        ),
    ],
)
def test_candidate_collection_is_deterministic(
    tmp_path: pathlib.Path,
    output_rel: str | None,
    contract_cli: ContractCliRunner,
    preserved_generated_state: None,
) -> None:
    if output_rel is not None:
        out = ROOT / output_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.unlink(missing_ok=True)
    else:
        out = tmp_path / "candidate.json"
    first = contract_cli.run(
        "collect",
        "--output",
        str(out),
    )
    assert first.returncode == 0, first.stderr
    payload_a = json_object(out.read_text())
    out.unlink(missing_ok=True)
    second = contract_cli.run(
        "collect",
        "--output",
        str(out),
    )
    assert second.returncode == 0, second.stderr
    payload_b = json_object(out.read_text())
    payload_a.pop("observation", None)
    payload_b.pop("observation", None)
    assert payload_a == payload_b


def test_collect_registers_candidate_with_verified_trust(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
    preserved_generated_state: None,
) -> None:
    state_path = ROOT / STATE_REL
    out = tmp_path / "candidate.json"
    result = contract_cli.run(
        "collect",
        "--output",
        str(out),
    )
    assert result.returncode == 0, result.stderr
    state = json_object(state_path.read_text(encoding="utf-8"))
    assert candidate_field(state, "trust_level") == "verified"
    assert candidate_field(state, "contract_ref") == CANDIDATE_CONTRACT_REL
    assert (ROOT / CANDIDATE_CONTRACT_REL).is_file()


@pytest.mark.parametrize(
    ("output_rel", "expected_ref"),
    [
        pytest.param(None, CANDIDATE_CONTRACT_REL, id="canonical"),
        pytest.param(
            "artifacts/upstream-upgrades/collect-test-candidate.json",
            "artifacts/upstream-upgrades/collect-test-candidate.json",
            id="custom",
        ),
    ],
)
def test_collect_persists_in_repo_output_outside_generated(
    tmp_path: pathlib.Path,
    output_rel: str | None,
    expected_ref: str,
    contract_cli: ContractCliRunner,
    preserved_generated_state: None,
) -> None:
    state_path = ROOT / STATE_REL
    if output_rel is not None:
        out = ROOT / output_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.unlink(missing_ok=True)
    else:
        out = tmp_path / "candidate.json"
    result = contract_cli.run(
        "collect",
        "--output",
        str(out),
    )
    assert result.returncode == 0, result.stderr
    state = json_object(state_path.read_text(encoding="utf-8"))
    assert candidate_field(state, "contract_ref") == expected_ref
    assert (ROOT / CANDIDATE_CONTRACT_REL).is_file()
    if output_rel is not None:
        canonical = json_object((ROOT / CANDIDATE_CONTRACT_REL).read_text(encoding="utf-8"))
        custom = json_object(out.read_text(encoding="utf-8"))
        canonical.pop("observation", None)
        custom.pop("observation", None)
        assert canonical == custom


def test_collect_verified_hash_on_disk_matches_promotion(
    tmp_path: pathlib.Path,
    contract_cli: ContractCliRunner,
    preserved_generated_state: None,
) -> None:
    out = tmp_path / "candidate.json"
    state_path = ROOT / STATE_REL
    result = contract_cli.run(
        "collect",
        "--output",
        str(out),
    )
    assert result.returncode == 0, result.stderr
    on_disk = json_object((ROOT / CANDIDATE_CONTRACT_REL).read_text(encoding="utf-8"))
    artifact = on_disk["artifact"]
    assert isinstance(artifact, dict)
    disk_hash = artifact["semantic_hash"]
    assert isinstance(disk_hash, str)
    assert disk_hash.startswith("sha256:")
    state = json_object(state_path.read_text(encoding="utf-8"))
    assert candidate_field(state, "semantic_hash") == disk_hash
    assert candidate_field(state, "trust_level") == "verified"
    decision_path = tmp_path / "decision.json"
    supported = state["supported"]
    assert isinstance(supported, dict)
    supported_version = supported.get("version")
    supported_commit = supported.get("commit")
    assert isinstance(supported_version, str)
    assert isinstance(supported_commit, str)
    decision_payload: dict[str, str | int] = {
        "schema_version": 1,
        "candidate_version": "0.4.3",
        "candidate_tag": "v0.4.3",
        "candidate_commit": "abc1234567890abcdef1234567890abcdef12345",
        "candidate_semantic_hash": disk_hash,
        "previous_supported_version": supported_version,
        "previous_supported_commit": supported_commit,
        "clean_gate_ref": "ci/check",
        "reviewer": "alice",
    }
    decision_path.write_text(json.dumps(decision_payload), encoding="utf-8")
    promote = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "promote",
            "--decision",
            str(decision_path),
            "--check",
            "--repo-root",
            str(ROOT),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert promote.returncode == 0, promote.stderr
