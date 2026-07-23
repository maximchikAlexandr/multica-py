#!/usr/bin/env python3
"""Capture the immutable pre-refactor offline test quality baseline (schema 2)."""

from __future__ import annotations

import argparse
import hashlib
import json
import operator
import pathlib
import re
import tomllib
import xml.etree.ElementTree as ET
from typing import cast

from scripts._loc_metrics import (
    glob_logical_lines as _glob_logical_lines,
)
from scripts._loc_metrics import (
    live_support_loc as _live_support_loc,
)
from scripts._loc_metrics import (
    max_test_support_file as _max_test_support_file,
)
from scripts.check_coverage import _load_coverage_config, _zone_percentages
from scripts.check_test_baseline import _count_package_install_paths

SHA_PATTERN: re.Pattern[str] = re.compile(r"^[0-9a-f]{40}$")


def _parse_junit(junit_path: pathlib.Path) -> float:
    root = ET.parse(junit_path).getroot()
    duration = 0.0
    for suite in root.iter("testsuite"):
        suite_time = suite.get("time")
        if suite_time is not None:
            duration += float(suite_time)
    return duration


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
        "config_sha256": _config_fingerprint(
            repo_root,
            [
                "tool.coverage.run",
                "tool.coverage.report",
                "tool.coverage.regexs",
                "tool.coverage.thresholds",
            ],
        ),
    }


def _config_fingerprint(repo_root: pathlib.Path, toml_sections: list[str]) -> str:
    pyproject_path = repo_root / "pyproject.toml"
    parsed: object = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise SystemExit("pyproject.toml root must be a table")
    data: dict[str, object] = {}
    for section_path in toml_sections:
        parts = section_path.split(".")
        current: object = parsed
        found = True
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        if found:
            data[section_path] = current
    canonical = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_mutation_results(path: pathlib.Path) -> dict[str, int | float]:
    text = path.read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    import contextlib

    for line in text.splitlines():
        stripped = line.strip()
        for key in ("killed", "survived", "timeout", "suspicious", "no_tests", "skipped"):
            prefix = key + "="
            if stripped.startswith(prefix):
                with contextlib.suppress(ValueError):
                    counts[key] = int(stripped[len(prefix) :])
    result: dict[str, int | float] = {}
    for key in ("killed", "survived", "timeout", "suspicious", "no_tests", "skipped"):
        result[key] = counts.get(key, 0)
    killed = counts.get("killed", 0)
    survived = counts.get("survived", 0)
    total = killed + survived
    result["score_percent"] = round((killed / total * 100) if total > 0 else 0.0, 2)
    return result


