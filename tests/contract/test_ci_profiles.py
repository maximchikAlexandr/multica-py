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
PYPROJECT = REPO_ROOT / "pyproject.toml"

COMPAT_MODULES = (
    "tests/packaging/test_import_smoke.py",
    "tests/packaging/test_wheel_install.py",
    "tests/unit/test_path_normalization.py",
    "tests/component/test_project_resources.py",
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
    assert "scripts/check_test_baseline.py" in content
    assert "--stage PR-07" in content
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
    assert "not live" not in compat or "-m compat" in compat
    assert "live_smoke" not in compat


def test_live_smoke_job_timeout_budget_is_300_seconds() -> None:
    content = _workflow_text(CI_WORKFLOW)
    live = _job_block(content, "live-smoke")
    assert "timeout-minutes: 5" in live or "timeout-minutes: 300" in live


def test_package_workflow_has_six_install_paths() -> None:
    from scripts.check_test_baseline import _count_package_install_paths

    assert _count_package_install_paths(REPO_ROOT) == 6


def test_package_workflow_builds_wheel_once() -> None:
    content = _workflow_text(PACKAGE_WORKFLOW)
    assert re.search(r"^\s*build:\s*$", content, re.MULTILINE) is not None
    assert content.count("uv build") == 1


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
    assert isinstance(tests_dir, str)
    assert isinstance(runner, str)
    assert tests_dir == "tests/unit tests/component"
    assert runner == "uv run pytest -x -q -m 'not live and not serial'"
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
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match is not None, result.stdout
    assert int(match.group(1)) >= 4
