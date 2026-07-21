"""Unit tests for quality baseline gate scripts."""

from __future__ import annotations

import json
import pathlib
import textwrap
from dataclasses import dataclass
from typing import Any
from unittest import mock

import pytest

from scripts import check_coverage, check_test_baseline

_BASELINE_SHA = "c69243c5cafe38aa26f774bb266f28a5cb883b36"
_THRESHOLDS = {"transport": 80, "models": 90, "resources": 70, "errors": 95}


@dataclass(frozen=True)
class CoverageCase:
    """One check_coverage scenario."""

    id: str
    files: dict[str, object] | None
    expect_exit: int
    stderr_fragment: str | None = None
    missing_threshold: bool = False
    missing_files: bool = False


@dataclass(frozen=True)
class CompareCase:
    """One compare_baseline scenario."""

    id: str
    mandatory_offline: int
    expect_exit: int
    match: str | None = None


def _coverage_payload(*, files: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "files": files
        or {
            "src/multica_py/_internal/transport.py": {
                "summary": {"covered_lines": 80, "missing_lines": 20},
            },
            "src/multica_py/models/issues.py": {
                "summary": {"covered_lines": 90, "missing_lines": 10},
            },
            "src/multica_py/resources/issues.py": {
                "summary": {"covered_lines": 70, "missing_lines": 30},
            },
            "src/multica_py/exceptions.py": {
                "summary": {"covered_lines": 95, "missing_lines": 5},
            },
        },
        "totals": {"percent_covered": 71.0, "percent_covered_branches": 54.0},
    }


def _write_pyproject(repo_root: pathlib.Path, *, thresholds: bool) -> None:
    body = (
        """
        [tool.coverage.regexs]
        transport = "multica_py/_internal/transport\\\\.py$"
        models = "multica_py/models/.*"
        resources = "multica_py/resources/.*"
        errors = "multica_py/exceptions\\\\.py$"
        """
        if thresholds
        else """
        [tool.coverage.regexs]
        transport = "multica_py/_internal/transport\\\\.py$"

        [tool.coverage.thresholds]
        """
    )
    thresholds_block = (
        ""
        if not thresholds
        else f"""
        [tool.coverage.thresholds]
        transport = {_THRESHOLDS["transport"]}
        models = {_THRESHOLDS["models"]}
        resources = {_THRESHOLDS["resources"]}
        errors = {_THRESHOLDS["errors"]}
        """
    )
    (repo_root / "pyproject.toml").write_text(
        textwrap.dedent(body + thresholds_block).lstrip(),
        encoding="utf-8",
    )


def _baseline_payload() -> dict[str, Any]:
    return {
        "schema": 1,
        "git_sha": _BASELINE_SHA,
        "collected": {
            "unit": 1,
            "contract": 1,
            "component_source": 1,
            "packaging": 1,
            "live": 1,
        },
        "mandatory_offline": 566,
        "loc": {"tests_python": 1, "scripts_python": 1, "resource_test_support": 100},
        "offline": {"tests": 1, "duration_seconds": 1.0},
        "coverage": {
            "statement_percent": 70.0,
            "branch_percent": 50.0,
            "zones": {"errors": 95.0, "models": 90.0, "resources": 70.0, "transport": 80.0},
        },
        "package_install_paths": 12,
    }


_COVERAGE_CASES = (
    CoverageCase("passes", None, 0),
    CoverageCase(
        "below-threshold",
        {
            "src/multica_py/_internal/transport.py": {
                "summary": {"covered_lines": 10, "missing_lines": 90},
            },
            "src/multica_py/models/issues.py": {
                "summary": {"covered_lines": 90, "missing_lines": 10},
            },
            "src/multica_py/resources/issues.py": {
                "summary": {"covered_lines": 70, "missing_lines": 30},
            },
            "src/multica_py/exceptions.py": {
                "summary": {"covered_lines": 95, "missing_lines": 5},
            },
        },
        1,
        "transport below threshold",
    ),
    CoverageCase("missing-threshold", None, 1, missing_threshold=True),
    CoverageCase("missing-files", None, 0, missing_files=True),
)


@pytest.mark.parametrize("case", _COVERAGE_CASES, ids=lambda case: case.id)
def test_check_coverage(
    tmp_path: pathlib.Path, case: CoverageCase, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_pyproject(repo_root, thresholds=not case.missing_threshold)
    coverage_path = tmp_path / "coverage.json"
    payload = "{}" if case.missing_files else json.dumps(_coverage_payload(files=case.files))
    coverage_path.write_text(payload, encoding="utf-8")
    with mock.patch.object(check_coverage, "_repo_root", return_value=repo_root):
        if case.missing_files:
            with pytest.raises(SystemExit, match="missing files mapping"):
                check_coverage.check_coverage(coverage_path, repo_root)
            return
        assert check_coverage.check_coverage(coverage_path, repo_root) == case.expect_exit
    if case.stderr_fragment:
        assert case.stderr_fragment in capsys.readouterr().err


def test_check_baseline_compare_unknown_stage_exits_two() -> None:
    assert (
        check_test_baseline.main(["--baseline", "tests/quality-baseline.json", "--mode", "compare"])
        == 2
    )


_COMPARE_CASES = (
    CompareCase("pass", 600, 0),
    CompareCase("regression", 100, 1, "mandatory offline count regressed"),
)


@pytest.mark.parametrize("case", _COMPARE_CASES, ids=lambda case: case.id)
def test_check_baseline_compare_mandatory(
    tmp_path: pathlib.Path,
    case: CompareCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_bytes(check_test_baseline._serialize_baseline(_baseline_payload()))
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(check_test_baseline, "_assert_baseline_bytes_unchanged", lambda *_: None)
    monkeypatch.setattr(
        check_test_baseline, "_current_mandatory_offline", lambda _root: case.mandatory_offline
    )
    if case.expect_exit == 0:
        assert check_test_baseline.compare_baseline(baseline_path, "PR-02", repo_root) == 0
    else:
        with pytest.raises(SystemExit, match=case.match):
            check_test_baseline.compare_baseline(baseline_path, "PR-02", repo_root)
