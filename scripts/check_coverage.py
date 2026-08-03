#!/usr/bin/env python3
"""Validate zonal statement coverage against pyproject thresholds."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tomllib
from typing import cast


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1]


def _load_coverage_config(
    repo_root: pathlib.Path,
) -> tuple[dict[str, str], dict[str, float], dict[str, float]]:
    pyproject = repo_root / "pyproject.toml"
    parsed: object = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise SystemExit("pyproject.toml root must be a table")
    data = cast("dict[str, object]", parsed)
    tool_obj = data.get("tool")
    if not isinstance(tool_obj, dict):
        raise SystemExit("pyproject.toml missing [tool.coverage]")
    tool = cast("dict[str, object]", tool_obj)
    coverage_obj = tool.get("coverage")
    if not isinstance(coverage_obj, dict):
        raise SystemExit("pyproject.toml missing [tool.coverage]")
    coverage = cast("dict[str, object]", coverage_obj)
    regexs_obj = coverage.get("regexs")
    thresholds_obj = coverage.get("thresholds")
    branch_thresholds_obj = coverage.get("branch_thresholds")
    if (
        not isinstance(regexs_obj, dict)
        or not isinstance(thresholds_obj, dict)
        or not isinstance(branch_thresholds_obj, dict)
    ):
        raise SystemExit(
            "pyproject.toml missing [tool.coverage.regexs], [tool.coverage.thresholds], "
            "or [tool.coverage.branch_thresholds]"
        )
    regexs = cast("dict[str, object]", regexs_obj)
    thresholds = cast("dict[str, object]", thresholds_obj)
    branch_thresholds = cast("dict[str, object]", branch_thresholds_obj)
    return (
        {str(name): str(pattern) for name, pattern in regexs.items()},
        _parse_thresholds(thresholds, "threshold"),
        _parse_thresholds(branch_thresholds, "branch threshold"),
    )


def _parse_thresholds(values: dict[str, object], label: str) -> dict[str, float]:
    parsed: dict[str, float] = {}
    for name, value in values.items():
        if isinstance(value, (int, float, str)):
            parsed[str(name)] = float(value)
        else:
            raise SystemExit(f"invalid {label} for {name!r}")
    return parsed


def _statement_counts(file_data: dict[str, object]) -> tuple[int, int]:
    summary = file_data.get("summary")
    if not isinstance(summary, dict):
        return 0, 0
    covered = summary.get("covered_lines")
    missing = summary.get("missing_lines")
    if not isinstance(covered, int) or not isinstance(missing, int):
        num_statements = summary.get("num_statements")
        if isinstance(num_statements, int) and isinstance(covered, int):
            missing_count = num_statements - covered
            return covered, missing_count
        return 0, 0
    return covered, missing


def _branch_counts(file_data: dict[str, object]) -> tuple[int, int] | None:
    summary = file_data.get("summary")
    if not isinstance(summary, dict):
        return None
    covered = summary.get("covered_branches")
    missing = summary.get("missing_branches")
    if not isinstance(covered, int) or not isinstance(missing, int):
        return None
    return covered, missing


def _zone_percentages(
    coverage_data: dict[str, object],
    zone_regexs: dict[str, str],
    *,
    branch: bool = False,
) -> tuple[dict[str, float], set[str], set[str]]:
    files = coverage_data.get("files")
    if not isinstance(files, dict):
        raise SystemExit("coverage JSON missing files mapping")
    compiled = {zone: re.compile(pattern) for zone, pattern in zone_regexs.items()}
    covered_by_zone = dict.fromkeys(zone_regexs, 0)
    missing_by_zone = dict.fromkeys(zone_regexs, 0)
    matched_zones: set[str] = set()
    missing_metrics: set[str] = set()
    for path, file_data in files.items():
        if not isinstance(file_data, dict):
            continue
        for zone, pattern in compiled.items():
            if pattern.search(str(path)):
                matched_zones.add(zone)
                counts = _branch_counts(file_data) if branch else _statement_counts(file_data)
                if counts is None:
                    missing_metrics.add(zone)
                    continue
                covered, missing = counts
                covered_by_zone[zone] += covered
                missing_by_zone[zone] += missing
    percentages: dict[str, float] = {}
    for zone in zone_regexs:
        covered = covered_by_zone[zone]
        missing = missing_by_zone[zone]
        total = covered + missing
        percentages[zone] = 100.0 if total == 0 else (covered / total) * 100.0
    return percentages, matched_zones, missing_metrics


def _has_branch_coverage(coverage_data: dict[str, object]) -> bool:
    meta = coverage_data.get("meta")
    return isinstance(meta, dict) and meta.get("branch_coverage") is True


def check_coverage(coverage_path: pathlib.Path, repo_root: pathlib.Path) -> int:
    """Validate zonal coverage and print sorted zone lines.

    Args:
        coverage_path: Path to coverage.py JSON report.
        repo_root: Repository root containing pyproject.toml.

    Returns:
        Exit code 0 on success, 1 when a zone is missing or below threshold.
    """
    zone_regexs, zone_thresholds, zone_branch_thresholds = _load_coverage_config(repo_root)
    parsed: object = json.loads(coverage_path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise SystemExit("coverage JSON root must be an object")
    payload = cast("dict[str, object]", parsed)
    percentages, statement_zones, _ = _zone_percentages(payload, zone_regexs)
    branch_enabled = _has_branch_coverage(payload)
    branch_percentages, branch_zones, missing_branch_metrics = _zone_percentages(
        payload, zone_regexs, branch=True
    )
    failed = False
    for zone in sorted(zone_regexs):
        if zone not in statement_zones:
            print(f"{zone}: no matching coverage files", file=sys.stderr)
            failed = True
            continue
        percent = percentages[zone]
        threshold = zone_thresholds.get(zone)
        if threshold is None:
            print(f"{zone}: {percent:.2f}% (missing threshold)", file=sys.stderr)
            failed = True
            continue
        print(f"{zone}: {percent:.2f}%")
        if percent < threshold:
            print(
                f"{zone} below threshold {threshold:.2f}% (got {percent:.2f}%)",
                file=sys.stderr,
            )
            failed = True
        branch_threshold = zone_branch_thresholds.get(zone)
        if branch_threshold is None:
            print(f"{zone}: missing branch threshold", file=sys.stderr)
            failed = True
            continue
        if not branch_enabled:
            print(f"{zone}: coverage JSON was not generated with branch coverage", file=sys.stderr)
            failed = True
            continue
        if zone in missing_branch_metrics:
            print(f"{zone}: matching coverage file is missing branch metrics", file=sys.stderr)
            failed = True
            continue
        if zone not in branch_zones:
            print(f"{zone}: no matching branch coverage files", file=sys.stderr)
            failed = True
            continue
        branch_percent = branch_percentages[zone]
        print(f"{zone} branches: {branch_percent:.2f}%")
        if branch_percent < branch_threshold:
            print(
                f"{zone} branches below threshold {branch_threshold:.2f}% "
                f"(got {branch_percent:.2f}%)",
                file=sys.stderr,
            )
            failed = True
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate zonal statement coverage.")
    parser.add_argument("--coverage-json", required=True, type=pathlib.Path)
    namespace = parser.parse_args(argv)
    coverage_json = cast("pathlib.Path", namespace.coverage_json)
    return check_coverage(coverage_json.resolve(), _repo_root())


if __name__ == "__main__":
    raise SystemExit(main())
