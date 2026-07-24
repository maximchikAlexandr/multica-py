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
import tempfile
import time
from collections.abc import Iterator
from typing import cast

import msgspec

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.live_compatibility_report import (
    SuiteMode,
    build_compatibility_report,
    write_compatibility_report,
)
from scripts.resolve_multica_target import resolve_target
from tools.live_support.environment import LiveSetupError, load_live_settings
from tools.live_support.outcomes import MutationOutcome, OutcomeCategory, TargetFingerprint

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
    pytest_target: str = ""
    inline_test: str = ""


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
        original="    4: NotFoundError,",
        mutated="    4: CommandExecutionError,",
        pytest_target="tests/live/test_errors.py::test_error_mapping[missing-resource]",
    ),
)

_INLINE_UPDATE_TITLE_TEST = """\
from __future__ import annotations
import datetime, json
from unittest.mock import MagicMock as _M
from multica_py._internal.specs import RawCommandResult as _R
from multica_py._internal.transport import CliTransport as _T
from multica_py.resources.projects import ProjectResource as _P
from multica_py.config import ClientConfig as _C
from multica_py.models.projects import ProjectUpdateRequest as _U
_WIRE = json.dumps({"id":"pr_1","title":"test-title","status":"planned"}).encode()
def test_update_title():
    t = _M(spec=_T)
    t.run_bytes.return_value = _R(
        argv=(), exit_code=0, stdout=_WIRE, stderr=b"", duration=datetime.timedelta(),
    )
    r = _P(t, _C())
    r.update("pr_1", _U(name="test-title"))
    a = t.run_bytes.call_args[0][0]
    assert "--title" in a, f"--title not in argv: {a}"
"""

