from __future__ import annotations

import pathlib

from multica_py._internal.upstream_contract import coverage, schema
from multica_py._internal.upstream_contract import diff as diff_module
from multica_py._internal.upstream_contract import impact as impact_module
from multica_py._internal.upstream_contract import suggestions as suggestions_module
from multica_py._internal.upstream_contract import upgrade as upgrade_module
from multica_py._internal.upstream_contract.paths import COVERAGE_PATH

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"
MUTATIONS = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "mutations"


def test_manifest_suggestions_are_incomplete() -> None:
    manifest = schema.decode_coverage(COVERAGE_PATH)
    before = schema.decode_contract(FIXTURES / "supported-cli-contract-baseline.json")
    after = schema.decode_contract(FIXTURES / "candidate-cli-contract-v2.json")
    diff = diff_module.diff_contracts(before, after)
    diff = diff_module.resolve_affected_operations(
        diff, coverage.build_bindings_index(manifest)
    )
    suggestions = suggestions_module.generate_manifest_suggestions(diff, manifest)
    assert suggestions
    assert all(s.coverage_level == "incomplete" for s in suggestions)
    assert all(s.operation_id != "unresolved" for s in suggestions)


def test_manifest_suggestions_skip_documentation_only() -> None:
    manifest = schema.decode_coverage(COVERAGE_PATH)
    before = schema.decode_contract(FIXTURES / "supported-cli-contract-baseline.json")
    after = schema.decode_contract(MUTATIONS / "help-text-changed.json")
    diff = diff_module.diff_contracts(before, after)
    suggestions = suggestions_module.generate_manifest_suggestions(diff, manifest)
    assert all(s.severity != "doc_only" for s in suggestions)


def test_apply_manifest_suggestions_keeps_rows_incomplete() -> None:
    manifest = schema.decode_coverage(COVERAGE_PATH)
    before = schema.decode_contract(FIXTURES / "supported-cli-contract-baseline.json")
    after = schema.decode_contract(FIXTURES / "candidate-cli-contract-v2.json")
    diff = diff_module.diff_contracts(before, after)
    diff = diff_module.resolve_affected_operations(
        diff, coverage.build_bindings_index(manifest)
    )
    suggestions = suggestions_module.generate_manifest_suggestions(diff, manifest)
    new_manifest = suggestions_module.apply_manifest_suggestions(manifest, suggestions)
    applied = [d for d in new_manifest.decisions if d.coverage_level == "incomplete"]
    assert applied


def test_changelog_fragment_summarises() -> None:
    before = schema.decode_contract(FIXTURES / "supported-cli-contract-baseline.json")
    after = schema.decode_contract(FIXTURES / "candidate-cli-contract-v2.json")
    diff = diff_module.diff_contracts(before, after)
    fragment = suggestions_module.generate_changelog_fragment(diff)
    assert "breaking" in fragment
    assert "additive" in fragment


def test_implementation_tasks_lists_changes() -> None:
    before = schema.decode_contract(FIXTURES / "supported-cli-contract-baseline.json")
    after = schema.decode_contract(FIXTURES / "candidate-cli-contract-v2.json")
    diff = diff_module.diff_contracts(before, after)
    tasks = suggestions_module.generate_implementation_tasks(diff)
    assert any("command_added" in t for t in tasks)


def test_build_bundle_returns_valid_bundle() -> None:
    before = schema.decode_contract(FIXTURES / "supported-cli-contract-baseline.json")
    after = schema.decode_contract(FIXTURES / "candidate-cli-contract-v2.json")
    diff = diff_module.diff_contracts(before, after)
    manifest = schema.decode_coverage(COVERAGE_PATH)
    impact = impact_module.build_impact(diff, manifest)
    bundle = upgrade_module.build_bundle(
        candidate_ref="candidate.json",
        diff=diff,
        impact=impact,
        manifest=manifest,
        generated_at="2026-07-18T00:00:00Z",
    )
    assert bundle.schema_version == 1
    assert bundle.upstream_diff.summary["total"] == len(bundle.upstream_diff.changes)
