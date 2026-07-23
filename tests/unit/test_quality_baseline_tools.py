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
from scripts.capture_test_baseline import capture_baseline

_BASELINE_SHA = "c69243c5cafe38aa26f774bb266f28a5cb883b36"
_SOURCE_SNAPSHOT = "b3a299b36d1ad5bc386b5e4517d2a348d53db31c"
_THRESHOLDS = {"transport": 80, "models": 90, "resources": 70, "errors": 95}


@dataclass(frozen=True)
class CoverageCase:
    id: str
    files: dict[str, object] | None
    expect_exit: int
    stderr_fragment: str | None = None
    missing_threshold: bool = False
    missing_files: bool = False


@dataclass(frozen=True)
class Schema2BaselineCase:
    id: str
    schema: int
    git_sha: str
    source_snapshot: str
    expect_error: bool
    error_fragment: str | None = None


@dataclass(frozen=True)
class MutationParseCase:
    id: str
    content: str
    expected_killed: int
    expected_score: float


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


def _baseline_payload_v2() -> dict[str, Any]:
    return {
        "schema": 2,
        "git_sha": _BASELINE_SHA,
        "source_snapshot": _SOURCE_SNAPSHOT,
        "coverage": {
            "statement_percent": 70.0,
            "branch_percent": 50.0,
            "zones": {"errors": 95.0, "models": 90.0, "resources": 70.0, "transport": 80.0},
            "config_sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        },
        "mutation": {
            "killed": 100,
            "survived": 20,
            "timeout": 0,
            "suspicious": 0,
            "no_tests": 0,
            "skipped": 0,
            "score_percent": 83.33,
            "config_sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        },
        "behavior": {
            "requirements_sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "operation_pairs": 111,
            "invariants": 11,
        },
        "loc": {
            "tests_python": 1000,
            "live_support_python": 100,
            "scripts_python": 200,
            "max_test_support_file": 300,
        },
        "offline": {
            "duration_seconds": 10.0,
            "collected": {},
        },
        "package_install_paths": 6,
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
    with pytest.raises(SystemExit, match="2"):
        check_test_baseline.main(
            ["--baseline", "tests/quality-baseline.json", "--stage", "unknown"]
        )


def test_check_baseline_compare_pr1_passes(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline_path = tmp_path / "baseline.json"
    payload = _baseline_payload_v2()
    baseline_path.write_bytes(check_test_baseline._serialize_baseline(payload))
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(check_test_baseline, "_assert_baseline_bytes_unchanged", lambda *_: None)
    assert check_test_baseline.compare_baseline(baseline_path, "pr1", repo_root) == 0


def test_check_baseline_compare_final_stage(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Final stage NOTE / strict modes against final LOC caps."""
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_bytes(check_test_baseline._serialize_baseline(_baseline_payload_v2()))
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    wf_dir = repo_root / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "package-test.yml").write_text(
        "jobs:\n  test:\n    strategy:\n      matrix:\n        path:\n          - wheel\n          - sdist\n          - src\n          - src-isolated\n          - editable\n          - system-python\n",
        encoding="utf-8",
    )
    tests_dir = repo_root / "tests"
    tests_dir.mkdir()
    for i in range(14):
        (tests_dir / f"f{i}.py").write_text("x = 1\n" * 800, encoding="utf-8")
    monkeypatch.setattr(check_test_baseline, "_assert_baseline_bytes_unchanged", lambda *_: None)
    assert (
        check_test_baseline.compare_baseline(baseline_path, "final", repo_root, strict_final=False)
        == 0
    )
    with pytest.raises(SystemExit, match="cap"):
        check_test_baseline.compare_baseline(baseline_path, "final", repo_root, strict_final=True)


def test_capture_baseline_mutation_results(tmp_path: pathlib.Path) -> None:
    results_path = tmp_path / "mutmut-results.txt"
    results_path.write_text(
        "killed=120\nsurvived=30\ntimeout=2\nsuspicious=1\nno_tests=5\nskipped=3\n",
        encoding="utf-8",
    )
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    wf_dir = repo_root / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "package-test.yml").write_text(
        'jobs:\n  test:\n    strategy:\n      matrix:\n        path:\n          - ubuntu-latest\n        python-version:\n          - "3.12"\n',
        encoding="utf-8",
    )
    (repo_root / "pyproject.toml").write_text(
        '[tool.mutmut]\npaths_to_mutate = ["src"]\n', encoding="utf-8"
    )
    (repo_root / "tests").mkdir()
    output_path = tmp_path / "baseline.json"
    exit_code = capture_baseline(
        _BASELINE_SHA,
        _SOURCE_SNAPSHOT,
        coverage_path=None,
        junit_path=None,
        mutation_path=results_path,
        behavior_path=None,
        output_path=output_path,
        repo_root=repo_root,
    )
    assert exit_code == 0
    parsed: object = json.loads(output_path.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict)
    mutation = parsed.get("mutation")
    assert isinstance(mutation, dict)
    assert mutation["killed"] == 120
    assert mutation["survived"] == 30
    assert mutation["score_percent"] == 80.0
    assert mutation["timeout"] == 2
    assert mutation["suspicious"] == 1
    assert mutation["no_tests"] == 5
    assert mutation["skipped"] == 3


_MUTATION_PARSE_CASES = (
    MutationParseCase("basic", "killed=10\nsurvived=5\n", 10, 66.67),
    MutationParseCase("all-killed", "killed=50\nsurvived=0\n", 50, 100.0),
    MutationParseCase("empty", "", 0, 0.0),
    MutationParseCase(
        "extra-fields",
        "killed=8\nsurvived=2\ntimeout=1\nsuspicious=0\nno_tests=1\nskipped=0\n",
        8,
        80.0,
    ),
    MutationParseCase("zero-killed", "killed=0\nsurvived=10\n", 0, 0.0),
)


@pytest.mark.parametrize("case", _MUTATION_PARSE_CASES, ids=lambda case: case.id)
def test_parse_mutation_results(tmp_path: pathlib.Path, case: MutationParseCase) -> None:
    from scripts.capture_test_baseline import _parse_mutation_results

    path = tmp_path / "results.txt"
    path.write_text(case.content, encoding="utf-8")
    result = _parse_mutation_results(path)
    assert result["killed"] == case.expected_killed
    assert result["score_percent"] == case.expected_score


def test_loc_counting(tmp_path: pathlib.Path) -> None:
    from scripts._loc_metrics import (
        glob_logical_lines,
        live_support_loc,
        max_test_support_file,
    )

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "tests" / "unit").mkdir(parents=True)
    (repo_root / "tests" / "live").mkdir(parents=True)
    (repo_root / "tools" / "live_support").mkdir(parents=True)
    (repo_root / "scripts").mkdir()
    (repo_root / "tests" / "unit" / "test_a.py").write_text(
        "def test_a(): pass\n", encoding="utf-8"
    )
    (repo_root / "tests" / "live" / "helper.py").write_text(
        "def helper(): pass\n", encoding="utf-8"
    )
    (repo_root / "tools" / "live_support" / "env.py").write_text(
        "def env(): pass\n", encoding="utf-8"
    )
    (repo_root / "scripts" / "build.py").write_text("def build(): pass\n", encoding="utf-8")
    assert glob_logical_lines(repo_root / "tests", "**/*.py") == 2
    assert live_support_loc(repo_root) == 2
    assert max_test_support_file(repo_root) == 1


_SCHEMA2_CASES = (
    Schema2BaselineCase("valid", 2, _BASELINE_SHA, _SOURCE_SNAPSHOT, False),
    Schema2BaselineCase(
        "wrong-schema", 1, _BASELINE_SHA, _SOURCE_SNAPSHOT, True, "schema must be 2"
    ),
    Schema2BaselineCase(
        "bad-git-sha", 2, "not-a-sha", _SOURCE_SNAPSHOT, True, "git_sha must be 40"
    ),
)


def test_schema2_assert_schema() -> None:
    for case in _SCHEMA2_CASES:
        payload = _baseline_payload_v2()
        payload["schema"] = case.schema
        payload["git_sha"] = case.git_sha
        payload["source_snapshot"] = case.source_snapshot
        if case.expect_error:
            with pytest.raises(SystemExit, match=case.error_fragment or ""):
                check_test_baseline._assert_schema(payload)
        else:
            check_test_baseline._assert_schema(payload)


def test_duration_limit_formula() -> None:
    assert max(45.0, 10.0 * 1.5) == 45.0
    assert max(45.0, 100.0 * 1.5) == 150.0


def test_fingerprint_comparison(tmp_path: pathlib.Path) -> None:
    from scripts.capture_test_baseline import _config_fingerprint

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text(
        '[tool.coverage.run]\nsource = ["multica_py"]\n[tool.mutmut]\npaths_to_mutate = ["src"]\n',
        encoding="utf-8",
    )
    coverage_fp = _config_fingerprint(repo_root, ["tool.coverage.run"])
    assert coverage_fp.startswith("sha256:")
    mutmut_fp = _config_fingerprint(repo_root, ["tool.mutmut"])
    assert mutmut_fp.startswith("sha256:")
    assert coverage_fp != mutmut_fp
