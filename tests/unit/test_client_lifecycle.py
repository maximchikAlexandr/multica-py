from __future__ import annotations

from dataclasses import dataclass

import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig


@dataclass
class _CloseTracker:
    count: int = 0

    def close(self) -> None:
        self.count += 1


@pytest.mark.parametrize("body_raises", [False, True], ids=["normal-exit", "exception-exit"])
def test_client_context_manager_lifecycle(body_raises: bool) -> None:
    """Verify one transport close per context and body exception propagation."""
    tracker = _CloseTracker()
    client = MulticaClient(ClientConfig())
    object.__setattr__(client, "_transport", tracker)
    if body_raises:
        with pytest.raises(RuntimeError, match="body failed"), client:
            raise RuntimeError("body failed")
    else:
        with client:
            pass
    assert tracker.count == 1
