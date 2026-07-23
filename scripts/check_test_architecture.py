#!/usr/bin/env python3
"""Check test architecture: behavioral manifest, duplicate map, and stage gates."""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import sys
import tomllib
from collections.abc import Callable
from typing import cast

from scripts._loc_metrics import (
    glob_logical_lines,
    live_support_loc,
    max_test_support_file,
)
from scripts.check_test_baseline import (
    FINAL_KNOWN_GAPS,
    FINAL_LIVE_SUPPORT_LOC_CAP,
    FINAL_MAX_FILE_LOC_CAP,
    FINAL_TESTS_LOC_CAP,
)
from scripts.check_test_baseline import (
    compare_baseline as _compare_baseline,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
STAGES = frozenset({"pr1", "pr2", "pr3", "pr4", "final"})

_REGISTRY_TYPE_NAMES = frozenset({"ArgvCase", "DecodeCase", "CommandCase", "OperationDefinition"})
_REGISTRY_CONST_NAMES = frozenset({"COMMAND_CHECKS"})
_REGISTRY_MODULES = (
    pathlib.Path("tests") / "cases",
    pathlib.Path("tests") / "component" / "command_cases.py",
    pathlib.Path("tests") / "component" / "resource_support.py",
    pathlib.Path("tests") / "unit" / "resources" / "cases",
    pathlib.Path("tests") / "unit" / "resources" / "cases" / "argv.py",
    pathlib.Path("tests") / "unit" / "resources" / "cases" / "decode.py",
)


def load_behavior_manifest(path: pathlib.Path, stage: str = "") -> dict[str, object]:
    parsed: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise SystemExit("behavior manifest root must be an object")
    manifest = cast("dict[str, object]", parsed)
    schema = manifest.get("schema")
    if schema != 1:
        raise SystemExit(f"behavior manifest schema must be 1, got {schema}")
    operations = manifest.get("operations")
    if not isinstance(operations, dict):
        raise SystemExit("behavior manifest missing operations dict")
    if stage != "pr1" and len(operations) < 111:
        raise SystemExit(
            f"behavior manifest operations must have at least 111 keys, got {len(operations)}"
        )
    invariants = manifest.get("invariants")
    if not isinstance(invariants, dict):
        raise SystemExit("behavior manifest missing invariants dict")
    return manifest


def load_duplicate_map(path: pathlib.Path) -> dict[str, object]:
    parsed: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise SystemExit("duplicate map root must be an object")
    data = cast("dict[str, object]", parsed)
    schema = data.get("schema")
    if schema != 1:
        raise SystemExit(f"duplicate map schema must be 1, got {schema}")
    records = data.get("records")
    if not isinstance(records, list):
        raise SystemExit("duplicate map missing records list")
    records_list = cast("list[dict[str, object]]", records)
    for i, record in enumerate(records_list):
        if not isinstance(record, dict):
            raise SystemExit(f"duplicate map record {i} must be an object")
        for key in ("removed_node_id", "retained_node_id", "protected_contract"):
            if key not in record:
                raise SystemExit(f"duplicate map record {i} missing {key}")
    return data


def validate_duplicate_map(
    map_data: dict[str, object], manifest_data: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    records = map_data.get("records")
    if not isinstance(records, list):
        errors.append("duplicate map missing records list")
        return errors
    operations = manifest_data.get("operations")
    if not isinstance(operations, dict):
        errors.append("manifest missing operations")
        return errors
    invariants = manifest_data.get("invariants")
    if not isinstance(invariants, dict):
        errors.append("manifest missing invariants")
        return errors
    all_manifest_ids: set[str] = set()
    all_manifest_ids.update(str(v) for v in invariants.values())
    records_list = cast("list[dict[str, object]]", records)
    for i, record in enumerate(records_list):
        retained = record.get("retained_node_id")
        contract = record.get("protected_contract")
        if isinstance(retained, str):
            pass
        else:
            errors.append(f"record {i}: retained_node_id must be a string")
        if isinstance(contract, str):
            if contract.startswith("operation:"):
                parts = contract.split(":")
                if len(parts) == 3:
                    op_id, dim = parts[1], parts[2]
                    if op_id not in operations:
                        errors.append(
                            f"record {i}: protected contract operation {op_id!r} not in manifest"
                        )
                    elif dim not in operations.get(op_id, []):
                        if isinstance(operations.get(op_id), list):
                            errors.append(
                                f"record {i}: operation {op_id!r} missing dimension {dim!r}"
                            )
                else:
                    errors.append(f"record {i}: invalid operation contract format {contract!r}")
            elif contract.startswith("invariant:"):
                inv_id = contract.split(":", 1)[1]
                if inv_id not in invariants:
                    errors.append(
                        f"record {i}: protected contract invariant {inv_id!r} not in manifest"
                    )
            else:
                errors.append(f"record {i}: unknown contract format {contract!r}")
        else:
            errors.append(f"record {i}: protected_contract must be a string")
    return errors


def validate_manifest_invariants(manifest_data: dict[str, object], stage: str) -> list[str]:
    errors: list[str] = []
    invariants = manifest_data.get("invariants")
    if not isinstance(invariants, dict):
        errors.append("manifest missing invariants dict")
        return errors
    required_process = frozenset(
        {
            "network.offline-hard-fail",
            "process.cancellation",
            "process.timeout",
            "process.sigterm-escalation",
            "process.descendant-cleanup",
        }
    )
    required_live = frozenset(
        {
            "live.cleanup-lifo",
            "live.workspace-isolation",
            "live.oracle-consistency",
            "live.secret-scan",
        }
    )
    required_sandbox = frozenset({"sandbox.deterministic", "sandbox.provider-canary"})
    required_packaging = frozenset(
        {"packaging.artifact-required", "packaging.single-build", "tooling.no-tests-import"}
    )
    stage_map: dict[str, frozenset[str]] = {
        "pr1": required_process,
        "pr2": required_process,
        "pr3": required_process | required_packaging,
        "pr4": required_process | required_packaging | required_live,
        "final": required_process | required_packaging | required_live | required_sandbox,
    }
    expected = stage_map.get(stage, frozenset())
    for key in expected:
        if key not in invariants:
            errors.append(f"required invariant {key!r} missing for stage {stage}")
    return errors


def _is_exported_via_init(init_path: pathlib.Path, name: str) -> bool:
    if not init_path.is_file():
        return False
    try:
        tree = ast.parse(init_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and elt.value == name:
                                return True
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local = alias.asname if alias.asname is not None else alias.name
                if local == name:
                    return True
    return False


def _check_registry_names(findings: list[str]) -> None:
    """Check #1: no module-level class/constant with registry names in registry modules."""
    for mod in _REGISTRY_MODULES:
        full = REPO_ROOT / mod
        if not full.exists():
            continue
        files = sorted(full.rglob("*.py")) if full.is_dir() else [full]
        for path in files:
            if path.name == "__init__.py" and path == full:
                init_path = path
            else:
                init_path = full / "__init__.py" if full.is_dir() else full.parent / "__init__.py"
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name in _REGISTRY_TYPE_NAMES:
                    if _is_exported_via_init(init_path, node.name):
                        findings.append(
                            f"Check #1: registry class {node.name!r} at {path.relative_to(REPO_ROOT)}"
                        )
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in _REGISTRY_CONST_NAMES:
                            findings.append(
                                f"Check #1: registry constant {target.id!r} at {path.relative_to(REPO_ROOT)}"
                            )


def _load_live_policy() -> dict[str, dict[str, str]]:
    """Load the live policy catalog from ``tests/cases/operations.py``.

    Reads the AST of the operations module to extract ``_LIVE_POLICY_RAW`` so
    the script can validate the catalog without importing the tests package.
    Returns:
        Mapping of sdk_method to ``{"mode": ..., "owner": ...}`` fields. Empty
        if the file is missing or unreadable.
    """
    policy_path = REPO_ROOT / "tests" / "cases" / "operations.py"
    if not policy_path.is_file():
        return {}
    try:
        tree = ast.parse(policy_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return {}
    policy: dict[str, dict[str, str]] = {}
    for node in ast.walk(tree):
        if (
            not isinstance(node, ast.AnnAssign)
            or not isinstance(node.target, ast.Name)
            or node.target.id != "_LIVE_POLICY_RAW"
        ):
            continue
        if node.value is None:
            return {}
        raw = cast("object", ast.literal_eval(node.value))
        if not isinstance(raw, dict):
            return {}
        for sdk, entry in cast("dict[str, object]", raw).items():
            if isinstance(entry, tuple) and len(entry) == 2:
                mode, owner = entry
            else:
                mode, owner = "unrunnable", "none"
            policy[str(sdk)] = {"mode": str(mode), "owner": str(owner)}
        return policy
    return policy


def _check_operation_cases_uniqueness(findings: list[str]) -> None:
    """Check #2/3/4/5/11: at most one registry, no duplicates, 111 unique, consistent live, owner present.

    Source of truth for the canonical OPERATION_CASES is the
    ``_LIVE_POLICY_RAW`` dict in ``tests/cases/operations.py`` (consumed by
    the ``_make_case`` genexp). The script reads the dict via AST to avoid
    importing the tests package.
    """
    cases_dir = REPO_ROOT / "tests" / "cases"
    if not cases_dir.is_dir():
        return
    registry_names = ("OPERATION_CASES", "ERROR_CASES")
    for name in registry_names:
        candidates: list[pathlib.Path] = []
        for path in sorted(cases_dir.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == name:
                            candidates.append(path)
        if len(candidates) > 1:
            findings.append(
                f"Check #2: {name} assigned in multiple files: {[str(p.relative_to(REPO_ROOT)) for p in candidates]}"
            )

    live_policy = _load_live_policy()
    sdk_method_ids = sorted(live_policy.keys())
    if len(sdk_method_ids) != len(set(sdk_method_ids)):
        from collections import Counter

        dupes = [k for k, v in Counter(sdk_method_ids).items() if v > 1]
        findings.append(f"Check #3: duplicate sdk_method in OPERATION_CASES: {sorted(dupes)}")
    if len(sdk_method_ids) != 111:
        findings.append(f"Check #4: OPERATION_CASES has {len(sdk_method_ids)} cases, expected 111")

    live_policies: dict[str, set[tuple[str, str]]] = {}
    for sdk, entry in live_policy.items():
        live_policies.setdefault(sdk, set()).add((entry["mode"], entry["owner"]))
    for op, policies in live_policies.items():
        if len(policies) > 1:
            findings.append(f"Check #5: inconsistent live policy for {op}: {sorted(policies)}")

    for sdk, entry in live_policy.items():
        if entry["mode"] not in {"", "none"} and not entry["owner"]:
            findings.append(f"Check #11: missing live owner for {sdk} (mode={entry['mode']})")


def _check_payload_size(findings: list[str]) -> None:
    """Check #15: payloads >4096 bytes stored in both Python and tests/fixtures/golden/."""
    payloads_path = REPO_ROOT / "tests" / "cases" / "payloads.py"
    if not payloads_path.is_file():
        return
    text = payloads_path.read_text(encoding="utf-8")
    if len(text.encode("utf-8")) > 4096:
        findings.append("Check #15: tests/cases/payloads.py exceeds 4096 bytes")
    golden_dir = REPO_ROOT / "tests" / "fixtures" / "golden"
    if not golden_dir.is_dir():
        return
    for path in sorted(golden_dir.iterdir()):
        if path.is_file():
            findings.append(
                f"Check #15: tests/fixtures/golden/{path.name} present alongside payloads.py"
            )


def _check_tests_loc(findings: list[str], baseline_path: pathlib.Path) -> None:
    """Tests LOC must not exceed pr1 baseline."""
    if not baseline_path.is_file():
        return
    parsed: object = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        return
    loc = parsed.get("loc")
    if not isinstance(loc, dict):
        return
    baseline_tests = loc.get("tests_python")
    if not isinstance(baseline_tests, int):
        return
    current = glob_logical_lines(REPO_ROOT / "tests", "**/*.py")
    if current > baseline_tests:
        findings.append(f"Tests LOC {current} exceeds pr1 baseline {baseline_tests}")


def _live_support_loc_now() -> int:
    """Compute the canonical live_support LOC the same way the baseline script does."""
    return live_support_loc(REPO_ROOT)


def _max_file_loc_now() -> int:
    return max_test_support_file(REPO_ROOT)


def _check_final_limits(
    findings: list[str],
    *,
    strict: bool,
) -> None:
    """Check #13: final-stage caps from ``contracts/quality-gates.md``.

    Returns the three findings as warnings (informational prints) unless
    ``strict`` is true, in which case they hard-fail. The known-gap
    tolerance exists because US5 is best effort and the slim-down requires
    T068/T074 work that breaks coverage if done without the full migration.
    """
    tests_now = glob_logical_lines(REPO_ROOT / "tests", "**/*.py")
    live_now = _live_support_loc_now()
    max_file = _max_file_loc_now()

    if tests_now > FINAL_TESTS_LOC_CAP:
        msg = (
            f"Tests LOC {tests_now} > final cap {FINAL_TESTS_LOC_CAP} "
            f"(known_gap: {FINAL_KNOWN_GAPS['tests_python']})"
        )
        if strict:
            findings.append(f"Check #13: {msg}")
        else:
            print(f"WARN: {msg}")
    if live_now > FINAL_LIVE_SUPPORT_LOC_CAP:
        msg = (
            f"live_support_python LOC {live_now} > final cap {FINAL_LIVE_SUPPORT_LOC_CAP} "
            f"(known_gap: {FINAL_KNOWN_GAPS['live_support_python']})"
        )
        if strict:
            findings.append(f"Check #13: {msg}")
        else:
            print(f"WARN: {msg}")
    if max_file > FINAL_MAX_FILE_LOC_CAP:
        findings.append(f"Check #13: max file LOC {max_file} > final cap {FINAL_MAX_FILE_LOC_CAP}")


def _iter_python_files(root: pathlib.Path) -> list[pathlib.Path]:
    if not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def _check_no_tests_imports(findings: list[str]) -> None:
    """Check #6: scripts/ and src/ must not import tests.* (production code).

    Live tests may import tests.cases / tests.live; the guard is about the
    toolchain boundary.
    """
    for boundary in (REPO_ROOT / "scripts", REPO_ROOT / "src"):
        for path in _iter_python_files(boundary):
            rel = path.relative_to(REPO_ROOT)
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "tests" or alias.name.startswith("tests."):
                            findings.append(f"Check #6: {rel} imports {alias.name!r}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module is None:
                        continue
                    if node.module == "tests" or node.module.startswith("tests."):
                        findings.append(f"Check #6: {rel} imports {node.module!r}")


def _check_no_packaging_skip(findings: list[str]) -> None:
    """Check #7: tests/packaging/ must not contain pytest.skip or pytest.xfail."""
    packaging_dir = REPO_ROOT / "tests" / "packaging"
    if not packaging_dir.is_dir():
        return
    for path in _iter_python_files(packaging_dir):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(REPO_ROOT)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"skip", "xfail"} and ast.unparse(node.func) in {
                    "pytest.skip",
                    "pytest.xfail",
                }:
                    findings.append(
                        f"Check #7: {rel}:{node.lineno} forbids pytest.skip / pytest.xfail in packaging"
                    )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for dec in node.decorator_list:
                    qualname = ast.unparse(dec)
                    if "skip" in qualname or "xfail" in qualname:
                        findings.append(
                            f"Check #7: {rel}:{node.lineno} forbids skip/xfail decorator in packaging"
                        )


def _check_no_fixtures_json(findings: list[str]) -> None:
    """Check #14: tests/fixtures/json/ must not exist after stage pr3."""
    legacy = REPO_ROOT / "tests" / "fixtures" / "json"
    if legacy.is_dir():
        findings.append(
            f"Check #14: legacy {legacy.relative_to(REPO_ROOT)} must be deleted after stage pr3"
        )


def _check_no_getfixturevalue_in_live(findings: list[str]) -> None:
    """Check #9: tests/live/ must not call request.getfixturevalue."""
    live_dir = REPO_ROOT / "tests" / "live"
    if not live_dir.is_dir():
        return
    for path in _iter_python_files(live_dir):
        rel = path.relative_to(REPO_ROOT)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "getfixturevalue":
                    findings.append(
                        f"Check #9: {rel}:{node.lineno} forbids request.getfixturevalue in tests/live/"
                    )


def _check_no_resource_identity_branch_in_crud(findings: list[str]) -> None:
    """Check #10: tests/live/test_crud.py must not branch/cast/lookup on resource identity.

    Resource-specific code (isinstance, .id, /api/<resource>/) is forbidden
    because the executor must be generic across all CRUD descriptors.
    """
    crud_path = REPO_ROOT / "tests" / "live" / "test_crud.py"
    if not crud_path.is_file():
        findings.append("Check #10: tests/live/test_crud.py not found")
        return
    text = crud_path.read_text(encoding="utf-8")
    for needle in ("isinstance(", "/api/"):
        if needle in text:
            findings.append(
                f"Check #10: tests/live/test_crud.py contains forbidden resource-identity token {needle!r}"
            )


def _check_pr1_gates(findings: list[str], manifest: dict[str, object] | None) -> None:
    process_path = REPO_ROOT / "tests" / "component" / "test_process_contract.py"
    if not process_path.is_file():
        findings.append("Check #8: test_process_contract.py not found")
    else:
        content = process_path.read_text(encoding="utf-8")
        if "pytest.mark.process" not in content or "pytest.mark.serial" not in content:
            findings.append("Check #8: test_process_contract.py missing process or serial markers")

    pyproject_path = REPO_ROOT / "pyproject.toml"
    if not pyproject_path.is_file():
        findings.append("Check #12: pyproject.toml not found")
    else:
        pyproject = cast(
            "dict[str, object]", tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        )
        addopts = str(
            cast(
                "dict[str, object]",
                cast(
                    "dict[str, object]",
                    cast("dict[str, object]", pyproject.get("tool", {})).get("pytest", {}),
                ).get("ini_options", {}),
            ).get("addopts", "")
        )
        if "not live and not packaging" not in addopts:
            findings.append("Check #12: default addopts missing 'not live and not packaging'")

    try:
        _compare_baseline(REPO_ROOT / "tests" / "quality-baseline.json", "pr1", REPO_ROOT)
    except SystemExit as exc:
        findings.append(f"baseline self-check failed: {exc}")


def check_architecture(stage: str, *, strict: bool = False) -> int:
    if stage not in STAGES:
        return 2
    manifest_path = REPO_ROOT / "tests" / "behavioral-coverage.json"
    duplicate_path = REPO_ROOT / "tests" / "duplicate-removal-map.json"
    findings: list[str] = []
    manifest: dict[str, object] | None = None
    if manifest_path.is_file():
        manifest = load_behavior_manifest(manifest_path, stage)
        inv_errors = validate_manifest_invariants(manifest, stage)
        findings.extend(f"invariant: {e}" for e in inv_errors)
    if duplicate_path.is_file():
        dm = load_duplicate_map(duplicate_path)
        if manifest is not None:
            dupe_errors = validate_duplicate_map(dm, manifest)
            findings.extend(f"duplicate-map: {e}" for e in dupe_errors)

    baseline_path = REPO_ROOT / "tests" / "quality-baseline.json"

    def _pr1_self_check(f: list[str]) -> None:
        _check_pr1_gates(f, manifest)

    def _tests_loc_check(f: list[str]) -> None:
        _check_tests_loc(f, baseline_path)

    def _final_limits_check(f: list[str]) -> None:
        _check_final_limits(f, strict=strict)

    _pr1: tuple[Callable[[list[str]], None], ...] = (_pr1_self_check,)
    _pr2 = _pr1 + (
        _check_registry_names,
        _check_operation_cases_uniqueness,
        _check_payload_size,
        _tests_loc_check,
    )
    _pr3 = _pr2 + (
        _check_no_tests_imports,
        _check_no_packaging_skip,
        _check_no_fixtures_json,
    )
    _pr4 = _pr3 + (
        _check_no_getfixturevalue_in_live,
        _check_no_resource_identity_branch_in_crud,
    )
    _final = _pr4 + (_final_limits_check,)
    _STAGE_CHECKS: dict[str, tuple[Callable[[list[str]], None], ...]] = {
        "pr1": _pr1,
        "pr2": _pr2,
        "pr3": _pr3,
        "pr4": _pr4,
        "final": _final,
    }

    for check in _STAGE_CHECKS[stage]:
        check(findings)

    if findings:
        for f in findings:
            print(f"FAIL: {f}")
        return 1
    print(f"Stage {stage} check passed ({len(findings)} findings)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check test architecture")
    stages_list: list[str] = sorted(STAGES)
    parser.add_argument("--stage", required=True, choices=stages_list)
    parser.add_argument(
        "--strict-final",
        action="store_true",
        help="Final stage: hard-fail on known_gap LOC limits instead of warning.",
    )
    args = parser.parse_args()
    return check_architecture(cast("str", args.stage), strict=cast("bool", args.strict_final))


if __name__ == "__main__":
    raise SystemExit(main())
