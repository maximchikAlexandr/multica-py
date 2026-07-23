from __future__ import annotations

import pathlib
import re
import tomllib
from typing import cast

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PACKAGE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "package-test.yml"
MUTATION_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "mutation.yml"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
PYPROJECT = REPO_ROOT / "pyproject.toml"

COMPAT_MODULES = (
    "tests/packaging/test_artifacts.py",
    "tests/unit/test_path_normalization.py",
)


def _workflow_text(path: pathlib.Path) -> str:
    assert path.is_file(), f"missing workflow: {path}"
    return path.read_text(encoding="utf-8")


def _job_block(content: str, job_name: str) -> str:
    lines = content.splitlines()
    start_idx = next((index for index, line in enumerate(lines) if line == f"  {job_name}:"), -1)
    assert start_idx >= 0, f"ci.yml missing {job_name} job"
    end_idx = len(lines)
    for index in range(start_idx + 1, len(lines)):
        if re.match(r"^  [a-z].*:$", lines[index]):
            end_idx = index
            break
    return "\n".join(lines[start_idx:end_idx])


def _quality_job(content: str) -> str:
    return _job_block(content, "quality")


def _compatibility_job(content: str) -> str:
    return _job_block(content, "compatibility")


def test_quality_job_uses_ubuntu_python_312_and_xdist() -> None:
    content = _workflow_text(CI_WORKFLOW)
    quality = _quality_job(content)
    assert "runs-on: ubuntu-latest" in quality
    assert 'python-version: "3.12"' in quality
    assert '-m "not live and not serial"' in quality
    assert "-n auto" in quality
    assert "--dist loadscope" in quality


def test_quality_job_runs_serial_coverage_append_pass() -> None:
    quality = _quality_job(_workflow_text(CI_WORKFLOW))
    assert '-m "serial and not live"' in quality
    assert "--cov-append" in quality
    assert "--cov-report=xml" in quality
    assert "--cov-report=json" in quality


def test_quality_job_wires_coverage_and_baseline_checks() -> None:
    content = _workflow_text(CI_WORKFLOW)
    assert "scripts/check_coverage.py" in content
    assert "scripts.check_test_baseline" in content
    assert "for s in pr1 pr2 pr3 pr4 final" in content
    assert "_manifest_coverage" not in content


def test_quality_job_excludes_live_from_offline_passes() -> None:
    quality = _quality_job(_workflow_text(CI_WORKFLOW))
    assert "not live" in quality
    assert "tests/live" not in quality


def test_compatibility_matrix_has_four_cells() -> None:
    compat = _compatibility_job(_workflow_text(CI_WORKFLOW))
    os_values = cast("list[str]", re.findall(r"ubuntu-latest|macos-latest", compat))
    py_values = cast("list[str]", re.findall(r'"3\.12"|"3\.13"|3\.12|3\.13', compat))
    assert "ubuntu-latest" in os_values
    assert "macos-latest" in os_values
    assert "3.12" in py_values or '"3.12"' in py_values
    assert "3.13" in py_values or '"3.13"' in py_values


def test_compatibility_job_runs_compat_marker_only() -> None:
    compat = _compatibility_job(_workflow_text(CI_WORKFLOW))
    assert "-m compat" in compat
    assert "not live" not in compat
    assert "live_smoke" not in compat


def test_live_smoke_job_timeout_budget_is_300_seconds() -> None:
    content = _workflow_text(CI_WORKFLOW)
    live = _job_block(content, "live-smoke")
    assert "timeout-minutes: 5" in live or "timeout-minutes: 300" in live


def test_live_smoke_sc009_sub_budgets_match_agent_sandbox_suite() -> None:
    """Suite test-phase budget must fit agent sandbox plus remaining smoke cases."""
    live = _job_block(_workflow_text(CI_WORKFLOW), "live-smoke")
    assert "budget 240" in live
    assert "float(test_phase) > 240" in live
    assert "float(env_ready) > 180" in live
    assert "TOTAL" in live and "300" in live
    assert "float(test_phase) > 120" not in live