def _requirements_sha256(manifest: dict[str, object]) -> str:
    operations = manifest.get("operations")
    if not isinstance(operations, dict):
        raise SystemExit("behavior manifest missing operations dict")
    invariants = manifest.get("invariants")
    if not isinstance(invariants, dict):
        raise SystemExit("behavior manifest missing invariants dict")
    operation_pairs: list[tuple[str, list[str]]] = []
    for op_id, dims in operations.items():
        if not isinstance(dims, list):
            raise SystemExit(f"invalid dimensions for operation {op_id!r}")
        str_dims: list[str] = sorted(str(d) for d in dims)
        operation_pairs.append((op_id, str_dims))
    operation_pairs.sort(key=operator.itemgetter(0))
    invariant_keys: list[str] = sorted(invariants.keys())
    payload: dict[str, object] = {
        "operation_pairs": operation_pairs,
        "invariant_keys": invariant_keys,
    }
    canonical = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _build_baseline(
    git_sha: str,
    source_snapshot: str,
    coverage_path: pathlib.Path | None,
    junit_path: pathlib.Path | None,
    mutation_path: pathlib.Path | None,
    behavior_path: pathlib.Path | None,
    repo_root: pathlib.Path,
) -> dict[str, object]:
    if SHA_PATTERN.fullmatch(git_sha) is None:
        raise SystemExit("--git-sha must be 40 lowercase hex characters")
    if SHA_PATTERN.fullmatch(source_snapshot) is None:
        raise SystemExit("--source-snapshot must be 40 lowercase hex characters")
    payload: dict[str, object] = {
        "schema": 2,
        "git_sha": git_sha,
        "source_snapshot": source_snapshot,
    }
    if coverage_path is not None:
        payload["coverage"] = _coverage_metrics(coverage_path, repo_root)
    else:
        payload["coverage"] = {
            "statement_percent": 0.0,
            "branch_percent": 0.0,
            "zones": {},
            "config_sha256": _config_fingerprint(
                repo_root,
                [
                    "tool.coverage.run",
                    "tool.coverage.report",
                    "tool.coverage.regexs",
                    "tool.coverage.thresholds",
                ],
            ),
        }
    if mutation_path is not None:
        mutation_data = _parse_mutation_results(mutation_path)
        assert isinstance(mutation_data, dict)
        mutation_data["config_sha256"] = cast(
            "int | float", _config_fingerprint(repo_root, ["tool.mutmut"])
        )
        payload["mutation"] = mutation_data
    else:
        payload["mutation"] = {
            "killed": 0,
            "survived": 0,
            "timeout": 0,
            "suspicious": 0,
            "no_tests": 0,
            "skipped": 0,
            "score_percent": 0.0,
            "config_sha256": _config_fingerprint(repo_root, ["tool.mutmut"]),
        }
    if behavior_path is not None and behavior_path.is_file():
        behavior_parsed: object = json.loads(behavior_path.read_text(encoding="utf-8"))
        if not isinstance(behavior_parsed, dict):
            raise SystemExit("behavior manifest root must be an object")
        behavior = cast("dict[str, object]", behavior_parsed)
        operations = behavior.get("operations")
        invariants_obj = behavior.get("invariants")
        operation_pairs = len(operations) if isinstance(operations, dict) else 0
        invariants_count = len(invariants_obj) if isinstance(invariants_obj, dict) else 0
        payload["behavior"] = {
            "requirements_sha256": _requirements_sha256(behavior),
            "operation_pairs": operation_pairs,
            "invariants": invariants_count,
        }
    else:
        behavior_obj: dict[str, object] = {"operations": {}, "invariants": {}}
        payload["behavior"] = {
            "requirements_sha256": _requirements_sha256(behavior_obj),
            "operation_pairs": 0,
            "invariants": 0,
        }
    payload["loc"] = {
        "tests_python": _glob_logical_lines(repo_root / "tests", "**/*.py"),
        "live_support_python": _live_support_loc(repo_root),
        "scripts_python": _glob_logical_lines(repo_root / "scripts", "*.py"),
        "max_test_support_file": _max_test_support_file(repo_root),
    }
    offline_duration = 0.0
    offline_collected: dict[str, int] = {}
    if junit_path is not None:
        offline_duration = _parse_junit(junit_path)
    payload["offline"] = {
        "duration_seconds": round(offline_duration, 3),
        "collected": offline_collected,
    }
    payload["package_install_paths"] = _count_package_install_paths(repo_root)
    return payload


def _serialize_baseline(payload: dict[str, object]) -> bytes:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    return text.encode("utf-8")


def capture_baseline(
    git_sha: str,
    source_snapshot: str,
    coverage_path: pathlib.Path | None,
    junit_path: pathlib.Path | None,
    mutation_path: pathlib.Path | None,
    behavior_path: pathlib.Path | None,
    output_path: pathlib.Path,
    repo_root: pathlib.Path,
) -> int:
    payload = _build_baseline(
        git_sha, source_snapshot, coverage_path, junit_path, mutation_path, behavior_path, repo_root
    )
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
    parser = argparse.ArgumentParser(description="Capture immutable test baseline (schema 2).")
    parser.add_argument("--git-sha", required=True)
    parser.add_argument("--source-snapshot", required=True)
    parser.add_argument("--coverage-json", type=pathlib.Path)
    parser.add_argument("--junit-xml", type=pathlib.Path)
    parser.add_argument("--mutation-results", type=pathlib.Path)
    parser.add_argument("--behavior-manifest", type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    ns = parser.parse_args(argv)
    git_sha: str = ns.git_sha
    source_snapshot: str = ns.source_snapshot
    coverage_path_val: pathlib.Path | None = ns.coverage_json
    junit_path_val: pathlib.Path | None = ns.junit_xml
    mutation_path_val: pathlib.Path | None = ns.mutation_results
    behavior_path_val: pathlib.Path | None = ns.behavior_manifest
    output_val: pathlib.Path = ns.output
    return capture_baseline(
        git_sha,
        source_snapshot,
        coverage_path_val.resolve() if coverage_path_val else None,
        junit_path_val.resolve() if junit_path_val else None,
        mutation_path_val.resolve() if mutation_path_val else None,
        behavior_path_val.resolve() if behavior_path_val else None,
        output_val.resolve(),
        pathlib.Path(__file__).resolve().parents[1],
    )


if __name__ == "__main__":
    raise SystemExit(main())
