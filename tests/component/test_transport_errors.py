"""Public command-path coverage for typed fake-CLI transport failures."""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable

import pytest

from multica_py.client import MulticaClient
from multica_py.exceptions import ConflictError, ValidationError
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
)


@pytest.mark.parametrize("case", _COMMAND_CASES, ids=lambda case: case.id)
def test_public_issue_command_preserves_typed_fake_cli_detail(
    client_factory: Callable[..., MulticaClient],
    tmp_path: pathlib.Path,
    case: CommandCase,
) -> None:
    """The public eager command path maps real fake-CLI failures and detail."""
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    response = FakeMultica(responses_dir=responses_dir).build_response(
        stderr=case.stderr,
        exit_code=1,
        argv=("fake_multica", "issue", "list", "--output", "json"),
    )
    (responses_dir / "issue.json").write_text(
        json.dumps(response.to_dict()),
        encoding="utf-8",
    )
    client = client_factory(environment=(("MULTICA_FAKE_RESPONSES", str(responses_dir)),))

    with pytest.raises(case.expected_error) as excinfo:
        client.issues.list()

    exc = excinfo.value
    assert exc.exit_code == case.expected_exit_code
    assert case.stderr in str(exc)
    assert case.stderr in exc.stderr
