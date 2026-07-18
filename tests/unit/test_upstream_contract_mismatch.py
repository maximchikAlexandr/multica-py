from __future__ import annotations

import pathlib

import msgspec

from multica_py._internal.upstream_contract import schema
from multica_py._internal.upstream_contract.collectors import source as source_collector
from multica_py._internal.upstream_contract.models import (
    CommandContract,
    ExecutionContract,
    OutputContract,
)

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"


def test_exporter_help_mismatch_classified_as_mismatch() -> None:
    exporter = schema.decode_contract(FIXTURES / "exporter-contract.json")
    help_contract = schema.decode_contract(FIXTURES / "help-parser-contract.json")
    diff = source_collector.classify_exporter_help_mismatch(exporter, help_contract)
    if diff.changes:
        assert all(c.severity == "mismatch" for c in diff.changes)


def test_exporter_help_agree_returns_true_for_identical() -> None:
    exporter = schema.decode_contract(FIXTURES / "exporter-contract.json")
    assert source_collector.exporter_help_agree(exporter, exporter) is True


def test_exporter_help_agree_returns_false_on_breaking() -> None:
    exporter = schema.decode_contract(FIXTURES / "exporter-contract.json")
    empty = msgspec.structs.replace(exporter, commands=())
    assert source_collector.exporter_help_agree(exporter, empty) is False


def test_exporter_help_agree_returns_false_on_additive() -> None:
    exporter = schema.decode_contract(FIXTURES / "exporter-contract.json")
    extra = CommandContract(
        path=("extra",),
        use="extra",
        execution=ExecutionContract(),
        output=OutputContract(),
    )
    with_extra = msgspec.structs.replace(exporter, commands=exporter.commands + (extra,))
    assert source_collector.exporter_help_agree(exporter, with_extra) is False


def test_exporter_help_agree_returns_false_on_potentially_breaking() -> None:
    exporter = schema.decode_contract(FIXTURES / "exporter-contract.json")
    cmd = exporter.commands[0]
    deprecated = msgspec.structs.replace(cmd, deprecated="use list instead")
    with_deprecation = msgspec.structs.replace(
        exporter,
        commands=(deprecated, *exporter.commands[1:]),
    )
    assert source_collector.exporter_help_agree(exporter, with_deprecation) is False


def test_classify_uses_mismatch_kind() -> None:
    exporter = schema.decode_contract(FIXTURES / "exporter-contract.json")
    help_contract = schema.decode_contract(FIXTURES / "help-parser-contract.json")
    diff = source_collector.classify_exporter_help_mismatch(exporter, help_contract)
    for change in diff.changes:
        assert change.kind in {
            "source_exporter_help_mismatch",
            "doc_only_changed",
            "provenance_only_changed",
        }
