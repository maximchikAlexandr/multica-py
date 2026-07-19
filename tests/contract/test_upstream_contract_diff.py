from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import cast

import pytest

from tests.contract.mutation_severity_cases import MUTATION_SEVERITY_CASES, MutationSeverityCase

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "upstream_contract.py"

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"
MUTATIONS = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "mutations"
BASELINE = FIXTURES / "supported-cli-contract-baseline.json"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo-root", str(ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("case", MUTATION_SEVERITY_CASES, ids=lambda c: c.id)  # type: ignore[misc]
def test_mutation_severity(case: MutationSeverityCase, tmp_path: pathlib.Path) -> None:
    """Verify each mutation fixture produces the expected severity via CLI."""
    target = tmp_path / "diff.json"
    result = _run(
        [
            "diff",
            "--from",
            str(BASELINE),
            "--to",
            str(MUTATIONS / case.mutation_file),
            "--format",
            "json",
            "--output",
            str(target),
        ]
    )
    payload = cast("dict[str, object]", json.loads(target.read_text()))
    changes = cast("list[dict[str, object]]", payload["changes"])
    severities = {c["severity"] for c in changes}
    for s in case.must_contain:
        assert s in severities
    for s in case.must_not_contain:
        assert s not in severities
    if case.id == "help-text-changed":
        assert severities
        assert severities <= {"doc_only", "provenance_only"}
    if case.unresolved_breaking is not None:
        if case.unresolved_breaking is True:
            assert result.returncode == 6
        else:
            assert result.returncode != 6


def test_diff_command_emits_valid_json() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        target = pathlib.Path(tmp) / "diff.json"
        result = _run(
            [
                "diff",
                "--from",
                str(BASELINE),
                "--to",
                str(FIXTURES / "candidate-cli-contract-v2.json"),
                "--format",
                "json",
                "--output",
                str(target),
            ]
        )
        assert result.returncode in (2, 6)
        payload = cast("dict[str, object]", json.loads(target.read_text()))
        assert "changes" in payload
        assert "summary" in payload