def test_package_workflow_has_six_install_paths() -> None:
    from scripts.check_test_baseline import _count_package_install_paths

    assert _count_package_install_paths(REPO_ROOT) == 6


def test_package_workflow_builds_wheel_once() -> None:
    """Guard-node for invariant packaging.single-build.

    Проверяет, что workflow package-test.yml содержит ровно один `uv build` step
    и что ci.yml не имеет ни одного `uv build` step (только package-test.yml
    является build gate).
    """
    package_content = _workflow_text(PACKAGE_WORKFLOW)
    ci_content = _workflow_text(CI_WORKFLOW)
    package_build_lines = [
        line
        for line in package_content.splitlines()
        if "uv build" in line and not line.strip().startswith("#")
    ]
    assert len(package_build_lines) == 1, (
        f"expected exactly 1 'uv build' invocation in package-test.yml, "
        f"found {len(package_build_lines)}"
    )
    ci_build_lines = [
        line
        for line in ci_content.splitlines()
        if "uv build" in line and not line.strip().startswith("#")
    ]
    assert not ci_build_lines, (
        f"ci.yml must not contain 'uv build' (package-test.yml is the sole build gate); "
        f"found {ci_build_lines}"
    )


def test_packaging_tests_have_no_skip() -> None:
    """No-skip invariant: tests under tests/packaging/ must not skip or xfail."""
    import ast

    packaging_dir = REPO_ROOT / "tests" / "packaging"
    for path in sorted(packaging_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for dec in node.decorator_list:
                    qualname = ast.unparse(dec)
                    if "skip" in qualname or "xfail" in qualname:
                        raise AssertionError(
                            f"{path.relative_to(REPO_ROOT)}:{node.lineno} "
                            f"forbids skip/xfail decorators (no-skip invariant): {qualname}"
                        )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Call) and ast.unparse(stmt.func) in {
                        "pytest.skip",
                        "pytest.xfail",
                    }:
                        raise AssertionError(
                            f"{path.relative_to(REPO_ROOT)}:{stmt.lineno} "
                            "forbids pytest.skip / pytest.xfail calls (no-skip invariant)"
                        )


def test_mutation_workflow_is_non_required_and_scheduled() -> None:
    content = _workflow_text(MUTATION_WORKFLOW)
    assert "workflow_dispatch" in content
    assert re.search(r'cron:\s*"0 3 \* \* 2"', content) is not None
    assert "continue-on-error: true" in content or "if: false" not in content


def test_mutation_workflow_uses_mutation_group_and_uploads_results() -> None:
    content = _workflow_text(MUTATION_WORKFLOW)
    assert "--group mutation" in content or "group mutation" in content
    assert "mutmut results" in content
    assert "upload-artifact" in content


def test_mutmut_config_matches_mutation_scope_contract() -> None:
    data = cast("dict[str, object]", tomllib.loads(PYPROJECT.read_text(encoding="utf-8")))
    tool = data.get("tool")
    assert isinstance(tool, dict)
    mutmut = tool.get("mutmut")
    assert isinstance(mutmut, dict)
    tests_dir = mutmut.get("tests_dir")
    runner = mutmut.get("runner")
    assert isinstance(tests_dir, (str, list))
    assert isinstance(runner, str)
    assert runner == "uv run pytest -x -q -m 'not live and not serial'"
    if isinstance(tests_dir, list):
        assert "tests/unit" in tests_dir
        assert "tests/component" in tests_dir
    else:
        assert tests_dir == "tests/unit tests/component"
    paths = mutmut.get("paths_to_mutate")
    assert isinstance(paths, list)
    path_items: list[str] = [str(item) for item in paths]
    assert "src/multica_py/config.py" in path_items
    joined = "\n".join(path_items)
    assert "models" not in joined
    assert "tests/" not in joined
    assert "scripts/" not in joined


