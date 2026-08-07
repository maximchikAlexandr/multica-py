from __future__ import annotations

import inspect
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from multica_py.config import ClientConfig
from multica_py.resources.agents import Agent, AgentResource


@dataclass(frozen=True)
class CopyValidationCase:
    id: str
    source_agent_id: str
    kwargs: tuple[tuple[str, object], ...]


_COPY_VALIDATION_CASES: tuple[CopyValidationCase, ...] = (
    CopyValidationCase("source", "", ()),
    CopyValidationCase("name", "a1", (("name", ""),)),
    CopyValidationCase("max-low", "a1", (("max_concurrent_tasks", 0),)),
    CopyValidationCase("max-high", "a1", (("max_concurrent_tasks", 51),)),
    CopyValidationCase("custom-args", "a1", (("custom_args", ("ok", 1)),)),
    CopyValidationCase("members-empty", "a1", (("public_to_member_ids", ()),)),
    CopyValidationCase("member", "a1", (("public_to_member_ids", ("",)),)),
)


@pytest.mark.parametrize(
    "case",
    _COPY_VALIDATION_CASES,
    ids=lambda case: case.id,
)
def test_copy_validation_is_zero_io(case: CopyValidationCase, mock_transport: MagicMock) -> None:
    resource = AgentResource(mock_transport, ClientConfig())

    with pytest.raises(ValueError):
        resource.copy_command(case.source_agent_id, **dict(case.kwargs))  # type: ignore[arg-type]

    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()


def test_copy_signatures_and_argv_exclude_secret_and_legacy_flags(
    mock_transport: MagicMock,
) -> None:
    resource = AgentResource(mock_transport, ClientConfig())
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    forbidden = {"custom_env", "mcp_config", "runtime_config", "visibility"}

    for method_name in ("copy", "copy_command"):
        parameters = inspect.signature(getattr(AgentResource, method_name)).parameters
        assert forbidden.isdisjoint(parameters)

    command = resource.copy_command("a1", description="", copy_skills=False)
    preview = command.commands[0]
    assert "--description ''" in preview
    assert "--no-skills" in preview
    assert all(flag not in preview for flag in forbidden)

    with pytest.raises(TypeError):
        resource.copy_command("a1", custom_env={})  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        resource.copy("a1", visibility="private")  # type: ignore[call-arg]
    mock_transport.run_bytes.assert_not_called()
    assert isinstance(Agent.from_dict({"id": "a1", "name": "agent"}), Agent)
