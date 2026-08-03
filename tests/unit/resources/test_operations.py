from __future__ import annotations

import datetime
import hashlib
import importlib
import inspect
import pathlib
from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from tests.cases.operations import (
    GENERATED_OPERATION_CASES,
    LEGACY_ARGV_MIGRATION,
    OPERATION_CASES,
    RESOURCE_SPECS,
    OperationCase,
    _resource_attr,
    discover_public_methods,
)
from tools.upstream_contract.contract import validate_contract

_RESOURCE_MAP: dict[str, type] = dict(RESOURCE_SPECS)


def _configure_mock(mock_transport: MagicMock, case: OperationCase) -> None:
    if case.transport_side_effect is not None:
        if case.transport_method == "run_bytes":
            mock_transport.run_bytes.side_effect = case.transport_side_effect
        elif case.transport_method == "run_text":
            mock_transport.run_text.side_effect = case.transport_side_effect
        elif case.transport_method == "spawn":
            mock_transport.spawn.side_effect = case.transport_side_effect
        return
    if case.transport_method == "spawn":
        mock_transport.spawn.return_value = MagicMock()
    elif case.transport_method == "run_bytes":
        mock_transport.run_bytes.return_value = RawCommandResult(
            argv=tuple(case.expected_argv),
            exit_code=case.exit_code,
            stdout=case.stdout or b"{}",
            stderr=case.stderr,
            duration=datetime.timedelta(),
        )
    elif case.transport_method == "run_text":
        text = (case.stdout or b"{}").decode("utf-8", errors="replace")
        mock_transport.run_text.return_value = TextResult(
            text=text,
            stderr=case.stderr.decode("utf-8", errors="replace"),
            exit_code=case.exit_code,
        )


def _normalized_argv(call_argv: tuple[str, ...], case: OperationCase) -> tuple[str, ...]:
    normalized = list(call_argv)
    for position in case.dynamic_argv_positions:
        normalized[position] = case.expected_argv[position]
    return tuple(normalized)


def _assert_transport_call(mock_transport: MagicMock, case: OperationCase) -> None:
    transport = cast("CliTransport", mock_transport)
    config = ClientConfig()
    ra = _resource_attr(case.sdk_method)
    cls = _RESOURCE_MAP[ra]
    resource = cls(transport, config)
    method = getattr(resource, case.method)
    result = method(*case.args, **dict(case.kwargs))

    if case.assert_result is not None:
        case.assert_result(result, mock_transport)

    if case.transport_method == "run_bytes":
        mock_transport.run_bytes.assert_called_once()
        call_args = mock_transport.run_bytes.call_args
        assert (
            _normalized_argv(cast("tuple[str, ...]", call_args.args[0]), case) == case.expected_argv
        )
        assert call_args.kwargs.get("stdin") == case.stdin
        assert call_args.kwargs.get("timeout") == (
            datetime.timedelta(seconds=case.timeout) if case.timeout is not None else None
        )
    elif case.transport_method == "run_text":
        mock_transport.run_text.assert_called_once()
        call_args = mock_transport.run_text.call_args
        assert (
            _normalized_argv(cast("tuple[str, ...]", call_args.args[0]), case) == case.expected_argv
        )
    elif case.transport_method == "spawn":
        mock_transport.spawn.assert_called_once_with(tuple(case.expected_argv))


@pytest.mark.parametrize("case", list(OPERATION_CASES), ids=lambda c: c.id)
def test_operation(case: OperationCase, mock_transport: MagicMock) -> None:
    _configure_mock(mock_transport, case)
    _assert_transport_call(mock_transport, case)


