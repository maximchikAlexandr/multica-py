from __future__ import annotations

from dataclasses import dataclass

from multica_py.exceptions import CommandExecutionError


@dataclass(frozen=True)
class CommandCase:
    id: str
    stderr: str
    expected_error: type[CommandExecutionError]
    expected_exit_code: int
