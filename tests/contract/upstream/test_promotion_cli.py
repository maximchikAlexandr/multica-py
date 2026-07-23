"""Boundary test for the upstream promotion CLI subcommands.

Covers `promote`, `reject`, and `compat` end-to-end via the real
script entry point. Pure promotion/validation logic lives in
`tests/unit/test_upstream_contract_promotion.py`.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import cast

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "upstream_contract.py"


def _write_state(fake_root: pathlib.Path, supported_version: str) -> None:
    gen = fake_root / "src" / "multica_py" / "_generated"
    gen.mkdir(parents=True)
    state = {
        "schema_version": 1,
        "supported": {
            "version": supported_version,
            "tag": f"v{supported_version}",
            "commit": "0" * 40,
            "semantic_hash": "sha256:0",
            "contract_ref": "x.json",
        },
    }
    (gen / "upstream_state.json").write_text(json.dumps(state))


def _run(args: list[str], repo_root: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo-root", str(repo_root)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_promote_requires_decision_file(tmp_path: pathlib.Path) -> None:
    fake_root = tmp_path / "repo"
    _write_state(fake_root, "0.4.2")
    result = _run(["promote", "--check"], fake_root)
    assert result.returncode != 0


def test_reject_clears_candidate_field(tmp_path: pathlib.Path) -> None:
    fake_root = tmp_path / "repo"
    gen = fake_root / "src" / "multica_py" / "_generated"
    gen.mkdir(parents=True)
    state = {
        "schema_version": 1,
        "supported": {
            "version": "0.4.2",
            "tag": "v0.4.2",
            "commit": "0" * 40,
            "semantic_hash": "sha256:0",
            "contract_ref": "x.json",
        },
        "candidate": {
            "version": "0.4.3",
            "tag": "v0.4.3",
            "commit": "abc1234567890abcdef1234567890abcdef12345",
            "semantic_hash": "sha256:abc",
            "contract_ref": "x.json",
            "trust_level": "verified",
        },
    }
    (gen / "upstream_state.json").write_text(json.dumps(state))
    decision = {
        "schema_version": 1,
        "candidate_version": "0.4.3",
        "candidate_tag": "v0.4.3",
        "candidate_commit": "abc1234567890abcdef1234567890abcdef12345",
        "candidate_semantic_hash": "sha256:abc",
        "previous_supported_version": "0.4.2",
        "previous_supported_commit": "0" * 40,
        "clean_gate_ref": "ci/check",
        "reviewer": "alice",
        "reason": "rollback",
    }
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(decision))
    result = _run(["reject", "--decision", str(decision_path)], fake_root)
    assert result.returncode == 0, result.stderr
    state = cast("dict[str, object]", json.loads((gen / "upstream_state.json").read_text()))
    assert "candidate" not in state or state["candidate"] is None


def test_compat_subcommand_runs(tmp_path: pathlib.Path) -> None:
    fake_root = tmp_path / "repo"
    _write_state(fake_root, "0.4.2")
    result = _run(["compat", "--sdk-version", "0.4.2"], fake_root)
    assert result.returncode == 0, result.stderr
    assert "0.4" in result.stdout
