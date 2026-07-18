from __future__ import annotations

import pathlib

from multica_py._internal.upstream_contract import diff as diff_module
from multica_py._internal.upstream_contract import impact as impact_module
from multica_py._internal.upstream_contract import schema

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"
MUTATIONS = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "mutations"
BASELINE = FIXTURES / "supported-cli-contract-baseline.json"
BASELINE_MANIFEST = FIXTURES / "coverage-manifest-baseline.json"


def test_impact_links_command_changes_to_operations() -> None:
    manifest = schema.decode_coverage(BASELINE_MANIFEST)
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "command-added.json")
    diff = diff_module.diff_contracts(before, after)
    impact = impact_module.build_impact(diff, manifest)
    unresolved = [e for e in impact.entries if e.unresolved_reason]
    assert unresolved
    assert any(e.command_path == ("sprint", "list") for e in unresolved)


def test_impact_links_flag_changes_to_operations() -> None:
    manifest = schema.decode_coverage(BASELINE_MANIFEST)
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "required-flag-added.json")
    diff = diff_module.diff_contracts(before, after)
    impact = impact_module.build_impact(diff, manifest)
    linked = [e for e in impact.entries if e.operation_id == "agents.list"]
    assert linked


def test_impact_skips_doc_only_changes() -> None:
    manifest = schema.decode_coverage(BASELINE_MANIFEST)
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "help-text-changed.json")
    diff = diff_module.diff_contracts(before, after)
    impact = impact_module.build_impact(diff, manifest)
    assert all(e.severity not in ("doc_only", "provenance_only") for e in impact.entries)


def test_impact_links_removed_command_to_operation() -> None:
    manifest = schema.decode_coverage(BASELINE_MANIFEST)
    before = schema.decode_contract(BASELINE)
    after = schema.decode_contract(MUTATIONS / "command-removed.json")
    diff = diff_module.diff_contracts(before, after)
    impact = impact_module.build_impact(diff, manifest)
    ops = {e.operation_id for e in impact.entries if e.operation_id}
    assert ops == {"agents.list"}
