from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from multica_py.config import ClientConfig
from multica_py.models.system import RuntimeUpdate
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
        lambda resource: resource.update("", RuntimeUpdate(target_version="1.2.3")),
        "runtime_id and target_version",
    ),
    InvalidRuntimeCase(
        "update-version",
        lambda resource: resource.update("r1", RuntimeUpdate(target_version=" ")),
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


def test_runtime_update_command_preserves_dual_input_and_is_lazy(
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = RuntimeResource(mock_transport, ClientConfig())

    direct = resource.update_command("r1", RuntimeUpdate(target_version="1.2.3", wait=True))
    keyword = resource.update_command("r1", target_version="1.2.3", wait=True)

    expected = "multica runtime update r1 --target-version 1.2.3 --wait --output json"
    assert direct.commands == (expected,)
    assert keyword.commands == (expected,)
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
