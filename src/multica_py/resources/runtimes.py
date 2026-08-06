from __future__ import annotations

from typing import cast, overload

from multica_py._internal.commands import Command, _Step
from multica_py.models.system import (
    RuntimeActivity,
    RuntimeDefinition,
    RuntimeUpdate,
    RuntimeUpdateResult,
    RuntimeUsage,
)
from multica_py.resources._base import BaseResource, _resolve_request


class RuntimeResource(BaseResource):
    def list_command(self) -> Command[tuple[RuntimeDefinition, ...]]:
        args, decode = self._plan_decode_list(("runtime", "list"), RuntimeDefinition)
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("tuple[RuntimeDefinition, ...]", results[0]),
        )

    def list(self) -> tuple[RuntimeDefinition, ...]:
        return self.list_command().run()

    def usage_command(
        self, runtime_id: str, *, days: int = 90
    ) -> Command[tuple[RuntimeUsage, ...]]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        if not 1 <= days <= 365:
            raise ValueError("days must be between 1 and 365")
        args, decode = self._plan_decode_list(
            ("runtime", "usage", runtime_id, "--days", str(days)), RuntimeUsage
        )
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("tuple[RuntimeUsage, ...]", results[0]),
        )

    def usage(self, runtime_id: str, *, days: int = 90) -> tuple[RuntimeUsage, ...]:
        return self.usage_command(runtime_id, days=days).run()

    def activity_command(self, runtime_id: str) -> Command[tuple[RuntimeActivity, ...]]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        args, decode = self._plan_decode_list(("runtime", "activity", runtime_id), RuntimeActivity)
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("tuple[RuntimeActivity, ...]", results[0]),
        )

    def activity(self, runtime_id: str) -> tuple[RuntimeActivity, ...]:
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
        plan_args, decode = self._plan_decode(tuple(args), RuntimeUpdateResult)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("RuntimeUpdateResult", results[0]),
        )

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
        plan_args, decode = self._plan_decode(tuple(args), RuntimeDefinition)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("RuntimeDefinition", results[0]),
        )

    def rename(self, runtime_id: str, name: str, *, machine: bool = False) -> RuntimeDefinition:
        return self.rename_command(runtime_id, name, machine=machine).run()

    def delete_command(self, runtime_id: str, *, cascade: bool = False) -> Command[None]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        args = ["runtime", "delete", runtime_id]
        if cascade:
            args.append("--cascade")
        return self._plan(
            steps=(_Step(tuple(args), "run_text"),),
            finalize=lambda results: None,
        )

    def delete(self, runtime_id: str, *, cascade: bool = False) -> None:
        self.delete_command(runtime_id, cascade=cascade).run()
