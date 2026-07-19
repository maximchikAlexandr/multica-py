#!/usr/bin/env python3
"""Run live integration tests with fail-closed input validation."""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import os
import pathlib
import subprocess
import sys
import time
from collections.abc import Iterator
from typing import cast

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.live_compatibility_report import (
    SuiteMode,
    build_compatibility_report,
    write_compatibility_report,
)
from scripts.resolve_multica_target import resolve_target
from tests.live.exceptions import LiveSetupError
from tests.live.settings import load_live_settings

DEFAULT_TARGET_FILE = REPO_ROOT / "contracts" / "multica-live-target.toml"

PROJECTS_UPDATE_TITLE = pathlib.Path("src/multica_py/resources/projects.py")
LABELS_RESOURCE = pathlib.Path("src/multica_py/resources/labels.py")
TRANSPORT = pathlib.Path("src/multica_py/_internal/transport.py")


@dataclasses.dataclass(frozen=True, slots=True)
class MutationCase:
    """One SC-002 mutation gate case."""

    name: str
    path: pathlib.Path
    original: str
    mutated: str
    pytest_target: str


MUTATION_CASES = (
    MutationCase(
        name="project-update-title-flag",
        path=PROJECTS_UPDATE_TITLE,
        original='            args.extend(["--title", request.name])',
        mutated='            args.extend(["--name", request.name])',
        pytest_target=(
            "tests/live/test_projects.py::test_p_omit_update_title_only_preserves_description"
        ),
    ),
    MutationCase(
        name="label-get-decoder",
        path=LABELS_RESOURCE,
        original='        return self._run_json_decode(("label", "get", label_id), Label)',
        mutated=(
            "        from multica_py.exceptions import OutputShapeError\n"
            '        raise OutputShapeError("mutation check forced decoder failure")'
        ),
        pytest_target="tests/live/test_labels.py::test_label_crud_round_trip",
    ),
    MutationCase(
        name="not-found-exit-mapping",
        path=TRANSPORT,
        original="            4: NotFoundError,",
        mutated="            4: CommandExecutionError,",
        pytest_target="tests/live/test_errors.py::test_missing_resource_raises_not_found_error",
    ),
)


def _validate_environment(*, resolve_cli: bool) -> None:
    try:
        load_live_settings(resolve_cli=resolve_cli, repo_root=REPO_ROOT)
    except LiveSetupError as exc:
        raise SystemExit(str(exc)) from exc
    if resolve_cli:
        os.environ["MULTICA_LIVE_RESOLVE_CLI"] = "1"


def _resolve_suite_mode(raw_mode: str | None) -> SuiteMode:
    candidate = raw_mode or os.environ.get("MULTICA_LIVE_MODE") or "smoke"
    if candidate not in {"smoke", "extended"}:
        msg = "suite mode must be smoke or extended"
        raise SystemExit(msg)
    if candidate == "extended":
        return "extended"
    return "smoke"


def _pytest_marker(mode: SuiteMode) -> str:
    if mode == "extended":
        return "live_smoke or live_extended"
    return "live_smoke"


def _run_pytest(pytest_args: list[str]) -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", *pytest_args],
        cwd=REPO_ROOT,
        check=False,
    )
    return int(completed.returncode)


def _assert_clean_worktree() -> None:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.stdout.strip():
        raise SystemExit("mutation check requires a clean git worktree")


@contextlib.contextmanager
def _patched_source(path: pathlib.Path, original: str, mutated: str) -> Iterator[None]:
    _assert_clean_worktree()
    full_path = REPO_ROOT / path
    content = full_path.read_text(encoding="utf-8")
    if original not in content:
        msg = f"mutation anchor not found in {path}"
        raise SystemExit(msg)
    original_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    full_path.write_text(content.replace(original, mutated, 1), encoding="utf-8")
    try:
        yield
    finally:
        subprocess.run(["git", "checkout", "--", str(path)], cwd=REPO_ROOT, check=True)
        restored = full_path.read_text(encoding="utf-8")
        if hashlib.sha256(restored.encode("utf-8")).hexdigest() != original_hash:
            raise SystemExit(f"failed to restore original content for {path}")


