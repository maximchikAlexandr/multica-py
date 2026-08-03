from __future__ import annotations

from typing import overload

from multica_py.models.system import (
    RuntimeActivity,
    RuntimeDefinition,
    RuntimeUpdate,
    RuntimeUpdateResult,
    RuntimeUsage,
)
from multica_py.resources._base import BaseResource, _resolve_request


class RuntimeResource(BaseResource):
    def list(self) -> tuple[RuntimeDefinition, ...]:
        return self._run_json_decode_list(("runtime", "list"), RuntimeDefinition)

    def usage(self, runtime_id: str, *, days: int = 90) -> tuple[RuntimeUsage, ...]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        if not 1 <= days <= 365:
            raise ValueError("days must be between 1 and 365")
        return self._run_json_decode_list(
            ("runtime", "usage", runtime_id, "--days", str(days)), RuntimeUsage
        )

    def activity(self, runtime_id: str) -> tuple[RuntimeActivity, ...]:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        return self._run_json_decode_list(("runtime", "activity", runtime_id), RuntimeActivity)

    @overload
    def update(self, runtime_id: str, request: RuntimeUpdate, /) -> RuntimeUpdateResult: ...
    @overload
    def update(
        self, runtime_id: str, *, target_version: str, wait: bool = False
    ) -> RuntimeUpdateResult: ...

    def update(  # type: ignore[misc]
        self, runtime_id: str, request: RuntimeUpdate | None = None, /, **kwargs: object
    ) -> RuntimeUpdateResult:
        req = _resolve_request(request, kwargs, RuntimeUpdate)
        if not runtime_id.strip() or not req.target_version.strip():
            raise ValueError("runtime_id and target_version must be nonblank")
        args = ["runtime", "update", runtime_id, "--target-version", req.target_version]
        if req.wait:
            args.append("--wait")
        return self._run_json_decode(tuple(args), RuntimeUpdateResult)

    def rename(self, runtime_id: str, name: str, *, machine: bool = False) -> RuntimeDefinition:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        args = ["runtime", "rename", runtime_id, name]
        if machine:
            args.append("--machine")
        return self._run_json_decode(tuple(args), RuntimeDefinition)

    def delete(self, runtime_id: str, *, cascade: bool = False) -> None:
        if not runtime_id.strip():
            raise ValueError("runtime_id must be nonblank")
        args = ["runtime", "delete", runtime_id]
        if cascade:
            args.append("--cascade")
        self._transport.run_text(tuple(args))
