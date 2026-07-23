"""Unit tests for test architecture scripts (manifest, duplicate map, stage CLI)."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

import pytest

from scripts.check_test_architecture import (
    STAGES,
    check_architecture,
    load_behavior_manifest,
    load_duplicate_map,
    validate_duplicate_map,
    validate_manifest_invariants,
)


@dataclass(frozen=True)
class ManifestLoadCase:
    id: str
    schema: int
    operations_count: int
    expect_success: bool
    error_fragment: str | None = None


@dataclass(frozen=True)
class DuplicateMapLoadCase:
    id: str
    schema: int
    records: list[dict[str, str]] | None
    expect_success: bool
    error_fragment: str | None = None


@dataclass(frozen=True)
class DuplicateValidateCase:
    id: str
    records: list[dict[str, str]]
    manifest_ops: dict[str, list[str]]
    manifest_invs: dict[str, str]
    expect_errors: int


def _write_manifest(
    path: pathlib.Path, schema: int, operations: dict[str, list[str]], invariants: dict[str, str]
) -> None:
    data: dict[str, object] = {
        "schema": schema,
        "source_snapshot": "b3a299b36d1ad5bc386b5e4517d2a348d53db31c",
        "operations": operations,
        "invariants": invariants,
    }
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _write_duplicate_map(path: pathlib.Path, schema: int, records: list[dict[str, str]]) -> None:
    data: dict[str, object] = {"schema": schema, "records": records}
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _make_operations(count: int) -> dict[str, list[str]]:
    return {f"op.{i}": ["argv", "decode"] for i in range(count)}


_MANIFEST_LOAD_CASES = (
    ManifestLoadCase("valid", 1, 111, True),
    ManifestLoadCase("wrong-schema", 2, 111, False, "schema must be 1"),
    ManifestLoadCase("too-few-ops", 1, 100, False, "must have at least 111 keys"),
)


@pytest.mark.parametrize("case", _MANIFEST_LOAD_CASES, ids=lambda c: c.id)
def test_load_behavior_manifest(tmp_path: pathlib.Path, case: ManifestLoadCase) -> None:
    path = tmp_path / "behavioral-coverage.json"
    _write_manifest(
        path,
        case.schema,
        _make_operations(case.operations_count),
        {"inv.1": "tests/test.py::test_fn"},
    )
    if case.expect_success:
        result = load_behavior_manifest(path)
        assert isinstance(result, dict)
    else:
        with pytest.raises(SystemExit, match=case.error_fragment or ""):
            load_behavior_manifest(path)


_DUPE_LOAD_CASES = (
    DuplicateMapLoadCase("valid-empty", 1, [], True),
    DuplicateMapLoadCase(
        "valid-with-records",
        1,
        [
            {
                "removed_node_id": "a",
                "retained_node_id": "b",
                "protected_contract": "operation:op.1:argv",
            }
        ],
        True,
    ),
    DuplicateMapLoadCase("wrong-schema", 2, [], False, "schema must be 1"),
    DuplicateMapLoadCase("missing-records", 1, None, False, "missing records list"),
)


@pytest.mark.parametrize("case", _DUPE_LOAD_CASES, ids=lambda c: c.id)
def test_load_duplicate_map(tmp_path: pathlib.Path, case: DuplicateMapLoadCase) -> None:
    path = tmp_path / "duplicate-removal-map.json"
    if case.records is None:
        path.write_text(json.dumps({"schema": case.schema}), encoding="utf-8")
    else:
        _write_duplicate_map(path, case.schema, case.records)
    if case.expect_success:
        result = load_duplicate_map(path)
        assert isinstance(result, dict)
    else:
        with pytest.raises(SystemExit, match=case.error_fragment or ""):
            load_duplicate_map(path)


_DUPE_VALIDATE_CASES = (
    DuplicateValidateCase(
        "valid",
        [
            {
                "removed_node_id": "old",
                "retained_node_id": "tests/test.py::test_fn",
                "protected_contract": "invariant:inv.1",
            }
        ],
        {"op.1": ["argv"]},
        {"inv.1": "tests/test.py::test_fn"},
        0,
    ),
    DuplicateValidateCase(
        "retained-node-missing",
        [
            {
                "removed_node_id": "old",
                "retained_node_id": "nonexistent",
                "protected_contract": "invariant:inv.1",
            }
        ],
        {"op.1": ["argv"]},
        {"inv.1": "tests/test.py::test_fn"},
        0,
    ),
    DuplicateValidateCase(
        "contract-missing-op",
        [
            {
                "removed_node_id": "old",
                "retained_node_id": "tests/test.py::test_fn",
                "protected_contract": "operation:op.99:argv",
            }
        ],
        {"op.1": ["argv"]},
        {"inv.1": "tests/test.py::test_fn"},
        1,
    ),
    DuplicateValidateCase(
        "contract-missing-inv",
        [
            {
                "removed_node_id": "old",
                "retained_node_id": "tests/test.py::test_fn",
                "protected_contract": "invariant:inv.99",
            }
        ],
        {"op.1": ["argv"]},
        {"inv.1": "tests/test.py::test_fn"},
        1,
    ),
    DuplicateValidateCase(
        "contract-unknown-format",
        [
            {
                "removed_node_id": "old",
                "retained_node_id": "tests/test.py::test_fn",
                "protected_contract": "unknown:foo:bar",
            }
        ],
        {"op.1": ["argv"]},
        {"inv.1": "tests/test.py::test_fn"},
        1,
    ),
)


@pytest.mark.parametrize("case", _DUPE_VALIDATE_CASES, ids=lambda c: c.id)
def test_validate_duplicate_map(case: DuplicateValidateCase) -> None:
    map_data: dict[str, object] = {"schema": 1, "records": case.records}
    manifest_data: dict[str, object] = {
        "schema": 1,
        "source_snapshot": "b3a299b36d1ad5bc386b5e4517d2a348d53db31c",
        "operations": case.manifest_ops,
        "invariants": case.manifest_invs,
    }
    errors = validate_duplicate_map(map_data, manifest_data)
    assert len(errors) == case.expect_errors, (
        f"expected {case.expect_errors} errors, got {len(errors)}: {errors}"
    )


_INVARIANT_CASES = (
    (
        "pr1-all-present",
        "pr1",
        {
            "network.offline-hard-fail": "",
            "process.cancellation": "",
            "process.timeout": "",
            "process.sigterm-escalation": "",
            "process.descendant-cleanup": "",
            "live.cleanup-lifo": "",
            "live.workspace-isolation": "",
            "live.oracle-consistency": "",
            "live.secret-scan": "",
            "sandbox.deterministic": "",
            "sandbox.provider-canary": "",
        },
        0,
    ),
    ("pr1-missing-one", "pr1", {"network.offline-hard-fail": ""}, 4),
    (
        "pr3-with-extras",
        "pr3",
        {
            "network.offline-hard-fail": "",
            "process.cancellation": "",
            "process.timeout": "",
            "process.sigterm-escalation": "",
            "process.descendant-cleanup": "",
            "live.cleanup-lifo": "",
            "live.workspace-isolation": "",
            "live.oracle-consistency": "",
            "live.secret-scan": "",
            "sandbox.deterministic": "",
            "sandbox.provider-canary": "",
            "packaging.artifact-required": "",
            "packaging.single-build": "",
            "tooling.no-tests-import": "",
        },
        0,
    ),
)


@pytest.mark.parametrize(
    "case_id,stage,invariants,expected_errors",
    _INVARIANT_CASES,
    ids=lambda x: x[0] if isinstance(x, tuple) and len(x) == 4 else x,
)
def test_validate_manifest_invariants(
    case_id: str, stage: str, invariants: dict[str, str], expected_errors: int
) -> None:
    manifest: dict[str, object] = {
        "schema": 1,
        "source_snapshot": "b3a299b36d1ad5bc386b5e4517d2a348d53db31c",
        "operations": _make_operations(111),
        "invariants": invariants,
    }
    errors = validate_manifest_invariants(manifest, stage)
    assert len(errors) == expected_errors


def test_check_architecture_stage_pr1_ok(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest_path = tmp_path / "behavioral-coverage.json"
    _write_manifest(
        manifest_path,
        1,
        _make_operations(111),
        {
            "network.offline-hard-fail": "tests/test.py::test_fn",
            "process.cancellation": "tests/test.py::test_fn",
            "process.timeout": "tests/test.py::test_fn",
            "process.sigterm-escalation": "tests/test.py::test_fn",
            "process.descendant-cleanup": "tests/test.py::test_fn",
            "live.cleanup-lifo": "tests/test.py::test_fn",
            "live.workspace-isolation": "tests/test.py::test_fn",
            "live.oracle-consistency": "tests/test.py::test_fn",
            "live.secret-scan": "tests/test.py::test_fn",
            "sandbox.deterministic": "tests/test.py::test_fn",
            "sandbox.provider-canary": "tests/test.py::test_fn",
        },
    )
    dupe_path = tmp_path / "duplicate-removal-map.json"
    _write_duplicate_map(dupe_path, 1, [])

    (tmp_path / "tests" / "component").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests" / "component" / "test_process_contract.py").write_text(
        "pytestmark = [pytest.mark.process, pytest.mark.serial]\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "-m \\"not live and not packaging\\""\n',
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts" / "check_test_baseline.py").write_text(
        "#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests" / "quality-baseline.json").write_text(
        '{"schema":2,"git_sha":"0000000000000000000000000000000000000000",'
        '"source_snapshot":"0000000000000000000000000000000000000000",'
        '"coverage":{"statement_percent":0,"branch_percent":0,"zones":{},"config_sha256":"sha256:0"},'
        '"mutation":{"killed":0,"survived":0,"timeout":0,"suspicious":0,"no_tests":0,"skipped":0,"score_percent":0,"config_sha256":"sha256:0"},'
        '"behavior":{"requirements_sha256":"sha256:0","operation_pairs":0,"invariants":0},'
        '"loc":{"tests_python":0,"live_support_python":0,"scripts_python":0,"max_test_support_file":0},'
        '"offline":{"duration_seconds":0,"collected":{}},"package_install_paths":0}\n',
        encoding="utf-8",
    )

    import scripts.check_test_architecture as arch
    import scripts.check_test_baseline as baseline_mod

    monkeypatch.setattr(arch, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(baseline_mod, "_assert_baseline_bytes_unchanged", lambda *_: None)
    assert arch.check_architecture("pr1") == 0


def test_check_architecture_unknown_stage_exit_2() -> None:
    assert check_architecture("unknown") == 2


def test_no_tests_import() -> None:
    """Guard-node for invariant ``tooling.no-tests-import``.

    Invokes ``check_architecture("pr3")`` to verify check #6 — that no file
    under ``scripts/`` or ``src/`` does ``from tests`` / ``import tests``.
    Also runs the inline check helper to fail closed with a precise finding
    on regressions.
    """
    import scripts.check_test_architecture as arch

    findings: list[str] = []
    arch._check_no_tests_imports(findings)
    assert findings == [], f"Check #6 regressions: {findings}"
