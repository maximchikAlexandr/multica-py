from __future__ import annotations

from dataclasses import dataclass

from multica_py.exceptions import CommandExecutionError


@dataclass(frozen=True)
class CommandCase:
    id: str
    stderr: str
    expected_error: type[CommandExecutionError] | None
    expected_exit_code: int
    stdout: str = ""
    response_exit_code: int = 1
    expected_argv: tuple[str, ...] = ("issue", "list", "--output", "json")
    resource_attr: str = "issues"
    method: str = "list"
    args: tuple[object, ...] = ()
    kwargs: tuple[tuple[str, object], ...] = ()
    expected_starters: tuple[object, ...] | None = None
    expected_output_truncated: bool | None = None
    expected_message: str | None = None
    expected_action_success: bool = False
    expected_comment: tuple[str, str, int] | None = None
