from __future__ import annotations

import datetime
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport


@pytest.fixture
def mock_transport() -> MagicMock:
    return MagicMock(spec=CliTransport)


@pytest.fixture
def raw_result() -> Callable[[bytes, int], RawCommandResult]:
    def _raw_result(stdout: bytes = b"", exit_code: int = 0) -> RawCommandResult:
        return RawCommandResult(
            argv=(),
            exit_code=exit_code,
            stdout=stdout,
            stderr=b"",
            duration=datetime.timedelta(),
        )

    return _raw_result