@pytest.mark.parametrize("module_path", COMPAT_MODULES)
def test_compat_contract_modules_exist(module_path: str) -> None:
    assert (REPO_ROOT / module_path).is_file()


def test_compat_marker_collects_at_least_four_items() -> None:
    import subprocess

    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q", "-m", "compat"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    selected_match = re.search(r"(\d+)/(\d+) tests collected", result.stdout)
    if selected_match is not None:
        collected = int(selected_match.group(1))
    else:
        fallback = re.search(r"(\d+) tests? collected", result.stdout)
        assert fallback is not None, result.stdout
        collected = int(fallback.group(1))
    assert collected >= 4


_PINNED_ACTIONS: dict[str, str] = {
    "actions/checkout": "b4ffde65f46336ab88eb53be808477a3936bae11",
    "astral-sh/setup-uv": "ecd24dd710f2fb0dca1693a67af11fc4a5c5ec84",
}

_SHA_RE = re.compile(r"@[0-9a-f]{40}")
_TAG_RE = re.compile(r"@v\d+(\.\d+)?$")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


def _iter_workflow_uses() -> list[tuple[pathlib.Path, str, str]]:
    found: list[tuple[pathlib.Path, str, str]] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "uses:" not in line:
                continue
            _, _, value = line.partition("uses:")
            value = value.strip()
            if not value:
                continue
            found.append((path, line, value))
    return found


def test_pr_workflow_runs_only_offline_check() -> None:
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert "pull_request" in text
    assert "push" in text
    run_lines = [line for line in text.splitlines() if line.strip().startswith("run:")]
    run_block = "\n".join(run_lines)
    for forbidden in ("observe", "prepare-upgrade", "promote", "collect "):
        assert forbidden not in run_block, f"PR workflow must not run: {forbidden!r}"


def test_observer_workflow_is_separate() -> None:
    text = (WORKFLOWS / "upstream-contract-observer.yml").read_text(encoding="utf-8")
    assert "schedule" in text or "workflow_dispatch" in text
    assert "observe" in text


def test_offline_check_in_ci_workflow() -> None:
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert "multica_py._internal.upstream_contract.cli check" in text


def test_actions_pinned_to_sha_or_tag_with_explanation() -> None:
    for path, line, value in _iter_workflow_uses():
        if "@" not in value:
            continue
        action, _, ref = value.partition("@")
        if action not in _PINNED_ACTIONS:
            continue
        expected_sha = _PINNED_ACTIONS[action]
        if _SHA_RE.match(f"@{ref}"):
            assert ref == expected_sha, (
                f"{path.name}: {action} pinned to {ref!r} but whitelist expects {expected_sha!r}"
            )
            continue
        if _TAG_RE.match(f"@{ref}"):
            if path.name == "upstream-contract-observer.yml":
                raise AssertionError(
                    f"{path.name}: observer workflow must pin actions by full SHA, got {ref!r}"
                )
            if "major-version-tag-allowed" in path.read_text(encoding="utf-8"):
                continue
            raise AssertionError(
                f"{path.name}: major-version tag {ref!r} used without repository policy comment"
            )
        raise AssertionError(f"{path.name}: unexpected action ref {ref!r}")


def test_pinned_action_shas_are_well_formed() -> None:
    for action, sha in _PINNED_ACTIONS.items():
        assert _HEX40_RE.match(sha), f"{action}: SHA {sha!r} is not 40 lowercase hex chars"
        assert set(sha) != {"0"}, f"{action}: SHA {sha!r} is all zeros"
        assert len(set(sha)) >= 8, f"{action}: SHA {sha!r} looks like a placeholder"


def test_workflow_files_exist() -> None:
    expected = {
        "ci.yml",
        "upstream-contract-observer.yml",
    }
    actual = {path.name for path in WORKFLOWS.glob("*.yml")}
    assert expected.issubset(actual)
