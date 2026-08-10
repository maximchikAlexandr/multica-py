from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py.config import ClientConfig
from multica_py.exceptions import ConflictError
from multica_py.resources.runtimes import RuntimeResource


@dataclass(frozen=True)
class InvalidRuntimeCase:
    id: str
    invoke: Callable[[RuntimeResource], object]
    message: str


INVALID_RUNTIME_CASES: tuple[InvalidRuntimeCase, ...] = (
    InvalidRuntimeCase("usage-id", lambda resource: resource.usage(" "), "runtime_id"),
    InvalidRuntimeCase("usage-days-low", lambda resource: resource.usage("r1", days=0), "days"),
    InvalidRuntimeCase("usage-days-high", lambda resource: resource.usage("r1", days=366), "days"),
    InvalidRuntimeCase("activity-id", lambda resource: resource.activity(""), "runtime_id"),
    InvalidRuntimeCase(
        "update-id",
        lambda resource: resource.update("", target_version="1.2.3"),
        "runtime_id and target_version",
    ),
    InvalidRuntimeCase(
        "update-version",
        lambda resource: resource.update("r1", target_version=" "),
        "runtime_id and target_version",
    ),
    InvalidRuntimeCase("rename-id", lambda resource: resource.rename(" ", "name"), "runtime_id"),
    InvalidRuntimeCase("delete-id", lambda resource: resource.delete(""), "runtime_id"),
)


@pytest.mark.parametrize("case", INVALID_RUNTIME_CASES, ids=lambda case: case.id)
def test_runtime_validation_fails_before_transport(
    case: InvalidRuntimeCase, mock_transport: MagicMock
) -> None:
    resource = RuntimeResource(mock_transport, ClientConfig())
    with pytest.raises(ValueError, match=case.message):
        case.invoke(resource)
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()


def test_runtime_delete_without_cascade_preserves_upstream_conflict_guidance() -> None:
    transport = MagicMock()
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    guidance = "Request conflict: active agents are attached; use --cascade to unbind them"
    transport.run_text.side_effect = ConflictError(guidance, exit_code=1, stderr=guidance)
    resource = RuntimeResource(transport, ClientConfig())

    command = resource.delete_command("r1")
    assert command.commands == ("multica runtime delete r1",)

    with pytest.raises(ConflictError, match="use --cascade to unbind them"):
        command.run()
    transport.run_text.assert_called_once_with(("runtime", "delete", "r1"))


def test_runtime_usage_preserves_future_provider_and_model_strings() -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = RawCommandResult(
        argv=("multica", "runtime", "usage", "r1", "--days", "90", "--output", "json"),
        exit_code=0,
        stdout=(
            b'[{"date":"2026-08-01","provider":"future-provider","model":"future-model",'
            b'"input_tokens":1,"output_tokens":2,"cache_read_tokens":3,"cache_write_tokens":4}]'
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    resource = RuntimeResource(transport, ClientConfig())

    usage = resource.usage("r1")

    assert usage[0].provider == "future-provider"
    assert usage[0].model == "future-model"
