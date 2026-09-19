"""Public command-path coverage for typed fake-CLI transport failures."""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable
from typing import cast

import pytest

from multica_py.client import MulticaClient
from multica_py.entities.comments import Comment
from multica_py.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from multica_py.models.agents import AgentConversationStarter
from multica_py.models.common import ActionResult
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
        id="comment-delete-pre-support-404",
        stderr="Error: DELETE /api/comments/c1/keep-replies returned 404: missing",
        expected_error=NotFoundError,
        expected_exit_code=4,
        expected_argv=("issue", "comment", "delete", "c1"),
        resource_attr="issues.comments",
        method="delete",
        args=("c1",),
    ),
    CommandCase(
        id="comment-update-eager-success",
        stderr="",
        expected_error=None,
        expected_exit_code=0,
        response_exit_code=0,
        expected_argv=(
            "issue",
            "comment",
            "update",
            "cmt_1",
            "--content",
            "revised",
            "--expected-revision",
            "3",
            "--output",
            "json",
        ),
        resource_attr="issues.comments",
        method="update",
        args=("cmt_1", "revised"),
        kwargs=(("expected_revision", 3),),
        stdout='{"id":"cmt_1","content":"revised","revision":3}',
        expected_comment=("cmt_1", "revised", 3),
    ),
    CommandCase(
        id="runtime-delete-structured-409-full",
        stderr=(
            "Error: DELETE /api/runtimes/r1 returned 409: "
            '{"code":"runtime_profile_instance_delete_unsupported",'
            '"error":"runtime diagnostic","active_agent_count":2}'
        ),
        expected_error=ConflictError,
        expected_exit_code=1,
        expected_message="runtime diagnostic",
        expected_argv=("runtime", "delete", "r1"),
        resource_attr="runtimes",
        method="delete",
        args=("r1",),
    ),
    CommandCase(
        id="runtime-delete-structured-409-optional-missing",
        stderr=(
            "Error: DELETE /api/runtimes/r1 returned 409: "
            '{"code":"runtime_profile_instance_delete_unsupported",'
            '"error":"stop daemon first"}'
        ),
        expected_error=ConflictError,
        expected_exit_code=1,
        expected_message="stop daemon first",
        expected_argv=("runtime", "delete", "r1"),
        resource_attr="runtimes",
        method="delete",
        args=("r1",),
    ),
    CommandCase(
        id="runtime-delete-structured-409-malformed",
        stderr="Error: DELETE /api/runtimes/r1 returned 409: not-json",
        expected_error=ConflictError,
        expected_exit_code=1,
        expected_argv=("runtime", "delete", "r1"),
        resource_attr="runtimes",
        method="delete",
        args=("r1",),
    ),
    CommandCase(
        id="runtime-delete-structured-404",
        stderr=(
            "Error: DELETE /api/runtimes/r1 returned 404: "
            '{"code":"runtime_not_found","error":"missing runtime"}'
        ),
        expected_error=NotFoundError,
        expected_exit_code=4,
        expected_message="missing runtime",
        expected_argv=("runtime", "delete", "r1"),
        resource_attr="runtimes",
        method="delete",
        args=("r1",),
    ),
    CommandCase(
        id="runtime-delete-structured-403",
        stderr=(
            "Error: DELETE /api/runtimes/r1 returned 403: "
            '{"code":"runtime_access_denied","error":"forbidden"}'
        ),
        expected_error=AuthorizationError,
        expected_exit_code=3,
        expected_message="forbidden",
        expected_argv=("runtime", "delete", "r1"),
        resource_attr="runtimes",
        method="delete",
        args=("r1",),
    ),
    CommandCase(
        id="runtime-delete-plain-conflict",
        stderr="Request conflict: runtime has active agents",
        expected_error=ConflictError,
        expected_exit_code=1,
        expected_argv=("runtime", "delete", "r1"),
        resource_attr="runtimes",
        method="delete",
        args=("r1",),
    ),
    CommandCase(
        id="runtime-delete-empty-success-no-cascade",
        stderr="",
        expected_error=None,
        expected_exit_code=0,
        response_exit_code=0,
        expected_argv=("runtime", "delete", "r1"),
        resource_attr="runtimes",
        method="delete",
        args=("r1",),
        expected_action_success=True,
    ),
    CommandCase(
        id="agent-create-model-thinking-argv",
        stderr="",
        expected_error=None,
        expected_exit_code=0,
        response_exit_code=0,
        expected_argv=(
            "agent",
            "create",
            "--name",
            "agent",
            "--model",
            "gpt-5",
            "--thinking-level",
            "high",
            "--output",
            "json",
        ),
        resource_attr="agents",
        method="create",
        kwargs=(("name", "agent"), ("model", "gpt-5"), ("thinking_level", "high")),
        stdout='{"id":"a1","name":"agent","model":"gpt-5","thinking_level":"high"}',
    ),
    CommandCase(
        id="agent-update-runtime-swap-argv",
        stderr="",
        expected_error=None,
        expected_exit_code=0,
        response_exit_code=0,
        expected_argv=(
            "agent",
            "update",
            "a1",
            "--runtime-id",
            "runtime-2",
            "--output",
            "json",
        ),
        resource_attr="agents",
        method="update",
        args=("a1",),
        kwargs=(("runtime_id", "runtime-2"),),
        stdout='{"id":"a1","name":"agent","runtime_id":"runtime-2"}',
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
            "--model",
            "gpt-5",
            "--conversation-starters",
            '[{"label":"Review","prompt":"Review this"},{"label":"Plan","prompt":"Plan this"}]',
            "--output",
            "json",
        ),
        resource_attr="agents",
        method="create",
        kwargs=(
            ("name", "agent"),
            ("model", "gpt-5"),
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
    CommandCase(
        id="issue-run-messages-truncation",
        stderr="",
        expected_error=None,
        expected_exit_code=0,
        response_exit_code=0,
        expected_argv=(
            "issue",
            "run-messages",
            "run1",
            "--issue",
            "i1",
            "--since",
            "0",
            "--output",
            "json",
        ),
        method="run_messages",
        args=("run1",),
        kwargs=(("issue_id", "i1"),),
        stdout=(
            '[{"task_id":"run1","seq":1,"type":"tool_result",'
            '"output":"partial","output_truncated":true}]'
        ),
        expected_output_truncated=True,
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

    resource: object = client
    for resource_part in case.resource_attr.split("."):
        resource = getattr(resource, resource_part)
    operation = getattr(resource, case.method)
    if case.expected_error is not None:
        with pytest.raises(case.expected_error) as excinfo:
            operation(*case.args, **dict(case.kwargs))

        exc = excinfo.value
        assert exc.exit_code == case.expected_exit_code
        assert (case.expected_message or case.stderr) in str(exc)
        assert case.stderr in exc.stderr
    else:
        result = operation(*case.args, **dict(case.kwargs))
        if case.expected_action_success:
            assert isinstance(result, ActionResult)
            assert result.success
            assert result.value is None
        if case.expected_starters is not None:
            assert tuple(getattr(result, "conversation_starters")) == case.expected_starters
        if case.expected_output_truncated is not None:
            assert result.items[0].output_truncated is case.expected_output_truncated
        if case.expected_comment is not None:
            assert isinstance(result, Comment)
            assert (result.id, result.body, result.revision) == case.expected_comment
        records = [
            json.loads(line) for line in record_path.read_text(encoding="utf-8").splitlines()
        ]
        assert len(records) == 1
        recorded_argv = cast("list[str]", records[-1]["argv"])
        assert tuple(recorded_argv[1:]) == case.expected_argv
