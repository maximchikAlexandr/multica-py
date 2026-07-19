from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
from typing import cast

from multica_py._internal.upstream_contract import schema
from multica_py._internal.upstream_contract.normalize import semantic_hash

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "upstream_contract.py"
STATE_REL = "src/multica_py/_generated/upstream_state.json"
CANDIDATE_CONTRACT_REL = "src/multica_py/_generated/upstream_candidate_contract.json"


def _json_object(raw: str) -> dict[str, object]:
    return cast("dict[str, object]", json.loads(raw))


def _candidate_field(state: dict[str, object], field: str) -> object:
    candidate = state["candidate"]
    assert isinstance(candidate, dict)
    return candidate[field]


def _fake_multica_with_exporter(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "fake_multica"
    p.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "__contract" ]; then\n'
        "  cat <<JSON\n"
        '{"commands":[{"path":["agent"],"use":"list","flags":[]}]}\n'
        "JSON\n"
        'elif [ "$1" = "--help" ]; then\n'
        "  echo Available Commands:\n"
        "  echo agent\n"
        "else\n"
        "  echo Usage\n"
        "fi\n"
    )
    p.chmod(0o755)
    return p


def _sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_candidate_collection_is_deterministic(tmp_path: pathlib.Path) -> None:
    fake = _fake_multica_with_exporter(tmp_path)
    sha = _sha256_of(fake)
    out_a = tmp_path / "a.json"
    out_b = tmp_path / "b.json"
    common = [
        "--binary",
        str(fake),
        "--version",
        "0.4.3",
        "--tag",
        "v0.4.3",
        "--commit",
        "abc1234567890abcdef1234567890abcdef12345",
        "--asset-name",
        "multica-0.4.3.tar.gz",
        "--sha256",
        sha,
        "--os",
        "linux",
        "--arch",
        "amd64",
        "--version-output",
        "multica 0.4.3",
    ]
    for target in (out_a, out_b):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "collect",
                *common,
                "--output",
                str(target),
                "--repo-root",
                str(ROOT),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
    payload_a = _json_object(out_a.read_text())
    payload_b = _json_object(out_b.read_text())
    payload_a.pop("observation", None)
    payload_b.pop("observation", None)
    assert payload_a == payload_b


def test_collect_registers_candidate_with_verified_trust(tmp_path: pathlib.Path) -> None:
    fake = _fake_multica_with_exporter(tmp_path)
    sha = _sha256_of(fake)
    out = tmp_path / "outside" / "candidate.json"
    state_path = ROOT / STATE_REL
    original_state = state_path.read_text(encoding="utf-8")
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
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
                "multica-0.4.3.tar.gz",
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
                "--repo-root",
                str(ROOT),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        state = _json_object(state_path.read_text(encoding="utf-8"))
        assert _candidate_field(state, "trust_level") == "verified"
        assert _candidate_field(state, "contract_ref") == CANDIDATE_CONTRACT_REL
        assert (ROOT / CANDIDATE_CONTRACT_REL).is_file()
    finally:
        state_path.write_text(original_state, encoding="utf-8")
        generated = ROOT / CANDIDATE_CONTRACT_REL
        if generated.exists():
            generated.unlink()


def test_collect_persists_in_repo_output_outside_generated(tmp_path: pathlib.Path) -> None:
    fake = _fake_multica_with_exporter(tmp_path)
    sha = _sha256_of(fake)
    out = ROOT / "artifacts" / "upstream-upgrades" / "collect-test-candidate.json"
    state_path = ROOT / STATE_REL
    original_state = state_path.read_text(encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
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
                "multica-0.4.3.tar.gz",
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
                "--repo-root",
                str(ROOT),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        canonical = _json_object((ROOT / CANDIDATE_CONTRACT_REL).read_text(encoding="utf-8"))
        custom = _json_object(out.read_text(encoding="utf-8"))
        canonical.pop("observation", None)
        custom.pop("observation", None)
        assert canonical == custom
        state = _json_object(state_path.read_text(encoding="utf-8"))
        assert (
            _candidate_field(state, "contract_ref")
            == "artifacts/upstream-upgrades/collect-test-candidate.json"
        )
        assert (ROOT / CANDIDATE_CONTRACT_REL).is_file()
    finally:
        state_path.write_text(original_state, encoding="utf-8")
        generated = ROOT / CANDIDATE_CONTRACT_REL
        if generated.exists():
            generated.unlink()
        if out.exists():
            out.unlink()


def test_collect_verified_hash_on_disk_matches_promotion(tmp_path: pathlib.Path) -> None:
    fake = _fake_multica_with_exporter(tmp_path)
    sha = _sha256_of(fake)
    out = tmp_path / "candidate.json"
    state_path = ROOT / STATE_REL
    original_state = state_path.read_text(encoding="utf-8")
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
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
                "multica-0.4.3.tar.gz",
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
                "--repo-root",
                str(ROOT),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        on_disk = _json_object((ROOT / CANDIDATE_CONTRACT_REL).read_text(encoding="utf-8"))
        artifact = on_disk["artifact"]
        assert isinstance(artifact, dict)
        disk_hash = artifact["semantic_hash"]
        assert isinstance(disk_hash, str)
        assert disk_hash.startswith("sha256:")
        contract = schema.decode_contract(ROOT / CANDIDATE_CONTRACT_REL)
        assert disk_hash == semantic_hash(contract)
        state = _json_object(state_path.read_text(encoding="utf-8"))
        assert _candidate_field(state, "semantic_hash") == disk_hash
        assert _candidate_field(state, "trust_level") == "verified"
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
    finally:
        state_path.write_text(original_state, encoding="utf-8")
        generated = ROOT / CANDIDATE_CONTRACT_REL
        if generated.exists():
            generated.unlink()
