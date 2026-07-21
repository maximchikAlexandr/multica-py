from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from multica_py.client import MulticaClient


@dataclass(frozen=True)
class ExpectedError:
    """Expected SDK exception for one error-mapping case."""

    exc_type: type[BaseException]
    exit_code: int | None = None


@dataclass(frozen=True)
class CommandCase:
    """One fake-CLI component contract case."""

    id: str
    invoke: Callable[[MulticaClient], object]
    expected_argv: tuple[str, ...]
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    expected: Any = None
    expected_error: ExpectedError | None = None
    marks: tuple[Any, ...] = ()
    sdk_method: str = ""
    check: str = "not_none"

    def __post_init__(self) -> None:
        if self.expected is not None and self.expected_error is not None:
            raise ValueError(f"{self.id}: expected and expected_error are mutually exclusive")
