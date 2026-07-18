from __future__ import annotations

import pathlib
import sys

from scripts.live_compatibility_report import build_compatibility_report
from scripts.resolve_multica_target import ResolvedTarget
from tests.live.settings import load_compatibility_target

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TARGET = REPO_ROOT / "contracts" / "multica-live-target.toml"


def test_build_compatibility_report_marks_pinned_regression() -> None:
    target = load_compatibility_target(TARGET)
    resolved = ResolvedTarget(
        target=target,
        cli_executable=pathlib.Path(sys.executable),
        cli_version_actual=target.cli_version_expected,
    )
    report = build_compatibility_report(
        resolved=resolved,
        suite_mode="extended",
        pytest_marker="live_smoke or live_extended",
        pytest_exit_code=1,
    )
    assert report["schema_version"] == 1
    assert report["regression_signal"] is True
    assert report["compatibility_signal_only"] is False
    assert report["interpretation"] == "pinned-target regression"


def test_build_compatibility_report_marks_upstream_signal_only() -> None:
    target = load_compatibility_target(TARGET)
    resolved = ResolvedTarget(
        target=target,
        cli_executable=pathlib.Path(sys.executable),
        cli_version_actual=target.cli_version_expected,
    )
    report = build_compatibility_report(
        resolved=resolved,
        suite_mode="extended",
        pytest_marker="live_smoke or live_extended",
        pytest_exit_code=1,
        observed_upstream_ref="main",
    )
    assert report["regression_signal"] is False
    assert report["compatibility_signal_only"] is True
    assert report["interpretation"] == "upstream-main compatibility signal only"
