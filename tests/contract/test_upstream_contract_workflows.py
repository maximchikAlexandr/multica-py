from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def _read(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def test_pr_workflow_runs_only_offline_check() -> None:
    text = _read("ci.yml")
    assert "pull_request" in text
    assert "push" in text
    run_lines = [line for line in text.splitlines() if line.strip().startswith("run:")]
    run_block = "\n".join(run_lines)
    for forbidden in ("observe", "prepare-upgrade", "promote", "collect "):
        assert forbidden not in run_block, f"PR workflow must not run: {forbidden!r}"


def test_observer_workflow_is_separate() -> None:
    text = _read("upstream-contract-observer.yml")
    assert "schedule" in text or "workflow_dispatch" in text
    assert "observe" in text


def test_offline_check_in_ci_workflow() -> None:
    text = _read("ci.yml")
    assert "multica_py._internal.upstream_contract.cli check" in text