def test_discovered_public_methods() -> None:
    discovered = discover_public_methods()
    canonical_cases = tuple(c for c in OPERATION_CASES if c.is_canonical)
    canonical = {c.sdk_method for c in canonical_cases}
    assert discovered == canonical
    assert len(canonical_cases) == len(canonical)
    assert len({c.id for c in OPERATION_CASES}) == len(OPERATION_CASES)
    generated = tuple(c for c in OPERATION_CASES if c.id.startswith("generated:"))
    manual = tuple(c for c in OPERATION_CASES if not c.id.startswith("generated:"))
    assert {c.id for c in generated} == {c.id for c in GENERATED_OPERATION_CASES}
    assert all(c.source_ref is None for c in generated)
    assert all(c.source_ref is not None for c in manual)
    assert all(c.contract_operation_id is not None for c in generated)


def test_approved_symbols_signatures_and_canonical_vectors_are_complete() -> None:
    contract = validate_contract(pathlib.Path("contracts/sdk-contract.json"))

    def contract_key(case: OperationCase) -> tuple[str, str]:
        assert case.contract_operation_id is not None
        if case.id.startswith("generated:"):
            _, entrypoint, _ = case.id.removeprefix("generated:").rsplit(":", 2)
            return case.contract_operation_id, entrypoint
        return case.contract_operation_id, "default"

    canonical_by_operation = {
        contract_key(case): case
        for case in OPERATION_CASES
        if case.is_canonical and case.contract_operation_id is not None
    }
    assert set(canonical_by_operation) == {
        (operation.operation_id, entrypoint.entrypoint_id)
        for operation in contract.operations
        for entrypoint in operation.entrypoints
    }
    assert len(canonical_by_operation) == sum(
        case.is_canonical and case.contract_operation_id is not None for case in OPERATION_CASES
    )
    catalogs = cast("dict[str, object]", contract.raw["catalogs"])
    signatures = cast("dict[str, object]", catalogs["signatures"])
    for operation in contract.operations:
        for entrypoint in operation.entrypoints:
            module_name, class_name, method_name = entrypoint.public_symbol.rsplit(".", 2)
            resource = getattr(importlib.import_module(module_name), class_name)
            method = getattr(resource, method_name)
            assert inspect.isfunction(method)
            assert entrypoint.signature_id in signatures
            assert (
                canonical_by_operation[(operation.operation_id, entrypoint.entrypoint_id)].method
                == method_name
            )


def test_legacy_payload_bijection() -> None:
    from tests.cases.legacy_payloads import LEGACY_PAYLOAD_FINGERPRINTS

    final_by_id: dict[str, OperationCase] = {c.id: c for c in OPERATION_CASES}

    def payload(case: OperationCase) -> tuple[object, ...]:
        return (
            case.resource_attr,
            case.method,
            case.args,
            tuple(sorted(dict(case.kwargs).items())),
            case.transport_method,
            case.expected_argv,
            case.stdin,
            case.timeout,
            case.stdout,
        )

    expected_legacy_ids = {f"legacy:{index:03d}" for index in range(1, 149)}
    assert set(LEGACY_ARGV_MIGRATION) == expected_legacy_ids
    assert len(LEGACY_PAYLOAD_FINGERPRINTS) == 148
    removed = {
        "legacy:014": "removed:attachments.list",
        "legacy:069": "removed:repositories.get",
        "legacy:070": "removed:repositories.checkout",
        "legacy:072": "removed:runtimes.get",
        "legacy:083": "removed:users.list",
        "legacy:084": "removed:users.get",
    }
    assert {key: LEGACY_ARGV_MIGRATION[key] for key in removed} == removed
    final_migration = {
        key: value for key, value in LEGACY_ARGV_MIGRATION.items() if key not in removed
    }
    assert len(final_migration.values()) == len(set(final_migration.values())) == 142
    assert set(final_migration.values()).issubset(final_by_id)

    legacy_by_id = {
        f"legacy:{index:03d}": fingerprint
        for index, fingerprint in enumerate(LEGACY_PAYLOAD_FINGERPRINTS, start=1)
    }
    for legacy_id, final_id in LEGACY_ARGV_MIGRATION.items():
        if legacy_id in removed:
            continue
        actual = hashlib.sha256(repr(payload(final_by_id[final_id])).encode()).hexdigest()
        assert legacy_by_id[legacy_id] == actual
