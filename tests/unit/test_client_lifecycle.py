from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig


@dataclass
class _CloseTracker:
    count: int = 0

    def close(self) -> None:
        self.count += 1


@dataclass
class _LifecycleCase:
    body_raises: bool
    tracker: _CloseTracker = field(default_factory=_CloseTracker)


_LIFECYCLE_CASES: tuple[_LifecycleCase, ...] = (
    _LifecycleCase(body_raises=False),
    _LifecycleCase(body_raises=True),
)


@pytest.mark.parametrize("case", _LIFECYCLE_CASES, ids=["normal-exit", "exception-exit"])
def test_client_context_manager_lifecycle(case: _LifecycleCase) -> None:
    """Verify one transport close per context and body exception propagation."""
    client = MulticaClient(ClientConfig())
    object.__setattr__(client, "_transport", case.tracker)
    if case.body_raises:
        with pytest.raises(RuntimeError, match="body failed"), client:
            raise RuntimeError("body failed")
    else:
        with client:
            pass
    assert case.tracker.count == 1