def _write_compatibility_report(
    *,
    suite_mode: SuiteMode,
    marker: str,
    exit_code: int,
    report_path: pathlib.Path | None,
    observed_upstream_ref: str | None,
) -> None:
    if report_path is None and suite_mode != "extended":
        return
    target_file = pathlib.Path(os.environ.get("MULTICA_LIVE_TARGET_FILE", str(DEFAULT_TARGET_FILE)))
    cli_path = (
        pathlib.Path(os.environ["MULTICA_LIVE_CLI"]) if os.environ.get("MULTICA_LIVE_CLI") else None
    )
    resolved = resolve_target(target_file.resolve(), cli_path)
    report = build_compatibility_report(
        resolved=resolved,
        suite_mode=suite_mode,
        pytest_marker=marker,
        pytest_exit_code=exit_code,
        observed_upstream_ref=observed_upstream_ref,
    )
    destination = (
        report_path
        or pathlib.Path(
            os.environ.get(
                "MULTICA_LIVE_ARTIFACT_DIR",
                REPO_ROOT / "tests" / "live" / ".artifacts",
            )
        )
        / "compatibility-report.json"
    )
    write_compatibility_report(destination, report)


def run_mutation_check(*, resolve_cli: bool) -> int:
    """Run SC-002 mutation gate: each mutation must break its target live test."""
    _validate_environment(resolve_cli=resolve_cli)
    failures: list[str] = []
    for case in MUTATION_CASES:
        with _patched_source(case.path, case.original, case.mutated):
            exit_code = _run_pytest(["-m", "live_smoke", case.pytest_target, "-q"])
        if exit_code == 0:
            failures.append(f"{case.name}: target test still passed with mutation applied")
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 1
    print("mutation check passed: all targeted live tests failed under mutation")
    return 0


def run_repeat(*, resolve_cli: bool, runs: int) -> int:
    """Run sequential live smoke runs and summarize flaky/runtime results."""
    _validate_environment(resolve_cli=resolve_cli)
    durations: list[float] = []
    failed_runs: list[int] = []
    for index in range(1, runs + 1):
        started = time.monotonic()
        exit_code = _run_pytest(["-m", "live_smoke", "tests/live", "-q"])
        elapsed = time.monotonic() - started
        durations.append(elapsed)
        status = "pass" if exit_code == 0 else "fail"
        print(f"run {index}/{runs}: {status} in {elapsed:.1f}s")
        if exit_code != 0:
            failed_runs.append(index)
    print(f"repeat summary: {runs - len(failed_runs)}/{runs} passed")
    if durations:
        print(
            "runtime seconds: "
            f"min={min(durations):.1f} "
            f"max={max(durations):.1f} "
            f"avg={sum(durations) / len(durations):.1f}"
        )
    if failed_runs:
        print(f"flaky or failed runs: {failed_runs}", file=sys.stderr)
        return 1
    return 0


def run_smoke(args: argparse.Namespace) -> int:
    """Validate inputs and invoke pytest for the live suite."""
    _validate_environment(resolve_cli=cast("bool", args.resolve_cli))
    suite_mode = _resolve_suite_mode(cast("str | None", args.mode))
    marker = _pytest_marker(suite_mode)
    forwarded_args = cast("list[str]", args.pytest_args)
    pytest_args = ["-m", marker, "tests/live", *forwarded_args]
    if forwarded_args and forwarded_args[0] == "--":
        pytest_args = ["-m", marker, "tests/live", *forwarded_args[1:]]
    exit_code = _run_pytest(pytest_args)
    _write_compatibility_report(
        suite_mode=suite_mode,
        marker=marker,
        exit_code=exit_code,
        report_path=cast("pathlib.Path | None", args.compatibility_report),
        observed_upstream_ref=cast("str | None", args.observed_upstream_ref),
    )
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    """Build the live test runner argument parser."""
    parser = argparse.ArgumentParser(
        description="Run multica-py live integration tests with validated inputs.",
    )
    parser.add_argument(
        "--resolve-cli",
        action="store_true",
        help="Resolve MULTICA_LIVE_CLI from the pinned target manifest.",
    )
    parser.add_argument(
        "--mode",
        choices=("smoke", "extended"),
        help="Live suite profile; defaults to MULTICA_LIVE_MODE or smoke.",
    )
    parser.add_argument(
        "--compatibility-report",
        type=pathlib.Path,
        help="Write a pinned-vs-upstream compatibility report to this JSON path.",
    )
    parser.add_argument(
        "--observed-upstream-ref",
        help="Upstream ref observed for this run when probing non-pinned code.",
    )
    parser.add_argument(
        "--mutation-check",
        action="store_true",
        help="Run SC-002 mutation gate against targeted live smoke tests.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        metavar="N",
        help="Run live smoke N times sequentially and summarize flaky/runtime results.",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments forwarded to pytest.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch live runner modes."""
    args = build_parser().parse_args(argv)
    if cast("bool", args.mutation_check):
        return run_mutation_check(resolve_cli=cast("bool", args.resolve_cli))
    repeat = cast("int | None", args.repeat)
    if repeat is not None:
        return run_repeat(resolve_cli=cast("bool", args.resolve_cli), runs=repeat)
    return run_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
