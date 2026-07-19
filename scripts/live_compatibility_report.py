from __future__ import annotations

import json
import pathlib
from typing import Literal

from scripts.resolve_multica_target import ResolvedTarget, build_version_report

REPORT_SCHEMA_VERSION = 1
SuiteMode = Literal["smoke", "extended"]


def build_compatibility_report(
    *,
    resolved: ResolvedTarget,
    suite_mode: SuiteMode,
    pytest_marker: str,
    pytest_exit_code: int,
    observed_upstream_ref: str | None = None,
) -> dict[str, object]:
    """Build a versioned pinned-vs-upstream compatibility report.

    Args:
        resolved: Verified compatibility target for the run.
        suite_mode: Live suite profile executed by the runner.
        pytest_marker: Marker expression passed to pytest.
        pytest_exit_code: Process exit code from pytest.
        observed_upstream_ref: Optional upstream ref when probing non-pinned code.

    Returns:
        JSON-serializable compatibility report payload.
    """
    pinned = build_version_report(resolved)
    observed_ref = observed_upstream_ref or pinned["upstream_ref"]
    pinned_ref = pinned["upstream_ref"]
    is_upstream_probe = observed_ref != pinned_ref
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "suite_mode": suite_mode,
        "pytest_marker": pytest_marker,
        "pytest_exit_code": pytest_exit_code,
        "pinned_target": pinned,
        "observed_upstream_ref": observed_ref,
        "regression_signal": pytest_exit_code != 0 and not is_upstream_probe,
        "compatibility_signal_only": is_upstream_probe,
        "interpretation": (
            "upstream-main compatibility signal only"
            if is_upstream_probe
            else "pinned-target regression"
        ),
    }


def write_compatibility_report(path: pathlib.Path, report: dict[str, object]) -> None:
    """Write one compatibility report atomically to disk.

    Args:
        path: Destination JSON file path.
        report: Compatibility report payload.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(path)
