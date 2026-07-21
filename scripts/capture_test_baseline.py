#!/usr/bin/env python3
"""Capture the immutable pre-refactor offline test quality baseline."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import cast

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_coverage import _load_coverage_config, _zone_percentages

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_DIFF_PATHS = frozenset(
    {
        "scripts/check_coverage.py",
        "scripts/capture_test_baseline.py",
        "scripts/check_test_baseline.py",
        "contracts/multica-live-target.toml",
        "tests/quality-baseline.json",
    }
)
EXCLUDED_NODE_IDS: tuple[str, ...] = ()
COLLECT_LAYERS = (
    ("unit", "tests/unit"),
    ("contract", "tests/contract"),
    ("component_source", "tests/component"),
    ("packaging", "tests/packaging"),
    ("live", "tests/live"),
)
BASELINE_SCHEMA = 1
PACKAGE_INSTALL_PATHS = 12


def _logical_lines(path: pathlib.Path) -> int:
    count = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        count += 1
    return count


def _glob_logical_lines(root: pathlib.Path, pattern: str) -> int:
    total = 0
    for path in sorted(root.glob(pattern)):
        if path.is_file():
            total += _logical_lines(path)
    return total


def _assert_allowed_diff(source_sha: str, repo_root: pathlib.Path) -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", source_sha],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise SystemExit(f"git diff failed: {result.stderr.strip()}")
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    disallowed = [path for path in changed if path not in ALLOWED_DIFF_PATHS]
    if disallowed:
        joined = ", ".join(sorted(disallowed))
        raise SystemExit(f"disallowed changes relative to {source_sha}: {joined}")


def _collect_layer_count(layer_path: str, repo_root: pathlib.Path) -> tuple[int, list[str]]:
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "-o",
            "addopts=",
            "--collect-only",
            "-q",
            layer_path,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 5):
        detail = (result.stderr or result.stdout).strip()
        raise SystemExit(f"pytest collection failed for {layer_path}: {detail}")
    node_ids = [
        line.strip()
        for line in result.stdout.splitlines()
        if "::" in line and not line.strip().startswith("no tests collected")
    ]
    summary_match = re.search(r"(\d+)\s+(?:tests|items)\s+collected", result.stdout)
    if summary_match is None:
        raise SystemExit(f"unable to parse collection count for {layer_path}")
    return int(summary_match.group(1)), node_ids


def _validate_excluded_nodes(node_ids: list[str]) -> None:
    counts = {node_id: node_ids.count(node_id) for node_id in EXCLUDED_NODE_IDS}
    problems = [
        f"{node_id} collected {counts[node_id]} times"
        for node_id in EXCLUDED_NODE_IDS
        if counts[node_id] != 1
    ]
    if problems:
        raise SystemExit("excluded node validation failed: " + "; ".join(problems))


def _mandatory_offline(collected: dict[str, int]) -> int:
    offline_total = (
        collected["unit"]
        + collected["contract"]
        + collected["component_source"]
        + collected["packaging"]
    )
    return offline_total - len(EXCLUDED_NODE_IDS)


def _parse_junit(junit_path: pathlib.Path) -> tuple[int, float]:
    root = ET.parse(junit_path).getroot()
    tests = 0
    duration = 0.0
    for suite in root.iter("testsuite"):
        suite_tests = suite.get("tests")
        suite_time = suite.get("time")
        if suite_tests is not None:
            tests += int(suite_tests)
        if suite_time is not None:
            duration += float(suite_time)
    if tests == 0:
        for _case in root.iter("testcase"):
            tests += 1
    return tests, duration


def _coverage_metrics(coverage_path: pathlib.Path, repo_root: pathlib.Path) -> dict[str, object]:
    parsed: object = json.loads(coverage_path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise SystemExit("coverage JSON root must be an object")
    payload = cast("dict[str, object]", parsed)
    totals = payload.get("totals")
    if not isinstance(totals, dict):
        raise SystemExit("coverage JSON missing totals")
    statement_percent = totals.get("percent_covered")
    if statement_percent is None:
        statement_percent = totals.get("percent_statements_covered")
    branch_percent = totals.get("percent_covered_branches")
    if branch_percent is None:
        branch_percent = totals.get("percent_branches_covered")
    if not isinstance(statement_percent, (int, float)):
        raise SystemExit("coverage JSON missing totals.percent_covered")
    if not isinstance(branch_percent, (int, float)):
        raise SystemExit("coverage JSON missing totals.percent_covered_branches")
    zone_regexs, _thresholds = _load_coverage_config(repo_root)
    zones = _zone_percentages(payload, zone_regexs)
    return {
        "statement_percent": float(statement_percent),
        "branch_percent": float(branch_percent),
        "zones": {zone: round(zones[zone], 2) for zone in sorted(zones)},
    }


def _build_baseline(
    source_sha: str,
    coverage_path: pathlib.Path,
    junit_path: pathlib.Path,
    repo_root: pathlib.Path,
) -> dict[str, object]:
    if SHA_PATTERN.fullmatch(source_sha) is None:
        raise SystemExit("--source-sha must be 40 lowercase hex characters")
    _assert_allowed_diff(source_sha, repo_root)
    collected: dict[str, int] = {}
    integration_nodes: list[str] = []
    for layer_key, layer_path in COLLECT_LAYERS:
        count, node_ids = _collect_layer_count(layer_path, repo_root)
        collected[layer_key] = count
        if layer_key == "component_source":
            integration_nodes = node_ids
    _validate_excluded_nodes(integration_nodes)
    offline_tests, offline_duration = _parse_junit(junit_path)
    return {
        "schema": BASELINE_SCHEMA,
        "git_sha": source_sha,
        "collected": collected,
        "mandatory_offline": _mandatory_offline(collected),
        "loc": {
            "tests_python": _glob_logical_lines(repo_root / "tests", "**/*.py"),
            "scripts_python": _glob_logical_lines(repo_root / "scripts", "*.py"),
            "resource_test_support": _glob_logical_lines(
                repo_root / "tests" / "component" / "resources",
                "**/*.py",
            ),
        },
        "offline": {
            "tests": offline_tests,
            "duration_seconds": round(offline_duration, 3),
        },
        "coverage": _coverage_metrics(coverage_path, repo_root),
        "package_install_paths": PACKAGE_INSTALL_PATHS,
    }


def _serialize_baseline(payload: dict[str, object]) -> bytes:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return text.encode("utf-8")


def capture_baseline(
    source_sha: str,
    coverage_path: pathlib.Path,
    junit_path: pathlib.Path,
    output_path: pathlib.Path,
    repo_root: pathlib.Path,
) -> int:
    """Generate or verify the baseline JSON file.

    Args:
        source_sha: Pre-change git commit SHA.
        coverage_path: Coverage JSON report path.
        junit_path: JUnit XML report path.
        output_path: Baseline JSON destination.
        repo_root: Repository root.

    Returns:
        Exit code 0 on success, 1 when an existing file would change.
    """
    payload = _build_baseline(source_sha, coverage_path, junit_path, repo_root)
    generated = _serialize_baseline(payload)
    if output_path.is_file():
        existing = output_path.read_bytes()
        if existing == generated:
            return 0
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(generated)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture immutable test baseline.")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--coverage-json", required=True, type=pathlib.Path)
    parser.add_argument("--junit-xml", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    namespace = parser.parse_args(argv)
    return capture_baseline(
        cast("str", namespace.source_sha),
        cast("pathlib.Path", namespace.coverage_json).resolve(),
        cast("pathlib.Path", namespace.junit_xml).resolve(),
        cast("pathlib.Path", namespace.output).resolve(),
        REPO_ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
