from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py.config import ClientConfig
from multica_py.exceptions import ConflictError, OutputShapeError
from multica_py.models.system import RuntimeDefinition
from multica_py.resources.runtimes import RuntimeResource


@dataclass(frozen=True)
class InvalidRuntimeCase:
    id: str
    invoke: Callable[[RuntimeResource], object]
    message: str


@dataclass(frozen=True)
class RuntimeDefinitionCase:
    id: str
    payload: bytes
    invoke: Callable[[RuntimeResource], RuntimeDefinition]


@dataclass(frozen=True)
class InvalidRuntimeDefinitionCase:
    id: str
    payload: bytes
    invoke: Callable[[RuntimeResource], object]


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


def test_runtime_delete_rejects_cascade_before_transport(mock_transport: MagicMock) -> None:
    resource = RuntimeResource(mock_transport, ClientConfig())
    with pytest.raises(ValueError, match="does not support cascade"):
        resource.delete_command("r1", cascade=True)
    mock_transport.run_text.assert_not_called()


def test_runtime_delete_empty_success_is_single_non_cascading_action(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = RuntimeResource(mock_transport, ClientConfig())
    command = resource.delete_command("r1")
    assert command.commands == ("multica runtime delete r1",)
    mock_transport.run_text.assert_not_called()


def test_runtime_usage_preserves_future_provider_and_model_strings(
    mock_transport: MagicMock, raw_result: Callable[..., RawCommandResult]
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    mock_transport.run_bytes.return_value = raw_result(
        argv=("multica", "runtime", "usage", "r1", "--days", "90", "--output", "json"),
        stdout=(
            b'[{"date":"2026-08-01","provider":"future-provider","model":"future-model",'
            b'"input_tokens":1,"output_tokens":2,"cache_read_tokens":3,"cache_write_tokens":4}]'
        ),
    )
    resource = RuntimeResource(mock_transport, ClientConfig())

    usage = resource.usage("r1")

    assert usage[0].provider == "future-provider"
    assert usage[0].model == "future-model"


@pytest.mark.parametrize(
    "case",
    (
        RuntimeDefinitionCase(
            "list",
            b'[{"id":"r1","name":"Codex","visibility":"workspace",'
            b'"shared_with":["member-2","member-1"]}]',
            lambda resource: resource.list()[0],
        ),
        RuntimeDefinitionCase(
            "rename",
            b'{"id":"r1","name":"Codex","visibility":"workspace","shared_with":["member-2","member-1"]}',
            lambda resource: resource.rename("r1", "Codex"),
        ),
    ),
    ids=lambda case: case.id,
)
def test_runtime_definition_decodes_visibility_and_ordered_sharing(
    case: RuntimeDefinitionCase,
    mock_transport: MagicMock,
    raw_result: Callable[..., RawCommandResult],
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    mock_transport.run_bytes.return_value = raw_result(
        argv=("multica", "runtime", case.id), stdout=case.payload
    )
    definition = case.invoke(RuntimeResource(mock_transport, ClientConfig()))

    assert definition.visibility == "workspace"
    assert definition.shared_with == ("member-2", "member-1")


def test_runtime_definition_legacy_sharing_fields_default_safely(
    mock_transport: MagicMock, raw_result: Callable[..., RawCommandResult]
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    mock_transport.run_bytes.return_value = raw_result(
        argv=("multica", "runtime", "list"), stdout=b'[{"id":"r1","name":"Codex"}]'
    )

    definition = RuntimeResource(mock_transport, ClientConfig()).list()[0]

    assert definition.visibility is None
    assert definition.shared_with == ()


@pytest.mark.parametrize(
    "case",
    (
        InvalidRuntimeDefinitionCase(
            "list-visibility",
            b'[{"id":"r1","name":"Codex","visibility":3}]',
            lambda resource: resource.list(),
        ),
        InvalidRuntimeDefinitionCase(
            "list-shared-with",
            b'[{"id":"r1","name":"Codex","shared_with":[3]}]',
            lambda resource: resource.list(),
        ),
        InvalidRuntimeDefinitionCase(
            "rename-visibility",
            b'{"id":"r1","name":"Codex","visibility":3}',
            lambda resource: resource.rename("r1", "Codex"),
        ),
        InvalidRuntimeDefinitionCase(
            "rename-shared-with",
            b'{"id":"r1","name":"Codex","shared_with":[3]}',
            lambda resource: resource.rename("r1", "Codex"),
        ),
    ),
    ids=lambda case: case.id,
)
def test_runtime_definition_rejects_malformed_sharing_fields(
    case: InvalidRuntimeDefinitionCase,
    mock_transport: MagicMock,
    raw_result: Callable[..., RawCommandResult],
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    mock_transport.run_bytes.return_value = raw_result(
        argv=("multica", "runtime", case.id.split("-", maxsplit=1)[0]),
        stdout=case.payload,
    )

    with pytest.raises(OutputShapeError):
        case.invoke(RuntimeResource(mock_transport, ClientConfig()))


def test_runtime_update_does_not_expose_definition_sharing_fields(
    mock_transport: MagicMock, raw_result: Callable[..., RawCommandResult]
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    mock_transport.run_bytes.return_value = raw_result(
        argv=("multica", "runtime", "update", "r1"),
        stdout=(
            b'{"id":"r1","status":"updated","visibility":"workspace","shared_with":["member-1"]}'
        ),
    )

    result = RuntimeResource(mock_transport, ClientConfig()).update("r1", target_version="stable")

    assert result.value is not None
    assert result.value.id == "r1"
    assert not hasattr(result.value, "visibility")
    assert not hasattr(result.value, "shared_with")
