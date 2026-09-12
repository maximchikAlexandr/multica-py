"""Public command-path coverage for typed fake-CLI transport failures."""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable
from typing import cast

import pytest

from multica_py.client import MulticaClient
from multica_py.exceptions import ConflictError, ValidationError
from multica_py.models.agents import AgentConversationStarter
from tests.component.resources.cases import CommandCase
from tests.fixtures.fake_multica import FakeMultica

pytestmark = [pytest.mark.component, pytest.mark.process]


_COMMAND_CASES: tuple[CommandCase, ...] = (
    CommandCase(
        id="conflict-detail",
        stderr="Request conflict: a skill with this name already exists",
        expected_error=ConflictError,
        expected_exit_code=1,
    ),
    CommandCase(
        id="validation-detail",
        stderr="Invalid request: thinking level is unsupported",
        expected_error=ValidationError,
        expected_exit_code=5,
    ),
    CommandCase(
        id="agent-create-conversation-starters",
        stderr="",
        expected_error=None,
        expected_exit_code=0,
        response_exit_code=0,
        expected_argv=(
            "agent",
            "create",
            "--name",
            "agent",
            "--conversation-starters",
            '[{"label":"Review","prompt":"Review this"},{"label":"Plan","prompt":"Plan this"}]',
            "--output",
            "json",
        ),
        resource_attr="agents",
        method="create",
        kwargs=(
            ("name", "agent"),
            (
                "conversation_starters",
                (
                    AgentConversationStarter(label="Review", prompt="Review this"),
                    AgentConversationStarter(label="Plan", prompt="Plan this"),
                ),
            ),
        ),
        stdout=json.dumps(
            {
                "id": "a1",
                "name": "Agent",
                "conversation_starters": [
                    {"label": "Review", "prompt": "Review this"},
                    {"label": "Plan", "prompt": "Plan this"},
                ],
            }
        ),
        expected_starters=(
            AgentConversationStarter(label="Review", prompt="Review this"),
            AgentConversationStarter(label="Plan", prompt="Plan this"),
        ),
    ),
    CommandCase(
        id="agent-update-conversation-starters-clear",
        stderr="",
        expected_error=None,
        expected_exit_code=0,
        response_exit_code=0,
        expected_argv=(
            "agent",
            "update",
            "a1",
            "--conversation-starters",
            "[]",
            "--output",
            "json",
        ),
        resource_attr="agents",
        method="update",
        args=("a1",),
        kwargs=(("conversation_starters", ()),),
        stdout=json.dumps(
            {
                "id": "a1",
                "name": "Agent",
                "conversation_starters": [],
            }
        ),
        expected_starters=(),
    ),
)


@pytest.mark.parametrize("case", _COMMAND_CASES, ids=lambda case: case.id)
def test_public_commands_preserve_typed_fake_cli_detail(
    client_factory: Callable[..., MulticaClient],
    tmp_path: pathlib.Path,
    case: CommandCase,
) -> None:
    """Public eager command paths map fake-CLI responses and typed detail."""
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    response = FakeMultica(responses_dir=responses_dir).build_response(
        stdout=case.stdout,
        stderr=case.stderr,
        exit_code=case.response_exit_code,
        argv=("fake_multica", *case.expected_argv),
    )
    (responses_dir / f"{case.expected_argv[0]}.json").write_text(
        json.dumps(response.to_dict()),
        encoding="utf-8",
    )
    record_path = tmp_path / "record.jsonl"
    client = client_factory(
        environment=(
            ("MULTICA_FAKE_RESPONSES", str(responses_dir)),
            ("MULTICA_FAKE_RECORD", str(record_path)),
            ("MULTICA_FAKE_RECORD_ROOT", str(tmp_path)),
        )
    )

    operation = getattr(getattr(client, case.resource_attr), case.method)
    if case.expected_error is not None:
        with pytest.raises(case.expected_error) as excinfo:
            operation(*case.args, **dict(case.kwargs))

        exc = excinfo.value
        assert exc.exit_code == case.expected_exit_code
        assert case.stderr in str(exc)
        assert case.stderr in exc.stderr
    else:
        result = operation(*case.args, **dict(case.kwargs))
        assert tuple(getattr(result, "conversation_starters")) == case.expected_starters
        records = [
            json.loads(line) for line in record_path.read_text(encoding="utf-8").splitlines()
        ]
        recorded_argv = cast("list[str]", records[-1]["argv"])
        assert tuple(recorded_argv[1:]) == case.expected_argv
