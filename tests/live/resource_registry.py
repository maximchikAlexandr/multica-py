from __future__ import annotations

from collections.abc import Callable

from multica_py.exceptions import NotFoundError


class ResourceRegistry:
    """LIFO registry for live test resource cleanup."""

    def __init__(self) -> None:
        self._cleanups: list[tuple[str, Callable[[], None]]] = []

    def defer(self, *, key: str, cleanup: Callable[[], None]) -> None:
        """Register one cleanup callback invoked in reverse creation order.

        Args:
            key: Unique registry key.
            cleanup: Callback invoked during cleanup.
        """
        self._cleanups.append((key, cleanup))

    def cleanup_all(self) -> list[dict[str, str]]:
        """Delete registered resources in reverse registration order.

        Returns:
            Cleanup failure records for any resources that could not be removed.
        """
        failures: list[dict[str, str]] = []
        for key, cleanup in reversed(self._cleanups):
            try:
                cleanup()
            except (ResourceAbsentError, NotFoundError):
                continue
            except Exception as exc:
                failures.append({"key": key, "message": str(exc)})
        return failures


class ResourceAbsentError(Exception):
    """Raised when cleanup finds an already absent resource."""
