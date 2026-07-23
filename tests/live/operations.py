"""Direct live executor callables (T064, currently empty — per-sdk executors pending)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# ponytail: T064 will fill in real per-sdk executors; until then the executor
# test is hard-skipped (see tests/live/extended/test_live_operations.py).
DIRECT_EXECUTORS: dict[str, Callable[..., Any]] = {}
