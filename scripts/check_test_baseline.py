#!/usr/bin/env python3
"""Validate or compare the committed test quality baseline."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from typing import cast

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.capture_test_baseline import EXCLUDED_NODE_IDS, _collect_layer_count, _logical_lines  # noqa: I001
from scripts.check_coverage import check_coverage

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
COMPARE_STAGES = frozenset({"PR-02", "PR-03", "PR-07", "final"})
STAGE_CHOICES: tuple[str, ...] = ("PR-02", "PR-03", "PR-07", "final")
BASELINE_REL_PATH = "tests/quality-baseline.json"


def _load_baseline(path: pathlib.Path) -> dict[str, object]:
    parsed: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise SystemExit("baseline root must be an object")
    return cast("dict[str, object]", parsed)


def _serialize_baseline(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _assert_schema(payload: dict[str, object]) -> None:
    required_top = (
        "schema",
        "git_sha",
        "collected",
        "mandatory_offline",
        "loc",
        "offline",
        "coverage",
        "package_install_paths",
    )
    for key in required_top:
        if key not in payload:
            raise SystemExit(f"baseline missing required key: {key}")
    git_sha = payload["git_sha"]
    if not isinstance(git_sha, str) or SHA_PATTERN.fullmatch(git_sha) is None:
        raise SystemExit("baseline git_sha must be 40 lowercase hex characters")
    collected = payload["collected"]
    if not isinstance(collected, dict):
        raise SystemExit("baseline collected must be an object")
    for layer in ("unit", "contract", "component_source", "packaging", "live"):
        value = collected.get(layer)
        if not isinstance(value, int) or value < 0:
            raise SystemExit(f"baseline collected.{layer} must be a non-negative integer")
    mandatory_offline = payload["mandatory_offline"]
    if not isinstance(mandatory_offline, int) or mandatory_offline < 0:
        raise SystemExit("baseline mandatory_offline must be a non-negative integer")
    loc = payload["loc"]
    if not isinstance(loc, dict):
        raise SystemExit("baseline loc must be an object")
    for key in ("tests_python", "scripts_python", "resource_test_support"):
        value = loc.get(key)
        if not isinstance(value, int) or value < 0:
            raise SystemExit(f"baseline loc.{key} must be a non-negative integer")
    offline = payload["offline"]
    if not isinstance(offline, dict):
        raise SystemExit("baseline offline must be an object")
    tests = offline.get("tests")
    duration = offline.get("duration_seconds")
    if not isinstance(tests, int) or tests < 0:
        raise SystemExit("baseline offline.tests must be a non-negative integer")
    if not isinstance(duration, (int, float)) or duration < 0:
        raise SystemExit("baseline offline.duration_seconds must be non-negative")
    coverage = payload["coverage"]
    if not isinstance(coverage, dict):
        raise SystemExit("baseline coverage must be an object")
    for key in ("statement_percent", "branch_percent"):
        value = coverage.get(key)
        if not isinstance(value, (int, float)) or value < 0:
            raise SystemExit(f"baseline coverage.{key} must be non-negative")
    zones = coverage.get("zones")
    if not isinstance(zones, dict):
        raise SystemExit("baseline coverage.zones must be an object")
    for zone, value in zones.items():
        if not isinstance(value, (int, float)) or value < 0:
            raise SystemExit(f"baseline coverage.zones.{zone} must be non-negative")
    package_paths = payload["package_install_paths"]
    if not isinstance(package_paths, int) or package_paths < 0:
        raise SystemExit("baseline package_install_paths must be a non-negative integer")


def _assert_ancestor(baseline_sha: str, repo_root: pathlib.Path) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", baseline_sha, "HEAD"],
        cwd=repo_root,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"baseline git_sha {baseline_sha} is not an ancestor of HEAD")


def _assert_baseline_bytes_unchanged(baseline_path: pathlib.Path, repo_root: pathlib.Path) -> None:
    result = subprocess.run(
        ["git", "diff", "--exit-code", "--", BASELINE_REL_PATH],
        cwd=repo_root,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("baseline file has uncommitted changes")
    if not baseline_path.is_file():
        raise SystemExit("baseline file is missing")
    committed = subprocess.run(
        ["git", "show", f"HEAD:{BASELINE_REL_PATH}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if committed.returncode != 0:
        return
    if committed.stdout != baseline_path.read_bytes():
        raise SystemExit("baseline file bytes differ from HEAD")


def _current_mandatory_offline(repo_root: pathlib.Path) -> int:
    layer_paths = ["tests/unit", "tests/contract", "tests/component", "tests/packaging"]
    total = sum(_collect_layer_count(layer_path, repo_root)[0] for layer_path in layer_paths)
    return total - len(EXCLUDED_NODE_IDS)


def _resource_support_loc(repo_root: pathlib.Path) -> int:
    component_resources = repo_root / "tests" / "component" / "resources"
    total = 0
    for path in sorted(component_resources.glob("**/*.py")):
        if path.is_file():
            total += _logical_lines(path)
    return total


def _regex_count(pattern: str, content: str) -> int:
    matches = cast("list[str]", re.compile(pattern).findall(content))
    return len(matches)


def _count_package_install_paths(repo_root: pathlib.Path) -> int:
    workflow = repo_root / ".github" / "workflows" / "package-test.yml"
    content = workflow.read_text(encoding="utf-8")
    os_values = cast(
        "list[str]",
        re.compile(r"^\s*-\s*(ubuntu-latest|macos-latest)\s*$", re.MULTILINE).findall(content),
    )
    py_values = cast(
        "list[str]",
        re.compile(r'^\s*-\s*"(\d+\.\d+)"\s*$', re.MULTILINE).findall(content),
    )
    matrix_size = max(1, len(os_values) * len(py_values))
    uv_conditional = bool(
        re.search(r"name:\s*uv pip install\b[\s\S]*?\n\s*if:", content)
        or re.search(r"name:\s*uv add\b[\s\S]*?\n\s*if:", content)
    )
    pip_steps = _regex_count(r"name:\s*pip install\b", content)
    uv_pip_steps = _regex_count(r"name:\s*uv pip install\b", content)
    uv_add_steps = _regex_count(r"name:\s*uv add\b", content)
    if uv_conditional:
        return matrix_size * pip_steps + uv_pip_steps + uv_add_steps
    install_steps = _regex_count(r"name:\s*(?:pip install|uv pip install|uv add)\b", content)
    return matrix_size * install_steps


def self_check(baseline_path: pathlib.Path, repo_root: pathlib.Path) -> int:
    """Validate baseline schema and repository ancestry.

    Args:
        baseline_path: Path to committed baseline JSON.
        repo_root: Repository root.

    Returns:
        Exit code 0 on success, 1 on validation failure.
    """
    payload = _load_baseline(baseline_path)
    _assert_schema(payload)
    git_sha = str(payload["git_sha"])
    _assert_ancestor(git_sha, repo_root)
    serialized = _serialize_baseline(payload)
    if serialized != baseline_path.read_bytes():
        raise SystemExit("baseline file is not deterministically serialized")
    print(f"baseline self-check passed for {git_sha}")
    return 0


def compare_baseline(
    baseline_path: pathlib.Path,
    stage: str,
    repo_root: pathlib.Path,
    coverage_json: pathlib.Path | None = None,
) -> int:
    """Compare current repository state against the immutable baseline.

    Args:
        baseline_path: Path to committed baseline JSON.
        stage: Comparison stage identifier.
        repo_root: Repository root.
        coverage_json: Optional coverage JSON for final-stage zonal checks.

    Returns:
        Exit code 0 on success, 1 on comparison failure.
    """
    payload = _load_baseline(baseline_path)
    _assert_baseline_bytes_unchanged(baseline_path, repo_root)
    mandatory_raw = payload["mandatory_offline"]
    if not isinstance(mandatory_raw, int):
        raise SystemExit("baseline mandatory_offline must be an integer")
    baseline_mandatory = mandatory_raw
    current_mandatory = _current_mandatory_offline(repo_root)
    if current_mandatory < baseline_mandatory:
        raise SystemExit(
            f"mandatory offline count regressed: {current_mandatory} < {baseline_mandatory}"
        )
    print(f"mandatory_offline: {current_mandatory} >= {baseline_mandatory}")
    if stage in {"PR-03", "PR-07", "final"}:
        loc = payload.get("loc")
        if not isinstance(loc, dict):
            raise SystemExit("baseline loc must be an object")
        resource_loc = loc.get("resource_test_support")
        if not isinstance(resource_loc, int):
            raise SystemExit("baseline loc.resource_test_support must be an integer")
        baseline_loc = resource_loc
        current_loc = _resource_support_loc(repo_root)
        limit = baseline_loc * 0.75
        if current_loc > limit:
            raise SystemExit(
                f"resource test/support LOC {current_loc} exceeds 75% limit {limit:.1f}"
            )
        print(f"resource_test_support LOC: {current_loc} <= {limit:.1f}")
    if stage in {"PR-07", "final"}:
        current_paths = _count_package_install_paths(repo_root)
        if current_paths != 6:
            raise SystemExit(f"package install paths must be 6, got {current_paths}")
        print("package_install_paths: 6")
    if stage == "final":
        coverage_path = coverage_json or (repo_root / "coverage.json")
        if not coverage_path.is_file():
            raise SystemExit(f"coverage JSON not found: {coverage_path}")
        if check_coverage(coverage_path.resolve(), repo_root) != 0:
            raise SystemExit("zonal coverage below configured thresholds")
    print(f"baseline compare passed for stage {stage}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or compare test baseline.")
    parser.add_argument("--baseline", required=True, type=pathlib.Path)
    parser.add_argument("--mode", required=True, choices=("self-check", "compare"))
    parser.add_argument("--stage", choices=STAGE_CHOICES)
    parser.add_argument("--coverage-json", type=pathlib.Path)
    namespace = parser.parse_args(argv)
    baseline_path = cast("pathlib.Path", namespace.baseline)
    mode = cast("str", namespace.mode)
    stage = cast("str | None", namespace.stage)
    coverage_json = cast("pathlib.Path | None", namespace.coverage_json)
    if mode == "self-check":
        return self_check(baseline_path.resolve(), REPO_ROOT)
    if stage is None:
        return 2
    if stage not in COMPARE_STAGES:
        return 2
    return compare_baseline(
        baseline_path.resolve(),
        stage,
        REPO_ROOT,
        coverage_json=coverage_json.resolve() if coverage_json is not None else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
