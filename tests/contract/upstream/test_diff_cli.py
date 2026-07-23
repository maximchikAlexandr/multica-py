"""Boundary test for the upstream `diff` CLI subcommand.

Representative smoke tests: diff between two contract files via the
real script entry point yields a JSON payload with `changes` and
`summary` keys. Exhaustive severity/mutation coverage lives in
`tests/unit/test_upstream_contract_diff.py`.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import cast

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "upstream_contract.py"

FIXTURES = pathlib.Path(__file__).resolve().parents[2] / "fixtures" / "upstream_contract" / "golden"
BASELINE = FIXTURES / "supported-cli-contract-baseline.json"
CANDIDATE = FIXTURES / "candidate-cli-contract-v2.json"
MUTATIONS = FIXTURES.parent / "mutations"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo-root", str(ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_diff_command_emits_valid_json(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "diff.json"
    result = _run(
        [
            "diff",
            "--from",
            str(BASELINE),
            "--to",
            str(CANDIDATE),
            "--format",
            "json",
            "--output",
            str(target),
        ]
    )
    assert result.returncode in (0, 2, 6), result.stderr
    payload = cast("dict[str, object]", json.loads(target.read_text()))
    assert "changes" in payload
    assert "summary" in payload


def test_diff_required_flag_added_is_breaking(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "diff.json"
    result = _run(
        [
            "diff",
            "--from",
            str(BASELINE),
            "--to",
            str(MUTATIONS / "required-flag-added.json"),
            "--format",
            "json",
            "--output",
            str(target),
        ]
    )
    assert result.returncode == 6, result.stderr
    payload = cast("dict[str, object]", json.loads(target.read_text()))
    severities = {
        cast("str", c["severity"]) for c in cast("list[dict[str, object]]", payload["changes"])
    }
    assert "breaking" in severities


def test_diff_help_text_change_is_doc_only(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "diff.json"
    result = _run(
        [
            "diff",
            "--from",
            str(BASELINE),
            "--to",
            str(MUTATIONS / "help-text-changed.json"),
            "--format",
            "json",
            "--output",
            str(target),
        ]
    )
    assert result.returncode in (0, 2), result.stderr
    payload = cast("dict[str, object]", json.loads(target.read_text()))
    severities = {
        cast("str", c["severity"]) for c in cast("list[dict[str, object]]", payload["changes"])
    }
    assert severities <= {"doc_only", "provenance_only"}


def test_diff_command_added_is_additive(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "diff.json"
    _run(
        [
            "diff",
            "--from",
            str(BASELINE),
            "--to",
            str(MUTATIONS / "command-added.json"),
            "--format",
            "json",
            "--output",
            str(target),
        ]
    )
    payload = cast("dict[str, object]", json.loads(target.read_text()))
    severities = {
        cast("str", c["severity"]) for c in cast("list[dict[str, object]]", payload["changes"])
    }
    assert "additive" in severities
