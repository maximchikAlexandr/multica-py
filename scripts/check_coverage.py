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


def _load_coverage_config(repo_root: pathlib.Path) -> tuple[dict[str, str], dict[str, float]]:
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
    if not isinstance(regexs_obj, dict) or not isinstance(thresholds_obj, dict):
        raise SystemExit(
            "pyproject.toml missing [tool.coverage.regexs] or [tool.coverage.thresholds]"
        )
    regexs = cast("dict[str, object]", regexs_obj)
    thresholds = cast("dict[str, object]", thresholds_obj)
    zone_regexs = {str(name): str(pattern) for name, pattern in regexs.items()}
    zone_thresholds: dict[str, float] = {}
    for name, value in thresholds.items():
        if isinstance(value, (int, float, str)):
            zone_thresholds[str(name)] = float(value)
        else:
            raise SystemExit(f"invalid threshold for {name!r}")
    return zone_regexs, zone_thresholds


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


def _zone_percentages(
    coverage_data: dict[str, object],
    zone_regexs: dict[str, str],
) -> dict[str, float]:
    files = coverage_data.get("files")
    if not isinstance(files, dict):
        raise SystemExit("coverage JSON missing files mapping")
    compiled = {zone: re.compile(pattern) for zone, pattern in zone_regexs.items()}
    covered_by_zone = dict.fromkeys(zone_regexs, 0)
    missing_by_zone = dict.fromkeys(zone_regexs, 0)
    for path, file_data in files.items():
        if not isinstance(file_data, dict):
            continue
        covered, missing = _statement_counts(file_data)
        for zone, pattern in compiled.items():
            if pattern.search(str(path)):
                covered_by_zone[zone] += covered
                missing_by_zone[zone] += missing
    percentages: dict[str, float] = {}
    for zone in zone_regexs:
        covered = covered_by_zone[zone]
        missing = missing_by_zone[zone]
        total = covered + missing
        percentages[zone] = 100.0 if total == 0 else (covered / total) * 100.0
    return percentages


def check_coverage(coverage_path: pathlib.Path, repo_root: pathlib.Path) -> int:
    """Validate zonal coverage and print sorted zone lines.

    Args:
        coverage_path: Path to coverage.py JSON report.
        repo_root: Repository root containing pyproject.toml.

    Returns:
        Exit code 0 on success, 1 when a zone is missing or below threshold.
    """
    zone_regexs, zone_thresholds = _load_coverage_config(repo_root)
    parsed: object = json.loads(coverage_path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise SystemExit("coverage JSON root must be an object")
    payload = cast("dict[str, object]", parsed)
    percentages = _zone_percentages(payload, zone_regexs)
    failed = False
    for zone in sorted(zone_regexs):
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
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate zonal statement coverage.")
    parser.add_argument("--coverage-json", required=True, type=pathlib.Path)
    namespace = parser.parse_args(argv)
    coverage_json = cast("pathlib.Path", namespace.coverage_json)
    return check_coverage(coverage_json.resolve(), _repo_root())


if __name__ == "__main__":
    raise SystemExit(main())
