from __future__ import annotations

import datetime
import hashlib
from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from tests.cases.operations import (
    LEGACY_ARGV_MIGRATION,
    OPERATION_CASES,
    RESOURCE_SPECS,
    OperationCase,
    _resource_attr,
    discover_public_methods,
)

_RESOURCE_MAP: dict[str, type] = dict(RESOURCE_SPECS)


def _configure_mock(mock_transport: MagicMock, case: OperationCase) -> None:
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


def _assert_transport_call(mock_transport: MagicMock, case: OperationCase) -> None:
    transport = cast("CliTransport", mock_transport)
    config = ClientConfig()
    ra = _resource_attr(case.sdk_method)
    cls = _RESOURCE_MAP[ra]
    resource = cls(transport, config)
    method = getattr(resource, case.method)
    result = method(*case.args, **dict(case.kwargs))

    if case.assert_result is not None:
        case.assert_result(result)

    if case.transport_method == "run_bytes":
        mock_transport.run_bytes.assert_called_once()
        call_args = mock_transport.run_bytes.call_args
        assert call_args.args == (tuple(case.expected_argv),)
        assert call_args.kwargs.get("stdin") == case.stdin
        assert call_args.kwargs.get("timeout") == (
            datetime.timedelta(seconds=case.timeout) if case.timeout is not None else None
        )
    elif case.transport_method == "run_text":
        mock_transport.run_text.assert_called_once()
        call_args = mock_transport.run_text.call_args
        assert call_args.args == (tuple(case.expected_argv),)
    elif case.transport_method == "spawn":
        mock_transport.spawn.assert_called_once_with(tuple(case.expected_argv))


@pytest.mark.parametrize("case", list(OPERATION_CASES), ids=lambda c: c.id)
def test_operation(case: OperationCase, mock_transport: MagicMock) -> None:
    _configure_mock(mock_transport, case)
    _assert_transport_call(mock_transport, case)


def test_discovered_public_methods() -> None:
    discovered = discover_public_methods()
    canonical = {c.sdk_method for c in OPERATION_CASES if c.is_canonical}
    assert discovered == canonical
    assert len(discovered) == 117
    assert len(OPERATION_CASES) == 141
    assert sum(1 for c in OPERATION_CASES if c.is_canonical) == 117
    assert sum(1 for c in OPERATION_CASES if not c.is_canonical) == 24
    generated = tuple(c for c in OPERATION_CASES if c.contract_operation_id is not None)
    manual = tuple(c for c in OPERATION_CASES if c.contract_operation_id is None)
    assert len(generated) == 30
    assert len(manual) == 111
    assert all(c.source_ref is None for c in generated)
    assert all(c.source_ref is not None for c in manual)
    assert all(
        (c.contract_operation_id is None) == (c.source_ref is not None) for c in OPERATION_CASES
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

    expected_legacy_ids = {f"legacy:{index:03d}" for index in range(1, 139)}
    assert set(LEGACY_ARGV_MIGRATION) == expected_legacy_ids
    assert len(LEGACY_PAYLOAD_FINGERPRINTS) == 138
    assert len(LEGACY_ARGV_MIGRATION.values()) == len(set(LEGACY_ARGV_MIGRATION.values())) == 138
    assert set(LEGACY_ARGV_MIGRATION.values()).issubset(final_by_id)

    legacy_by_id = {
        f"legacy:{index:03d}": fingerprint
        for index, fingerprint in enumerate(LEGACY_PAYLOAD_FINGERPRINTS, start=1)
    }
    for legacy_id, final_id in LEGACY_ARGV_MIGRATION.items():
        actual = hashlib.sha256(repr(payload(final_by_id[final_id])).encode()).hexdigest()
        assert legacy_by_id[legacy_id] == actual
