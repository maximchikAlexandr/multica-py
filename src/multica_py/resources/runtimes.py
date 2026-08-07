from __future__ import annotations

from typing import cast, overload

from multica_py._internal.commands import Command
from multica_py.models.common import Page
from multica_py.models.system import (
    RuntimeActivity,
    RuntimeDefinition,
    RuntimeUpdate,
    RuntimeUpdateResult,
    RuntimeUsage,
)
from multica_py.resources._base import BaseResource, _resolve_request


class RuntimeResource(BaseResource):
    def list_command(self) -> Command[Page[RuntimeDefinition]]:
        return self._decoded_page_command(("runtime", "list"), RuntimeDefinition)

    def list(self) -> Page[RuntimeDefinition]:
        return self.list_command().run()

    def usage_command(self, runtime_id: str, *, days: int = 90) -> Command[Page[RuntimeUsage]]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        if not 1 <= days <= 365:
            raise ValueError("days must be between 1 and 365")
        return self._decoded_page_command(
            ("runtime", "usage", runtime_id, "--days", str(days)), RuntimeUsage
        )

    def usage(self, runtime_id: str, *, days: int = 90) -> Page[RuntimeUsage]:
        return self.usage_command(runtime_id, days=days).run()

    def activity_command(self, runtime_id: str) -> Command[Page[RuntimeActivity]]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        return self._decoded_page_command(("runtime", "activity", runtime_id), RuntimeActivity)

    def activity(self, runtime_id: str) -> Page[RuntimeActivity]:
        return self.activity_command(runtime_id).run()

    @overload
    def update_command(
        self, runtime_id: str, request: RuntimeUpdate, /
    ) -> Command[RuntimeUpdateResult]: ...
    @overload
    def update_command(
        self, runtime_id: str, *, target_version: str, wait: bool = False
    ) -> Command[RuntimeUpdateResult]: ...

    def update_command(  # type: ignore[misc]
        self, runtime_id: str, request: RuntimeUpdate | None = None, /, **kwargs: object
    ) -> Command[RuntimeUpdateResult]:
        req = _resolve_request(request, kwargs, RuntimeUpdate)
        if not runtime_id.strip() or not req.target_version.strip():
            raise ValueError("runtime_id and target_version must be nonblank")
        args = ["runtime", "update", runtime_id, "--target-version", req.target_version]
        if req.wait:
            args.append("--wait")
        return self._decoded_command(tuple(args), RuntimeUpdateResult)

    @overload
    def update(self, runtime_id: str, request: RuntimeUpdate, /) -> RuntimeUpdateResult: ...
    @overload
    def update(
        self, runtime_id: str, *, target_version: str, wait: bool = False
    ) -> RuntimeUpdateResult: ...

    def update(  # type: ignore[misc]
        self, runtime_id: str, request: RuntimeUpdate | None = None, /, **kwargs: object
    ) -> RuntimeUpdateResult:
        return self.update_command(runtime_id, cast("RuntimeUpdate", request), **kwargs).run()

    def rename_command(
        self, runtime_id: str, name: str, *, machine: bool = False
    ) -> Command[RuntimeDefinition]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        args = ["runtime", "rename", runtime_id, name]
        if machine:
            args.append("--machine")
        return self._decoded_command(tuple(args), RuntimeDefinition)

    def rename(self, runtime_id: str, name: str, *, machine: bool = False) -> RuntimeDefinition:
        return self.rename_command(runtime_id, name, machine=machine).run()

    def delete_command(self, runtime_id: str, *, cascade: bool = False) -> Command[None]:
        """Build a runtime-delete plan, optionally cascading to dependents.

        ``cascade=True`` asks the upstream CLI to unbind dependent agents,
        cancel their queued/running work, and delete the runtime while
        preserving each agent's configuration, chats, and task history.
        """
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        args = ["runtime", "delete", runtime_id]
        if cascade:
            args.append("--cascade")
        return self._none_command(tuple(args))

    def delete(self, runtime_id: str, *, cascade: bool = False) -> None:
        """Delete a runtime; cascade preserves dependent agents and their history."""
        self.delete_command(runtime_id, cascade=cascade).run()
