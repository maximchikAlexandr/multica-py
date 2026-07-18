from __future__ import annotations

import datetime
import sys

import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import (
    AuthenticationError,
    CommandExecutionError,
    NetworkError,
    NotFoundError,
    ValidationError,
)


def _failed_result(exit_code: int) -> RawCommandResult:
    return RawCommandResult(
        argv=("multica", "project", "get", "missing"),
        exit_code=exit_code,
        stdout=b"",
        stderr=b"error",
        duration=datetime.timedelta(),
    )


@pytest.mark.parametrize(
    ("exit_code", "expected_exc"),
    [
        (2, NetworkError),
        (3, AuthenticationError),
        (4, NotFoundError),
        (5, ValidationError),
        (99, CommandExecutionError),
    ],
)
def test_transport_maps_exit_code_to_exception(exit_code: int, expected_exc: type[Exception]):
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    transport._execute = lambda *args, **kwargs: _failed_result(exit_code)  # type: ignore[method-assign]
    with pytest.raises(expected_exc) as excinfo:
        transport.run_text(("project", "get", "missing"))
    exc = excinfo.value
    assert exc.exit_code == exit_code
    assert isinstance(exc, CommandExecutionError)


def test_transport_exit_code_mapping_preserves_context():
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    transport._execute = lambda *args, **kwargs: RawCommandResult(  # type: ignore[method-assign]
        argv=("multica", "auth", "status"),
        exit_code=3,
        stdout=b"unauthorized",
        stderr=b"forbidden",
        duration=datetime.timedelta(),
    )
    with pytest.raises(AuthenticationError) as excinfo:
        transport.run_text(("auth", "status"))
    exc = excinfo.value
    assert exc.stdout == "unauthorized"
    assert exc.stderr == "forbidden"
    assert exc.argv == ("multica", "auth", "status")
