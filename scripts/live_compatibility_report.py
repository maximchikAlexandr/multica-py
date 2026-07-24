from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Literal, cast

from multica_py._internal.upstream_contract.generator.validation import TARGET_LITERALS
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
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(path)


def _load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def cmd_aggregate(args: argparse.Namespace) -> int:
    smoke_path = pathlib.Path(args.smoke) if args.smoke else None
    extended_path = pathlib.Path(args.extended) if args.extended else None
    mutation_path = pathlib.Path(args.mutation)
    stability_path = pathlib.Path(args.stability) if args.stability else None
    output = pathlib.Path(args.output)

    sections: dict[str, Any] = {}

    if smoke_path and smoke_path.exists():
        sections["smoke"] = _load(smoke_path)
    if extended_path and extended_path.exists():
        sections["extended"] = _load(extended_path)
    if mutation_path.exists():
        sections["mutation"] = _load(mutation_path)
    if stability_path and stability_path.exists():
        sections["stability"] = _load(stability_path)

    mutation_ok = False
    raw_m = sections.get("mutation")
    if raw_m is not None:
        if isinstance(raw_m, list):
            killed = sum(1 for x in raw_m if cast("dict[str, Any]", x).get("killed"))
            survived = len(raw_m) - killed
            invalid = 0
        else:
            m = cast("dict[str, Any]", raw_m)
            killed = int(m.get("killed", 0))
            survived = int(m.get("survived", 0))
            invalid = int(m.get("invalid", 0))
        mutation_ok = killed >= 3 and survived == 0 and invalid == 0

    smoke_ok = False
    raw_smoke = sections.get("smoke")
    if raw_smoke is not None:
        s = cast("dict[str, Any]", raw_smoke)
        smoke_ok = s.get("category") == "passed" and int(s.get("pytest_exit_code", 1)) == 0

    extended_ok = False
    raw_ext = sections.get("extended")
    if raw_ext is not None:
        e = cast("dict[str, Any]", raw_ext)
        extended_ok = e.get("category") == "passed" and int(e.get("pytest_exit_code", 1)) == 0

    stability_ok = False
    raw_stab = sections.get("stability")
    if raw_stab is not None:
        st = cast("dict[str, Any]", raw_stab)
        stability_ok = int(st.get("pass_count", 0)) >= 10

    accepted = mutation_ok
    if smoke_path:
        accepted = accepted and smoke_ok
    if extended_path:
        accepted = accepted and extended_ok
    if stability_path:
        accepted = accepted and stability_ok

    summary: dict[str, Any] = {
        "schema_version": 1,
        "accepted": accepted,
        "target": {
            "version": TARGET_LITERALS["version"],
            "tag": TARGET_LITERALS["tag"],
            "commit": TARGET_LITERALS["commit"],
        },
        "stages": sections,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    sys.stdout.write(f"acceptance-summary: accepted={accepted}\n")
    return 0 if accepted else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="live_compatibility_report")
    sub = parser.add_subparsers(dest="command", required=True)

    p_agg = sub.add_parser("aggregate")
    p_agg.add_argument("--smoke", default=None)
    p_agg.add_argument("--extended", default=None)
    p_agg.add_argument("--mutation", required=True)
    p_agg.add_argument("--stability", default=None)
    p_agg.add_argument("--output", required=True)
    p_agg.set_defaults(func=cmd_aggregate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
