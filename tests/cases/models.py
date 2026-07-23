from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class BehaviorDimension(Enum):
    ARGV = "argv"
    DECODE = "decode"
    COMPONENT_ROUNDTRIP = "component-roundtrip"
    ERROR_MAPPING = "error-mapping"
    SECRET_REDACTION = "secret-redaction"
    MALFORMED_OUTPUT = "malformed-output"
    PRESENCE_OMITTED = "presence-omitted"
    PRESENCE_NULL = "presence-null"
    PRESENCE_EMPTY = "presence-empty"
    LIVE_SMOKE = "live-smoke"
    LIVE_EXTENDED = "live-extended"
    LIVE_SANDBOX = "live-sandbox"


@dataclass(frozen=True)
class ExpectedTransportCall:
    method: str
    args: list[str]
    stdin: str | None = None
    timeout: int | None = None


@dataclass(frozen=True)
class FakeCliResponse:
    """In-memory fake-CLI response: stdout/stderr bytes + exit code."""

    stdout: bytes = b""
    stderr: bytes = b""
    exit_code: int = 0


@dataclass(frozen=True)
class LivePolicy:
    """Closed modes: smoke | extended | sandbox | unrunnable. `reason` non-None only for unrunnable (spec §4)."""

    mode: str = "unrunnable"
    owner: str = "none"
    reason: str | None = None


@dataclass(frozen=True)
class OperationCase:
    sdk_method: str
    operation_id: str
    variant_id: str = "default"
    args: tuple[object, ...] = ()
    kwargs: tuple[tuple[str, object], ...] = ()
    expected_call: ExpectedTransportCall | None = None
    response: FakeCliResponse | None = None
    assert_result: Callable[[object], None] | None = None
    dimensions: frozenset[BehaviorDimension] = field(default_factory=frozenset)
    live: LivePolicy = field(default_factory=LivePolicy)
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ErrorCase:
    id: str
    operation: OperationCase
    response: FakeCliResponse
    exception_type: type[BaseException]
    assert_exception: Callable[[BaseException], None] | None = None
    dimensions: frozenset[BehaviorDimension] = field(default_factory=frozenset)
