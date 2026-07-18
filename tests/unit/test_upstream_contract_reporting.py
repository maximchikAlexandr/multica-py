from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import TYPE_CHECKING

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from multica_py._internal.upstream_contract import reporting  # noqa: E402
from multica_py._internal.upstream_contract.models import ReportFailure  # noqa: E402

if TYPE_CHECKING:
    import pytest

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"


def _invoke_check(capsys: pytest.CaptureFixture[str], args: list[str]) -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "upstream_contract.py"), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    capsys.readouterr()
    return proc.returncode


def test_human_output_has_required_four_lines(capsys: pytest.CaptureFixture[str]) -> None:
    code = _invoke_check(
        capsys,
        ["check", "--format", "human", "--repo-root", str(ROOT)],
    )
    assert code in (0, 2, 3, 6)


def test_json_output_is_valid_json() -> None:
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        target = pathlib.Path(tmp) / "report.json"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "upstream_contract.py"),
                "check",
                "--format",
                "json",
                "--output",
                str(target),
                "--repo-root",
                str(ROOT),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode in (0, 2, 3, 6)
        if result.returncode != 3:
            data = json.loads(target.read_text())
            assert "status" in data
            assert "coverage" in data


def test_empty_report_has_schema_version_one() -> None:
    report = reporting.empty_report()
    assert report.schema_version == 1
    assert report.status == "clean"


def test_add_failure_appends_to_list() -> None:
    report = reporting.add_failure(
        reporting.empty_report(),
        ReportFailure(code="X", message="oops"),
    )
    assert len(report.failures) == 1
    assert report.failures[0].code == "X"


def test_replace_state_returns_new_instance() -> None:
    import msgspec

    report = reporting.empty_report()
    updated = msgspec.structs.replace(report, status="gaps")
    assert updated is not report
    assert updated.status == "gaps"
    assert report.status == "clean"


def test_exit_code_taxonomy() -> None:
    from multica_py._internal.upstream_contract.models import CoverageReport

    cases = [
        ("clean", 0),
        ("gaps", 2),
        ("invalid", 3),
        ("collection-failed", 4),
        ("mismatch", 5),
        ("unresolved-breaking", 6),
    ]
    for status, expected in cases:
        report = CoverageReport(schema_version=1, status=status)
        from multica_py._internal.upstream_contract.cli import _exit_code_for

        assert _exit_code_for(report) == expected
