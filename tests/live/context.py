from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from multica_py.client import MulticaClient
from tests.live.bootstrap import TestIdentity
from tests.live.oracle import DirectApiOracle


@dataclass(frozen=True, slots=True)
class LiveContext:
    """Context passed to every LiveOperation.invoke and CRUD round-trip.

    Attributes:
        client: Live SDK client bound to the primary workspace.
        oracle: Direct HTTP oracle for arrange/assert/cleanup.
        register_resource: Registers created resources for teardown.
        identity: Authenticated test identity with redacted secrets.
    """

    client: MulticaClient
    oracle: DirectApiOracle
    register_resource: Callable[..., None]
    identity: TestIdentity
