from __future__ import annotations

import pytest

from multica_py.client import MulticaClient
from multica_py.models.agents import AgentCreateRequest, AgentUpdateRequest
from tests.component.conftest import assert_command_argv
from tests.component.resource_payloads import P_ID_AG_001_NAME_HELPER_SKILLS_2
from tests.component.resource_support import CommandCase

PRESENCE_COMMAND_CASES: tuple[CommandCase, ...] = (
    CommandCase(
        id="agents.create.omit-description",
        sdk_method="agents.create",
        invoke=lambda c: c.agents.create(AgentCreateRequest(name="my-agent")),
        expected_argv=("agent", "create", "--name", "my-agent", "--output", "json"),
        stdout=P_ID_AG_001_NAME_HELPER_SKILLS_2,
    ),
    CommandCase(
        id="agents.create.set-description",
        sdk_method="agents.create",
        invoke=lambda c: c.agents.create(AgentCreateRequest(name="my-agent", description="desc")),
        expected_argv=(
            "agent",
            "create",
            "--name",
            "my-agent",
            "--description",
            "desc",
            "--output",
            "json",
        ),
        stdout=P_ID_AG_001_NAME_HELPER_SKILLS_2,
    ),
    CommandCase(
        id="agents.update.omit-name",
        sdk_method="agents.update",
        invoke=lambda c: c.agents.update("ag_001", AgentUpdateRequest()),
        expected_argv=("agent", "update", "ag_001", "--output", "json"),
        stdout=P_ID_AG_001_NAME_HELPER_SKILLS_2,
    ),
    CommandCase(
        id="agents.update.set-name",
        sdk_method="agents.update",
        invoke=lambda c: c.agents.update("ag_001", AgentUpdateRequest(name="new")),
        expected_argv=("agent", "update", "ag_001", "--name", "new", "--output", "json"),
        stdout=P_ID_AG_001_NAME_HELPER_SKILLS_2,
    ),
)


@pytest.mark.parametrize("case", PRESENCE_COMMAND_CASES, ids=lambda item: item.id)
def test_presence_semantics(case: CommandCase, fake_cli_client: MulticaClient) -> None:
    assert_command_argv(case, fake_cli_client)
