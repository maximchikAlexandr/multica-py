"""LIFO registry for live test resource cleanup.

``ResourceRegistry`` predates ``LiveSession.defer_cleanup`` and is kept
narrow for legacy tests that still need a non-session cleanup channel
(e.g., ``tests/live/test_issue_workflow.py`` which asserts the
``cleanup_all`` return shape). New code should use
``LiveSession.defer_cleanup`` directly.
"""

from __future__ import annotations

from collections.abc import Callable

from multica_py.exceptions import NotFoundError
from tools.live_support.oracle import ResourceAbsentError

__all__ = ["ResourceRegistry"]


class ResourceRegistry:
    """LIFO registry for live test resource cleanup."""

    def __init__(self) -> None:
        self._cleanups: list[tuple[str, Callable[[], None]]] = []

    def defer(self, *, key: str, cleanup: Callable[[], None]) -> None:
        """Register one cleanup callback invoked in reverse creation order."""
        self._cleanups.append((key, cleanup))

    def cleanup_all(self) -> list[dict[str, str]]:
        """Delete registered resources in reverse registration order."""
        failures: list[dict[str, str]] = []
        for key, cleanup in reversed(self._cleanups):
            try:
                cleanup()
            except (ResourceAbsentError, NotFoundError):
                continue
            except Exception as exc:  # surfaced to the caller
                failures.append({"key": key, "message": str(exc)})
        return failures
