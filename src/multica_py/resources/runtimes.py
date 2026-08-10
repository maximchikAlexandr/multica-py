from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.common import ActionResult, Page
from multica_py.models.system import (
    RuntimeActivity,
    RuntimeDefinition,
    RuntimeUpdateResult,
    RuntimeUsage,
)
from multica_py.resources._base import BaseResource


class RuntimeResource(BaseResource):
    def list_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[Page[RuntimeDefinition]]:
        return self._decoded_page_command(("runtime", "list"), RuntimeDefinition, options=options)

    def list(self, *, options: OperationOptions | None = None) -> Page[RuntimeDefinition]:
        return self.list_command(options=options).run()

    def usage_command(
        self,
        runtime_id: str,
        *,
        days: int = 90,
        options: OperationOptions | None = None,
    ) -> Command[Page[RuntimeUsage]]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        if not 1 <= days <= 365:
            raise ValueError("days must be between 1 and 365")
        return self._decoded_page_command(
            ("runtime", "usage", runtime_id, "--days", str(days)), RuntimeUsage, options=options
        )

    def usage(
        self, runtime_id: str, *, days: int = 90, options: OperationOptions | None = None
    ) -> Page[RuntimeUsage]:
        return self.usage_command(runtime_id, days=days, options=options).run()

    def activity_command(
        self, runtime_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[RuntimeActivity]]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        return self._decoded_page_command(
            ("runtime", "activity", runtime_id), RuntimeActivity, options=options
        )

    def activity(
        self, runtime_id: str, *, options: OperationOptions | None = None
    ) -> Page[RuntimeActivity]:
        return self.activity_command(runtime_id, options=options).run()

    def update_command(
        self,
        runtime_id: str,
        *,
        target_version: str,
        wait: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[RuntimeUpdateResult]]:
        if not runtime_id.strip() or not target_version.strip():
            raise ValueError("runtime_id and target_version must be nonblank")
        args = ["runtime", "update", runtime_id, "--target-version", target_version]
        if wait:
            args.append("--wait")
        return self._action_decoded_command(tuple(args), RuntimeUpdateResult, options=options)

    def update(
        self,
        runtime_id: str,
        *,
        target_version: str,
        wait: bool = False,
        options: OperationOptions | None = None,
    ) -> ActionResult[RuntimeUpdateResult]:
        return self.update_command(
            runtime_id, target_version=target_version, wait=wait, options=options
        ).run()

    def rename_command(
        self,
        runtime_id: str,
        name: str,
        *,
        machine: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[RuntimeDefinition]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        args = ["runtime", "rename", runtime_id, name]
        if machine:
            args.append("--machine")
        return self._decoded_command(tuple(args), RuntimeDefinition, options=options)

    def rename(
        self,
        runtime_id: str,
        name: str,
        *,
        machine: bool = False,
        options: OperationOptions | None = None,
    ) -> RuntimeDefinition:
        return self.rename_command(runtime_id, name, machine=machine, options=options).run()

    def delete_command(
        self, runtime_id: str, *, cascade: bool = False, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
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
        return self._action_command(tuple(args), options=options)

    def delete(
        self, runtime_id: str, *, cascade: bool = False, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        """Delete a runtime; cascade preserves dependent agents and their history."""
        return self.delete_command(runtime_id, cascade=cascade, options=options).run()