UNIT_MUTATION_CASES = (
    MutationCase(
        name="project-update-title-flag-unit",
        path=PROJECTS_UPDATE_TITLE,
        original='            args.extend(["--title", request.name])',
        mutated='            args.extend(["--name", request.name])',
        inline_test=_INLINE_UPDATE_TITLE_TEST,
    ),
    MutationCase(
        name="label-get-decoder-unit",
        path=LABELS_RESOURCE,
        original='        return self._run_json_decode(("label", "get", label_id), Label)',
        mutated=(
            "        from multica_py.exceptions import OutputShapeError\n"
            '        raise OutputShapeError("mutation check forced decoder failure")'
        ),
        pytest_target="tests/unit/resources/test_operations.py::test_operation_argv[labels.get]",
    ),
    MutationCase(
        name="not-found-exit-mapping-unit",
        path=TRANSPORT,
        original="    4: NotFoundError,",
        mutated="    4: CommandExecutionError,",
        pytest_target="tests/unit/test_transport.py::test_exit_code_maps_to_exception[exit-4-notfound]",
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


def _compute_source_sha256(path: pathlib.Path) -> str:
    content = path.read_text(encoding="utf-8")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@contextlib.contextmanager
def _mutated_context(path: pathlib.Path, original: str, mutated: str) -> Iterator[None]:
    full_path = path if path.is_absolute() else REPO_ROOT / path
    content = full_path.read_text(encoding="utf-8")
    if original not in content:
        msg = f"mutation anchor not found in {path}"
        raise SystemExit(msg)
    original_content = content
    original_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    full_path.write_text(content.replace(original, mutated, 1), encoding="utf-8")
    try:
        yield
    finally:
        full_path.write_text(original_content, encoding="utf-8")
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
    outcome_category: OutcomeCategory | None = None,
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
    if outcome_category is not None:
        report["outcome_category"] = outcome_category.value
    write_compatibility_report(destination, report)


def run_mutation_check(args: argparse.Namespace) -> int:
    """Run SC-002 mutation gate against unit (default) or live tests."""
    scope = cast("str", args.mutation_scope)
    if scope == "live":
        _validate_environment(resolve_cli=cast("bool", args.resolve_cli))
    cases = MUTATION_CASES if scope == "live" else UNIT_MUTATION_CASES
    mutation_results = cast("pathlib.Path | None", args.mutation_results)
    artifact_dir = REPO_ROOT / ".test-artifacts" / "mutation"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    outcomes: list[MutationOutcome] = []
    failures: list[str] = []
    marker: list[str] = ["-m", "live_smoke"] if scope == "live" else []
    for case in cases:
        control_xml = artifact_dir / f"{case.name}-control.xml"
        mutated_xml = artifact_dir / f"{case.name}-mutated.xml"
        if case.inline_test:
            with tempfile.TemporaryDirectory() as tmpdir:
                test_file = pathlib.Path(tmpdir) / "test_mutation.py"
                test_file.write_text(case.inline_test, encoding="utf-8")
                target = str(test_file)
                _run_pytest([*marker, target, "-q", "-x", "--junitxml", str(control_xml)])
                control_sha256 = _compute_source_sha256(REPO_ROOT / case.path)
                with _mutated_context(case.path, case.original, case.mutated):
                    exit_code = _run_pytest(
                        [*marker, target, "-q", "-x", "--junitxml", str(mutated_xml)]
                    )
                    mutated_sha256 = _compute_source_sha256(REPO_ROOT / case.path)
        else:
            _run_pytest([*marker, case.pytest_target, "-q", "-x", "--junitxml", str(control_xml)])
            control_sha256 = _compute_source_sha256(REPO_ROOT / case.path)
            with _mutated_context(case.path, case.original, case.mutated):
                exit_code = _run_pytest(
                    [*marker, case.pytest_target, "-q", "-x", "--junitxml", str(mutated_xml)]
                )
                mutated_sha256 = _compute_source_sha256(REPO_ROOT / case.path)
        killed = exit_code != 0
        outcomes.append(
            MutationOutcome(
                target=case.name,
                control_fingerprint=TargetFingerprint(
                    version="", tag="", commit="", sha256=control_sha256
                ),
                mutated_fingerprint=TargetFingerprint(
                    version="", tag="", commit="", sha256=mutated_sha256
                ),
                killed=killed,
                control_path=str(control_xml),
                mutated_path=str(mutated_xml),
            )
        )
        if not killed:
            failures.append(f"{case.name}: mutation survived (test passed with mutation)")
    if mutation_results is not None:
        mutation_results.parent.mkdir(parents=True, exist_ok=True)
        mutation_results.write_text(msgspec.json.encode(outcomes).decode("utf-8"), encoding="utf-8")
        print(f"mutation results written to {mutation_results}")
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 1
    killed_count = sum(1 for o in outcomes if o.killed)
    survivors = len(outcomes) - killed_count
    print(f"mutation check passed: {killed_count} killed, {survivors} survived, 0 invalid")
    return 0


def run_repeat(*, resolve_cli: bool, runs: int, pytest_args: list[str] | None = None) -> int:
    """Run sequential live smoke runs and summarize flaky/runtime results."""
    _validate_environment(resolve_cli=resolve_cli)
    durations: list[float] = []
    failed_runs: list[int] = []
    leftover_prefixes: set[str] = set()
    forwarded = pytest_args or []
    for index in range(1, runs + 1):
        run_id = os.urandom(16).hex()
        os.environ["MULTICA_LIVE_RUN_ID"] = run_id
        prefix = f"multica-py-live-{run_id}"
        started = time.monotonic()
        argv = ["-m", "live_smoke", "tests/live/test_agent_sandbox.py", *forwarded]
        if forwarded and forwarded[0] == "--":
            argv = ["-m", "live_smoke", "tests/live/test_agent_sandbox.py", *forwarded[1:]]
        exit_code = _run_pytest(argv)
        elapsed = time.monotonic() - started
        durations.append(elapsed)
        status = "pass" if exit_code == 0 else "fail"
        print(f"run {index}/{runs}: {status} in {elapsed:.1f}s (run_id={run_id})")
        if exit_code != 0:
            failed_runs.append(index)
        leftover_prefixes.update(_collect_leftover_prefixes(prefix))
    print(f"repeat summary: {runs - len(failed_runs)}/{runs} passed")
    if durations:
        print(
            "runtime seconds: "
            f"min={min(durations):.1f} "
            f"max={max(durations):.1f} "
            f"avg={sum(durations) / len(durations):.1f}"
        )
    if leftover_prefixes:
        print(f"managed leftovers: {sorted(leftover_prefixes)}", file=sys.stderr)
        return 1
    if failed_runs:
        print(f"flaky or failed runs: {failed_runs}", file=sys.stderr)
        return 1
    return 0


def _collect_leftover_prefixes(prefix: str) -> set[str]:
    leftovers: set[str] = set()
    ps = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={prefix}", "--format", "{{.Names}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    leftovers.update(line for line in ps.stdout.splitlines() if line.strip())
    volumes = subprocess.run(
        ["docker", "volume", "ls", "--filter", f"name={prefix}", "--format", "{{.Name}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    leftovers.update(line for line in volumes.stdout.splitlines() if line.strip())
    return leftovers


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
    category = OutcomeCategory.passed if exit_code == 0 else OutcomeCategory.failed
    _write_compatibility_report(
        suite_mode=suite_mode,
        marker=marker,
        exit_code=exit_code,
        report_path=cast("pathlib.Path | None", args.compatibility_report),
        observed_upstream_ref=cast("str | None", args.observed_upstream_ref),
        outcome_category=category,
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
        help="Run SC-002 mutation gate against targeted unit or live tests.",
    )
    parser.add_argument(
        "--mutation-results",
        type=pathlib.Path,
        help="Write mutation results JSON to this path.",
    )
    parser.add_argument(
        "--mutation-scope",
        choices=("live", "unit"),
        default="unit",
        help="Which mutation cases to run: live (existing SC-002) or unit (default).",
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
        return run_mutation_check(args)
    repeat = cast("int | None", args.repeat)
    if repeat is not None:
        forwarded = cast("list[str]", args.pytest_args)
        return run_repeat(
            resolve_cli=cast("bool", args.resolve_cli),
            runs=repeat,
            pytest_args=forwarded,
        )
    return run_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
