from __future__ import annotations

from multica_py.models.system import RuntimeDefinition
from multica_py.resources._base import BaseResource


class RuntimeResource(BaseResource):
    def list(self) -> tuple[RuntimeDefinition, ...]:
        return self._run_json_decode_list(("runtime", "list"), RuntimeDefinition)

    def get(self, runtime_id: str) -> RuntimeDefinition:
        return self._run_json_decode(("runtime", "get", runtime_id), RuntimeDefinition)
