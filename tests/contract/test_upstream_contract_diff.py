from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import cast

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


def test_diff_command_required_flag_exits_unresolved_breaking() -> None:
    result = _run(
        [
            "diff",
            "--from",
            str(BASELINE),
            "--to",
            str(MUTATIONS / "required-flag-added.json"),
            "--format",
            "human",
        ]
    )
    assert result.returncode == 6  # EXIT_UNRESOLVED_BREAKING


def test_diff_command_doc_only_exits_clean() -> None:
    result = _run(
        [
            "diff",
            "--from",
            str(BASELINE),
            "--to",
            str(MUTATIONS / "help-text-changed.json"),
            "--format",
            "human",
        ]
    )
    assert result.returncode == 0


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
